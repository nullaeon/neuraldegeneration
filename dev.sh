#!/usr/bin/env bash

docker run --rm -it \
    --gpus all \
    --name heatdeathprotocol \
    --env-file .env \
    -v "$(pwd)":/workspace \
    -v /mnt/hf_cache:/mnt/hf_cache:rw \
    -e LOCAL_UID=$(id -u) \
    -e LOCAL_GID=$(id -g) \
    -w /workspace \
    -v ~/.aws:/aws:ro \
    -e AWS_SHARED_CREDENTIALS_FILE=/aws/credentials \
    -e AWS_CONFIG_FILE=/aws/config \
    heatdeathprotocol \
    bash
