import os
import random
from glob import glob
from collections import Counter
from transformers import PreTrainedTokenizerFast

# === CONFIG ===
TOKENIZER_PATH = "tokenizer/tokenizer.json"
TEXT_GLOB = "data/english_only/*.txt"
NUM_SAMPLES = 10000  # Target number of sampled lines
BLOCK_SIZE = 512     # Max length of tokenized input

# === Load tokenizer ===
print(f"Loading tokenizer from {TOKENIZER_PATH}")
tokenizer = PreTrainedTokenizerFast(tokenizer_file=TOKENIZER_PATH)
tokenizer.pad_token = "<pad>"
tokenizer.bos_token = "<s>"
tokenizer.eos_token = "</s>"
tokenizer.unk_token = "<unk>"
tokenizer.padding_side = "right"
tokenizer.truncation_side = "right"

print("Vocab size:", tokenizer.vocab_size)

# === Efficient sampling from large file set ===
def sample_lines_from_files(files, num_samples, sample_rate=0.002):
    sample = []
    rng = random.Random(42)
    for path in files:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if rng.random() < sample_rate:
                    sample.append(line)
                    if len(sample) >= num_samples:
                        return sample
    return sample

print("Sampling lines from text files...")
file_list = glob(TEXT_GLOB)
sample_lines = sample_lines_from_files(file_list, NUM_SAMPLES)
print(f"Sampled {len(sample_lines)} lines from {len(file_list)} files.")

# === Token-level analysis ===
max_token_id = 0
token_counts = Counter()
bigrams = Counter()
total_tokens = 0
total_chars = 0
bad_lines = 0

for line in sample_lines:
    try:
        encoded = tokenizer(
            line,
            truncation=True,
            max_length=BLOCK_SIZE,
            padding="max_length",
            return_attention_mask=False
        )
        input_ids = encoded["input_ids"]
        if any(tid > 2_147_483_647 for tid in input_ids):
            raise ValueError("Token ID exceeds int32 range.")
        token_counts.update(input_ids)
        bigrams.update(zip(input_ids[:-1], input_ids[1:]))
        max_token_id = max(max_token_id, max(input_ids))
        total_tokens += len(input_ids)
        total_chars += len(line)
    except Exception as e:
        print(f"⚠️  Skipping line due to error: {e}")
        bad_lines += 1

# === Entropy calculation ===
def entropy(counter):
    from math import log2
    total = sum(counter.values())
    return -sum((count / total) * log2(count / total) for count in counter.values() if count > 0)

token_entropy = entropy(token_counts)
bigram_entropy = entropy(bigrams)

# === Final report ===
print("\n=== Tokenizer Evaluation Report ===")
print(f"Max token ID seen      : {max_token_id}")
print(f"Total unique tokens    : {len(token_counts)}")
print(f"Token entropy          : {token_entropy:.3f}")
print(f"Bigram entropy         : {bigram_entropy:.3f}")
print(f"Avg tokens per line    : {total_tokens / len(sample_lines):.2f}")
print(f"Avg chars per line     : {total_chars / len(sample_lines):.2f}")
print(f"Skipped bad lines      : {bad_lines}")

if max_token_id > 2_147_483_647:
    print("❌ WARNING: Token ID exceeds int32 max (2147483647) — will crash PyArrow!")

if max_token_id > tokenizer.vocab_size:
    print("❌ WARNING: Token ID exceeds vocab size — tokenizer may be broken.")

print("\nTop 10 most frequent tokens:")
for tid, count in token_counts.most_common(10):
    decoded = tokenizer.decode([tid]).replace("\n", "\\n")
    print(f"  {tid:5d} | {count:7d} | {decoded!r}")
