#!/bin/bash

set -e

# --- Configuration ---
IMAGE_NAME="heatdeathprotocol"
TAG="latest"
PYTHON_SCRIPT="./training/train_multi_gpu.py"
DEFAULT_ARGS="--config training/configs/dev_cloud_test.yaml"

# Allow args override
ARGS=${1:-$DEFAULT_ARGS}

# --- Ensure cache dir exists ---
mkdir -p ./hf_cache

# --- Build the image ---
echo "📦 Building Docker image..."
docker build -t "${IMAGE_NAME}:${TAG}" .

# --- Run the container ---
echo "🚀 Running container..."
docker run --rm -i \
    --gpus all \
    --name heatdeathprotocol \
    --env-file .env \
    -v "$(pwd)":/workspace \
    -v "$(pwd)/hf_cache":/mnt/hf_cache:rw \
    -e LOCAL_UID="$(id -u)" \
    -e LOCAL_GID="$(id -g)" \
    -w /workspace \
    -v "$HOME/.aws:/aws:ro" \
    -e AWS_SHARED_CREDENTIALS_FILE=/aws/credentials \
    -e AWS_CONFIG_FILE=/aws/config \
    "${IMAGE_NAME}:${TAG}" \
    torchrun --nproc_per_node="$(nvidia-smi -L | wc -l)" "$PYTHON_SCRIPT" $ARGS
