#!/bin/bash

# ---------------------------------------
# Kill a single EC2 instance by ID
# Usage: ./killaws.sh i-xxxxxxxxxxxxxxxxx
# ---------------------------------------

set -euo pipefail

INSTANCE_ID="${1:-}"
if [[ -z "$INSTANCE_ID" ]]; then
  echo "❌ Usage: $0 <instance-id>"
  exit 1
fi

AWS_REGION="${AWS_REGION:-us-west-2}"
AWS_PROFILE="${AWS_PROFILE:-default}"

echo "⚠️ Terminating instance: $INSTANCE_ID in region: $AWS_REGION using profile: $AWS_PROFILE"
read -p "Proceed? (y/n): " confirm
[[ $confirm == [yY] ]] || { echo "Aborted."; exit 0; }

aws ec2 terminate-instances \
  --instance-ids "$INSTANCE_ID" \
  --region "$AWS_REGION" \
  --profile "$AWS_PROFILE"

echo "✅ Termination request sent."
