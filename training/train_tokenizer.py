from tokenizers import ByteLevelBPETokenizer
from pathlib import Path
import os

# Folder containing your cleaned corpus
CORPUS_DIR = "data/english_only"
FILES = list(Path(CORPUS_DIR).glob("*.txt"))

# Output directory for tokenizer
OUTPUT_DIR = "tokenizer"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Train tokenizer
tokenizer = ByteLevelBPETokenizer()
tokenizer.train(
    files=[str(f) for f in FILES],
    vocab_size=32000,
    min_frequency=2,
    special_tokens=["<pad>", "<s>", "</s>", "<unk>", "<mask>"]
)

# Save to disk
tokenizer.save_model(OUTPUT_DIR)
tokenizer.save("tokenizer/tokenizer.json")
print("Tokenizer trained and saved to", OUTPUT_DIR)

