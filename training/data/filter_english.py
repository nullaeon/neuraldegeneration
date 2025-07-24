import csv
from pathlib import Path
import shutil

METADATA_FILE = "metadata.csv"
INPUT_DIR = Path("cleaned")
OUTPUT_DIR = Path("english_only")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

english_ids = set()
with open(METADATA_FILE, "r", encoding="utf-8", errors="ignore") as f:
    reader = csv.reader(f)
    header = next(reader)  # Skip header if present
    for row in reader:
        if len(row) < 6:
            continue
        lang_field = row[5].strip()
        if lang_field == "['en']":
            pg_id = row[0].strip()
            english_ids.add(pg_id)

# Copy matching files
count = 0
for pg_id in english_ids:
    filename = f"{pg_id}_raw.txt"
    src_path = INPUT_DIR / filename
    dst_path = OUTPUT_DIR / filename
    if src_path.exists():
        shutil.copy(src_path, dst_path)
        count += 1
    else:
        print(f"⚠️ Missing file: {filename}")

print(f"\n✅ Copied {count} English files to {OUTPUT_DIR}/")
