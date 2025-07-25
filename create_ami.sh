#!/bin/bash
set -euo pipefail

# -------------------------
# AMI Creation Script
# -------------------------

# Customize this section
AMI_NAME="nullaeon-cuda12.8-ubuntu2204-$(date +%Y%m%d-%H%M%S)"
AMI_DESCRIPTION="Stable training environment with CUDA 12.8, PyTorch, transformers, and dependencies pre-installed"
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\" '{print $4}')

echo "Creating AMI from instance: $INSTANCE_ID"
echo "Region: $REGION"
echo "AMI Name: $AMI_NAME"

# Create the AMI
AMI_ID=$(aws ec2 create-image \
  --region "$REGION" \
  --instance-id "$INSTANCE_ID" \
  --name "$AMI_NAME" \
  --description "$AMI_DESCRIPTION" \
  --no-reboot \
  --query 'ImageId' \
  --output text)

echo "✅ AMI creation requested: $AMI_ID"

# Optional: tag the AMI
aws ec2 create-tags \
  --region "$REGION" \
  --resources "$AMI_ID" \
  --tags Key=Name,Value="$AMI_NAME" Key=Project,Value=NeuralDegen

echo "📦 AMI tagged and ready: $AMI_ID"
