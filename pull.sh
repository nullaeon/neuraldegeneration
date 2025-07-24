#!/usr/bin/env bash

# CONFIG
QUAY_USERNAME="nullaeon"
QUAY_REPO="heatdeathprotocol"
TAG="latest"

# Full image name
QUAY_IMAGE="quay.io/${QUAY_USERNAME}/${QUAY_REPO}:${TAG}"

echo "📥 Pulling latest image from Quay.io: ${QUAY_IMAGE}"
docker pull "${QUAY_IMAGE}"

echo "✅ Image pulled successfully!"

# Optional: Run the image interactively
echo "🚀 Starting container..."
docker run -it --rm \
    -v "$(pwd):/workspace" \
    -w /workspace \
    "${QUAY_IMAGE}" bash
