## Objective

To investigate whether recursively training a language model on its own synthetic output causes a measurable collapse in information entropy, diversity, and generation complexity over time.

---

## Experimental Protocol

### Phase 1: Base Model Initialization

- **Model**: Train LLM₀ from scratch (e.g., 100M parameters) or fine-tune a small pretrained model (e.g., GPT-2 124M) on a curated human-authored corpus.
- **Corpus C₀**: ~100M tokens from Project Gutenberg or similar
- **Checkpoint**: Save model weights `M₀`

---

### Phase 2: Recursive Corpus Expansion

Repeat for N generations (e.g., 10):

1. **Generation**
    - Use current model `M_t` to generate synthetic text `S_t`
    - No prompts; pure freeform generation
2. **Corpus Update**
    - Form new corpus: `C_{t+1} = C_0 ∪ S_0 ∪ S_1 ∪ ... ∪ S_t`
    - Optional: tag each sample as `synthetic_t` or `human`
3. **Model Training**
    - Train a new model `M_{t+1}` on corpus `C_{t+1}`
4. **Metrics Logging**
    - Evaluate entropy and diversity of corpus and model output
    - Save model and training metadata

---

## Evaluation Metrics

### Corpus-Level

- **Token entropy** (Shannon)
- **N-gram diversity**
- **Type-token ratio (TTR)**
- **Zipf distribution slope**
- **Topic distribution variance** (e.g., via LDA)

### Model Output-Level

- **Token-level output entropy**
- **KL divergence from M₀**
- **Syntactic diversity (POS-tag sequences)**
- **Sentence length variance**
- **BLEU/METEOR vs held-out human samples**

---

## Hypothesis

As synthetic data accumulates in the corpus, it will increasingly saturate the model's training distribution, leading to:

- Decreasing entropy in corpus and output
- Loss of lexical, syntactic, and semantic diversity
- Templated or degenerate model generations

This simulates a form of linguistic heat death via recursive self-pollution.

---

## Optional Extensions

- Vary temperature or sampling strategy to test resilience
- Introduce adversarial or anti-collapse objectives
- Visualize entropy curves across generations