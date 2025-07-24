#!/bin/bash

# === INPUT ===
TOKEN_CODE="$1"
PROFILE_NAME="$2"

if [ -z "$TOKEN_CODE" ] || [ -z "$PROFILE_NAME" ]; then
  echo "Usage: $0 <MFA_CODE> <AWS_PROFILE>"
  exit 1
fi

# === CONFIG ===
DURATION_SECONDS=129600  # 36 hours

# === DYNAMICALLY GET MFA ARN ===
MFA_DEVICE_ARN=$(aws iam list-mfa-devices \
  --profile "$PROFILE_NAME" \
  | jq -r '.MFADevices[0].SerialNumber')

if [ -z "$MFA_DEVICE_ARN" ] || [ "$MFA_DEVICE_ARN" == "null" ]; then
  echo "❌ Could not retrieve MFA device ARN. Check profile or permissions."
  exit 1
fi

# === GET TEMPORARY CREDENTIALS ===
SESSION=$(aws sts get-session-token \
  --serial-number "$MFA_DEVICE_ARN" \
  --token-code "$TOKEN_CODE" \
  --duration-seconds "$DURATION_SECONDS" \
  --profile "$PROFILE_NAME")

if [ $? -ne 0 ]; then
  echo "❌ Failed to get session token"
  exit 1
fi

# === EXPORT TO CURRENT SHELL ===
export AWS_ACCESS_KEY_ID=$(echo "$SESSION" | jq -r .Credentials.AccessKeyId)
export AWS_SECRET_ACCESS_KEY=$(echo "$SESSION" | jq -r .Credentials.SecretAccessKey)
export AWS_SESSION_TOKEN=$(echo "$SESSION" | jq -r .Credentials.SessionToken)

echo "✅ MFA login successful. Temporary credentials now active."
echo "⏳ Expires: $(echo "$SESSION" | jq -r .Credentials.Expiration)"
