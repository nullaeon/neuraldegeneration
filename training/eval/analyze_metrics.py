import math
from collections import Counter
from pathlib import Path
import re

# Load the generated text file
INPUT_FILE = "generated_large.txt"
RAW = Path(INPUT_FILE).read_text(encoding="utf-8")

# Split samples by marker
samples = [s.strip() for s in RAW.split("=== SAMPLE ===") if s.strip()]
print(f"Loaded {len(samples)} samples")

# Tokenizer: simple word-level for metric purposes
def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())

# Entropy calculation
def shannon_entropy(tokens):
    counts = Counter(tokens)
    total = len(tokens)
    probs = [c / total for c in counts.values()]
    return -sum(p * math.log2(p) for p in probs)

# n-gram generation
def ngrams(tokens, n):
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

# Diversity and repetition
def ngram_stats(tokens, n):
    ng = ngrams(tokens, n)
    total = len(ng)
    unique = len(set(ng))
    return {
        "total": total,
        "unique": unique,
        "ratio": unique / total if total else 0,
        "repetition": 1 - (unique / total) if total else 0
    }

# Aggregate metrics
entropies = []
ngram_metrics = {1: [], 2: [], 3: []}

for text in samples:
    tokens = tokenize(text)
    entropies.append(shannon_entropy(tokens))

    for n in ngram_metrics:
        ngram_metrics[n].append(ngram_stats(tokens, n))

# Output results
def average(lst): return sum(lst) / len(lst) if lst else 0

print("\n=== Metrics Across Samples ===")
print(f"Avg token entropy: {average(entropies):.4f}")

for n in ngram_metrics:
    avg_ratio = average([m["ratio"] for m in ngram_metrics[n]])
    avg_repetition = average([m["repetition"] for m in ngram_metrics[n]])
    print(f"{n}-gram diversity: {avg_ratio:.4f} | repetition: {avg_repetition:.4f}")
