# Neural Degeneration
The **NeuralDegeneration** repo is an experimental playground for studying *synthetic collapse* in recursively-trained language models. The goal: simulate an LLM ingesting its own generations until linguistic entropy approaches heat death. Outputs become predictably uniform, boring, or degenerate.

We start with a human-authored corpus (e.g., a subset of Project Gutenberg), train a base model, generate new text, add it back into the corpus, and repeat. Over time, the dataset gets increasingly saturated with synthetic data. The experiment explores how entropy and diversity metrics evolve across generations.

More details of experimental design can be found in the `experimental_design_phase_1.md` document. 

This experiment is based on research conducted in the following works: 
[THE CURIOUS CASE OF NEURAL TEXT DeGENERATION, (Holtzman et al., 2020)](https://arxiv.org/abs/1904.09751)
[AI models collapse when trained on recursively generated data, (Shumailov et al., 2024)](https://www.nature.com/articles/s41586-024-07566-y)

## Core Components

| Directory / Script             | Purpose                                              |
|-------------------------------|------------------------------------------------------|
| `training/train.py`           | Main training loop using HuggingFace Trainer API     |
| `training/eval/`              | Entropy, repetition, and diversity metric calculations |
| `training/data/`              | Data cleaning, filtering, and synthetic data generation |
| `training/tokenizer/`         | Training and loading custom tokenizers               |
| `training/configs/`           | YAML config files for training runs (cloud/local)    |
| `*.sh` scripts                | Build, run, and AWS automation scripts                |

## Basic Workflow

1. **Start with a seed corpus.**  
   a. Gather the project Gutenberg corpus using the pipeline in [this repo](https://github.com/pgcorpus/gutenberg) and use `training/data/subset_gutenberg.py` and filtering scripts to clean and subset Project Gutenberg texts.

2. **Train initial model (`LLM₀`).**  
   Run training using:
   ```bash
   ./run.sh training/train.py --config training/configs/dev_local_test.yaml
   ```
   ^^^ fill out the config file yourself using the example

3. **Generate samples.**  
   Use `training/eval/generate_samples.py` to create new text samples.

4. **Evaluate entropy and diversity.**  
   Run:
   ```bash
   python training/eval/analyze_metrics.py
   ```

5. **Add generated samples to corpus.**  
   Merge with the original corpus and repeat the training cycle.

6. **Track entropy collapse.**  
   Over generations, monitor:
   - Shannon entropy
   - n-gram diversity
   - Repetition rate

## Requirements

- Python 3.11
- PyTorch, HuggingFace Transformers, Datasets
- Docker (for cloud setup)
- AWS CLI (for EC2 automation with A100 or G5 instances)
- Potentially others, I tried to make most everything handled by the docker image, but `GPUSETUP.md` helps ensure you can use the GPU from within the docker

Use the provided Docker image and use the bash scripts as necessary: 
- `pull.sh` to pull the latest docker image from quay.io, may need to login with `docker login quay.io`
- `build.sh` to build the docker image locally (no pulling, worst case takes 5 minutes)
- `run.sh` to run a training session from inside the container after everything is configured
- `dev.sh` to interactively go inside the container, good for manual experimentation
- `launch_aws.sh` for launching an EC2 instance, requires a lot of configuration (fill out the .env.example file, please do not commit it anywhere with your secrets), including IAM permissions, but if you're feeling up to spending a weekend on this, very doable. The script is currently configured to kill the train.py script after 25 minutes, and to kill the entire EC2 instance after 30 minutes. Update as needed.


## ⚠️ Warnings

- This repo will happily consume your GPU (local) or your wallet (AWS). Training even 100M-300M models for multiple generations can take GPU DAYS, not hours. And good luck getting approved for a P4/P5 instance on AWS without a slide deck and VC backing.
- Recursive LLM training /should/ result in unpredictable behavior. You're literally amplifying the model's own hallucinations.

## License
Apache 2.0, see the included LICENSE file.
