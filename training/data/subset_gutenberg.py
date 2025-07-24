import os
import random
import shutil
from pathlib import Path

# --- Configuration ---
INPUT_DIR = "./english_only"
OUTPUT_DIR = "./english_only_subset"
NUM_FILES = 1000
SEED = 42

def main():
    input_path = Path(INPUT_DIR)
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get all .txt files
    all_txt_files = sorted(input_path.glob("*.txt"))
    print(f"Found {len(all_txt_files)} .txt files in {INPUT_DIR}")

    if len(all_txt_files) < NUM_FILES:
        raise ValueError(f"Requested {NUM_FILES} files, but only found {len(all_txt_files)}")

    # Deterministic shuffle
    random.seed(SEED)
    selected_files = random.sample(all_txt_files, NUM_FILES)

    # Copy to output dir
    for src_path in selected_files:
        dst_path = output_path / src_path.name
        shutil.copy(src_path, dst_path)

    print(f"✅ Copied {NUM_FILES} files to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
