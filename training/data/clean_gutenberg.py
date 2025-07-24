import os
from pathlib import Path

INPUT_DIR = "raw"
OUTPUT_DIR = "cleaned"

HEADER_START = "*** START OF THIS PROJECT GUTENBERG"
FOOTER_START = "*** END OF THIS PROJECT GUTENBERG"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for filepath in Path(INPUT_DIR).glob("*.txt"):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    start_idx, end_idx = 0, len(lines)
    for i, line in enumerate(lines):
        if HEADER_START in line:
            start_idx = i + 1
        elif FOOTER_START in line:
            end_idx = i
            break

    clean_text = lines[start_idx:end_idx]
    output_path = Path(OUTPUT_DIR) / filepath.name
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(clean_text)

    print(f"Cleaned: {filepath.name} -> {output_path}")
