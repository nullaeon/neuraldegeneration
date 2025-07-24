#!/bin/bash
# Usage: ./aws-ssh.sh <instance-id> [profile]

INSTANCE_ID="$1"
AWS_PROFILE="${2:-testrunner}"  # Optional AWS profile fallback

# Look up the public IP and key name
read -r PUBLIC_IP KEY_NAME <<< $(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].[PublicIpAddress,KeyName]' \
  --output text \
  --profile "$AWS_PROFILE")

if [[ -z "$PUBLIC_IP" || "$PUBLIC_IP" == "None" ]]; then
  echo "❌ Could not retrieve public IP for instance $INSTANCE_ID"
  exit 1
fi

# Launch SSH
echo "🔗 Connecting to $PUBLIC_IP using key $KEY_NAME..."
ssh -i "~/.ssh/${KEY_NAME}.pem" "ubuntu@${PUBLIC_IP}"
