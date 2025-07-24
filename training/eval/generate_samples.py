import torch
from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast
from pathlib import Path
import logging
import time
import random

# ==== Config ====
MODEL_PATH = "../llm0"
OUTPUT_FILE = "generated_large.txt"
NUM_SAMPLES = 20000
MAX_LENGTH = 256
TEMPERATURE = 1.0
TOP_P = 0.95
REPETITION_PENALTY = 1.2
LOG_INTERVAL = 100
SEED = 42  # Optional
# ================

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Set seed for reproducibility
torch.manual_seed(SEED)
random.seed(SEED)

# Load model and tokenizer
tokenizer = PreTrainedTokenizerFast.from_pretrained(MODEL_PATH)
model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# Clear existing file if exists
Path(OUTPUT_FILE).unlink(missing_ok=True)

start_time = time.time()

with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
    for i in range(1, NUM_SAMPLES + 1):
        input_ids = tokenizer.encode(tokenizer.bos_token or "<s>", return_tensors="pt").to(device)

        with torch.no_grad():
            output = model.generate(
                input_ids=input_ids,
                max_length=MAX_LENGTH,
                do_sample=True,
                top_p=TOP_P,
                temperature=TEMPERATURE,
                repetition_penalty=REPETITION_PENALTY,
                pad_token_id=tokenizer.pad_token_id
            )

        text = tokenizer.decode(output[0], skip_special_tokens=True).strip()
        f.write(text + "\n\n=== SAMPLE ===\n\n")

        if i % LOG_INTERVAL == 0 or i == NUM_SAMPLES:
            elapsed = time.time() - start_time
            logging.info(f"Generated {i}/{NUM_SAMPLES} samples — Elapsed: {elapsed:.1f}s")

logging.info("✅ Generation complete.")
