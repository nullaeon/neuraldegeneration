#!/usr/bin/env bash

# Script: remove_heatdeathprotocol.sh

CONTAINER_NAME="heatdeathprotocol"

# Check if the container exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping container: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME"

    echo "Removing container: $CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
else
    echo "No container named '$CONTAINER_NAME' exists."
fi
