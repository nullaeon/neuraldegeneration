import os
import random
import torch
import argparse
import yaml
from glob import glob
from dataclasses import dataclass
from transformers import (
    GPT2Config,
    GPT2LMHeadModel,
    Trainer,
    TrainingArguments,
    PreTrainedTokenizerFast,
)
from datasets import load_dataset
import boto3
from urllib.parse import urlparse
from torch.distributed import is_initialized, get_rank, barrier

# --- Utils ---
def is_main_process():
    return not is_initialized() or get_rank() == 0

# --- Config Dataclass ---
@dataclass
class TrainConfig:
    tokenizer_path: str
    tokenizer_s3_uri: str
    english_glob: str
    generated_glob: str
    max_english_files: int
    max_generated_files: int
    output_dir: str
    model_name: str
    block_size: int
    batch_size: int
    gradient_accum_steps: int
    epochs: int
    learning_rate: float
    warmup_steps: int
    weight_decay: float
    save_limit: int
    dataset_s3_uris: list
    model_s3_upload_path: str

    @staticmethod
    def from_yaml(path: str):
        with open(path, 'r') as f:
            raw = yaml.safe_load(f)
        return TrainConfig(**raw)

# --- Trainer Class ---
class LLMTrainer:
    def __init__(self, cfg: TrainConfig):
        self.cfg = cfg
        self.tokenizer = None

    def _setup_tokenizer(self):
        self.tokenizer.pad_token = "<pad>"
        self.tokenizer.bos_token = "<s>"
        self.tokenizer.eos_token = "</s>"
        self.tokenizer.unk_token = "<unk>"
        self.tokenizer.padding_side = "right"
        self.tokenizer.truncation_side = "right"

    def prepare_data(self):
        if is_main_process():
            if self.cfg.tokenizer_s3_uri and str(self.cfg.tokenizer_s3_uri).lower() != "null":
                parsed = urlparse(self.cfg.tokenizer_s3_uri)
                bucket = parsed.netloc
                key = parsed.path.lstrip("/")
                if not os.path.exists(self.cfg.tokenizer_path):
                    print(f"[RANK 0] Downloading tokenizer from s3://{bucket}/{key}")
                    boto3.client("s3").download_file(bucket, key, self.cfg.tokenizer_path)
                else:
                    print(f"[RANK 0] Tokenizer already exists: {self.cfg.tokenizer_path}")

            if self.cfg.dataset_s3_uris and str(self.cfg.dataset_s3_uris).lower() != "null":
                for uri in self.cfg.dataset_s3_uris:
                    parsed = urlparse(uri)
                    bucket = parsed.netloc
                    prefix = parsed.path.lstrip("/")
                    s3 = boto3.client("s3")
                    paginator = s3.get_paginator("list_objects_v2")
                    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                        if "Contents" not in page:
                            continue
                        for obj in page["Contents"]:
                            key = obj["Key"]
                            if not key.endswith(".txt"):
                                continue
                            filename = os.path.basename(key)
                            local_path = os.path.join("data/s3_cache", filename)
                            if not os.path.exists(local_path):
                                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                                print(f"[RANK 0] Downloading {key} → {local_path}")
                                s3.download_file(bucket, key, local_path)
                            else:
                                print(f"[RANK 0] Skipping existing file {local_path}")

        if is_initialized():
            barrier()

        self.tokenizer = PreTrainedTokenizerFast(tokenizer_file=self.cfg.tokenizer_path)
        self._setup_tokenizer()

    def _tokenize_function(self, example):
        return self.tokenizer(
            example["text"],
            truncation=True,
            max_length=self.cfg.block_size,
            padding=False,
            return_attention_mask=True
        )

    def _group_texts(self, examples):
        result = {}
        for key in examples:
            concatenated = sum(examples[key], [])
            total_length = (len(concatenated) // self.cfg.block_size) * self.cfg.block_size
            result[key] = [
                concatenated[i:i + self.cfg.block_size] for i in range(0, total_length, self.cfg.block_size)
            ]
        result["labels"] = result["input_ids"].copy()
        return result

    def train(self):
        num_proc = min(16, os.cpu_count())
        random.seed(42)

        file_list = []

        if self.cfg.dataset_s3_uris and str(self.cfg.dataset_s3_uris).lower() != "null":
            for filename in os.listdir("data/s3_cache"):
                file_list.append(os.path.join("data/s3_cache", filename))

        if self.cfg.english_glob != "NONE":
            english_files = glob(self.cfg.english_glob)[:self.cfg.max_english_files]
            random.shuffle(english_files)
            file_list += english_files

        if self.cfg.generated_glob != "NONE":
            generated_files = glob(self.cfg.generated_glob)[:self.cfg.max_generated_files]
            file_list += generated_files

        random.shuffle(file_list)

        raw_dataset = load_dataset("text", data_files={"train": file_list})["train"]
        split_dataset = raw_dataset.train_test_split(test_size=0.1, seed=42)

        train_ds = split_dataset["train"].map(
            self._tokenize_function,
            batched=True,
            remove_columns=["text"],
            num_proc=num_proc
        )
        val_ds = split_dataset["test"].map(
            self._tokenize_function,
            batched=True,
            remove_columns=["text"],
            num_proc=num_proc
        )

        lm_train = train_ds.map(self._group_texts, batched=True, num_proc=num_proc)
        lm_val = val_ds.map(self._group_texts, batched=True, num_proc=num_proc)

        config = GPT2Config(
            vocab_size=self.tokenizer.vocab_size,
            n_positions=self.cfg.block_size,
            n_ctx=self.cfg.block_size,
            n_embd=512,
            n_layer=12,
            n_head=8,
            pad_token_id=self.tokenizer.pad_token_id
        )
        model = GPT2LMHeadModel(config)

        training_args = TrainingArguments(
            output_dir=self.cfg.output_dir,
            overwrite_output_dir=True,
            per_device_train_batch_size=self.cfg.batch_size,
            gradient_accumulation_steps=self.cfg.gradient_accum_steps,
            num_train_epochs=self.cfg.epochs,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            learning_rate=float(self.cfg.learning_rate),
            warmup_steps=self.cfg.warmup_steps,
            dataloader_num_workers=num_proc,
            weight_decay=self.cfg.weight_decay,
            logging_dir=os.path.join(self.cfg.output_dir, "logs"),
            logging_steps=100,
            save_total_limit=self.cfg.save_limit,
            fp16=torch.cuda.is_available(),
            push_to_hub=False,
            ddp_find_unused_parameters=False
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=lm_train,
            eval_dataset=lm_val,
            tokenizer=self.tokenizer
        )

        trainer.train()
        trainer.save_model(self.cfg.model_name)
        self.tokenizer.save_pretrained(self.cfg.model_name)

        if is_main_process() and self.cfg.model_s3_upload_path and str(self.cfg.model_s3_upload_path).lower() != "null":
            parsed = urlparse(self.cfg.model_s3_upload_path)
            bucket = parsed.netloc
            prefix = parsed.path.lstrip("/")
            for root, _, files in os.walk(self.cfg.model_name):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.cfg.model_name)
                    s3_key = os.path.join(prefix, rel_path)
                    boto3.client("s3").upload_file(full_path, bucket, s3_key)
                    print(f"[RANK 0] Uploaded {full_path} → s3://{bucket}/{s3_key}")

# --- CLI Entrypoint ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    parser.add_argument("--cpu_local", action="store_true", help="Run with CPU backend for local debugging")
    args = parser.parse_args()

    if args.cpu_local:
        print("[DEBUG] Forcing torch CPU backend")
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    cfg = TrainConfig.from_yaml(args.config)
    trainer = LLMTrainer(cfg)
    trainer.prepare_data()
    trainer.train()

if __name__ == "__main__":
    main()
