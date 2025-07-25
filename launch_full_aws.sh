#!/bin/bash

# ---------------------------------------
# HD Protocol Instance Launcher (Spot or On-Demand)
# ---------------------------------------

set -euo pipefail

# --- Configuration from environment variables ---

AMI_ID="${AMI_ID:?Must set AMI_ID}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g5.xlarge}"
KEY_NAME="${KEY_NAME:?Must set KEY_NAME}"
SECURITY_GROUP="${SECURITY_GROUP:?Must set SECURITY_GROUP}"
INSTANCE_PROFILE="${INSTANCE_PROFILE:?Must set INSTANCE_PROFILE}"
AWS_REGION="${AWS_REGION:-us-west-2}"
REPO_URL="${REPO_URL:-https://github.com/yourusername/hd-protocol.git}"
CONFIG_S3_PATH="${CONFIG_S3_PATH:?Must set CONFIG_S3_PATH (e.g. s3://bucket/configs/config.yaml)}"
CONFIG_LOCAL_NAME="${CONFIG_LOCAL_NAME:-config.yaml}"
TAG_NAME="${TAG_NAME:-HD-Protocol-Train}"
AWS_PROFILE="${AWS_PROFILE:?Must set the aws user profile for resource access}"
MARKET_TYPE="${MARKET_TYPE:-spot}"
VOLUME_SIZE="${VOLUME_SIZE:-128}"

# --- Optional prompt to confirm launch ---
echo "⚠️ Launching a $MARKET_TYPE instance with $INSTANCE_TYPE and ${VOLUME_SIZE}GB root volume in region $AWS_REGION"
read -p "Proceed? (y/n): " confirm
[[ $confirm == [yY] ]] || { echo "Aborted."; exit 1; }

echo "⚠️  You will be launching a full training run on $INSTANCE_TYPE, with a timeout of 48 hours, this could cost as much as 50.0 USD or more..."
read -p "Proceed? (y/n): " confirm
[[ $confirm == [yY] ]] || { echo "Aborted."; exit 1; }

# --- AZ → Subnet Mapping ---
declare -A SUBNET_MAP=(
  [us-west-2a]=subnet-0693d571076dd795a
  [us-west-2b]=subnet-0bbb2898ec2714531
  [us-west-2c]=subnet-0cffee235518b970e
  [us-west-2d]=subnet-09c5c61182de22c46
)

# --- Block Device Mapping (root volume size override) ---
BLOCK_DEVICE_MAPPINGS=$(cat <<EOF
[
  {
    "DeviceName": "/dev/sda1",
    "Ebs": {
      "VolumeSize": $VOLUME_SIZE,
      "VolumeType": "gp3",
      "DeleteOnTermination": true
    }
  }
]
EOF
)

# --- Create user data temp file ---
USER_DATA_FILE=$(mktemp)
cat > "$USER_DATA_FILE" <<EOF
#!/bin/bash
set -euxo pipefail
exec > /var/log/user_data.log 2>&1

echo "[INFO] Disabling unattended upgrades"
systemctl stop unattended-upgrades || true
systemctl disable unattended-upgrades || true
apt purge unattended-upgrades -y || true

echo "[INFO] Installing core packages"
apt-get update
apt-get install -y git unzip htop tmux at python3-pip

echo "[INFO] Enabling Docker"
systemctl enable --now docker
usermod -aG docker ubuntu

echo "[INFO] Enabling atd"
systemctl enable --now atd

cd /home/ubuntu

echo "[INFO] Setting up logs and repo"
mkdir -p logs
git clone $REPO_URL repo
cd repo

echo "[INFO] Downloading config from S3: $CONFIG_S3_PATH"
aws s3 cp "$CONFIG_S3_PATH" "$CONFIG_LOCAL_NAME"

echo "[INFO] Preparing environment"
mkdir -p /home/ubuntu/hf_cache
chown -R ubuntu:ubuntu /home/ubuntu/hf_cache
echo "HF_HOME=/home/ubuntu/hf_cache" > .env

chmod +x cloud_run.sh

echo "[INFO] Scheduling auto-shutdown in 48 hours"
echo "shutdown -h now" | at now + 47 hours

echo "[INFO] Starting training at \$(date)" | tee -a /home/ubuntu/logs/train.log
export TRANSFORMERS_CACHE=/home/ubuntu/hf_cache
timeout 48h ./cloud_run.sh "--config $CONFIG_LOCAL_NAME" >> /home/ubuntu/logs/train.log 2>&1

echo "[INFO] Training completed at \$(date)"
shutdown -h now
EOF

# --- Pre-flight credential check ---
aws sts get-caller-identity --profile "$AWS_PROFILE" > /dev/null || {
  echo "❌ Invalid or expired AWS credentials for profile '$AWS_PROFILE'"
  rm -f "$USER_DATA_FILE"
  exit 1
}

# --- Launch EC2 Instance with fallback across AZs ---
SUCCESS=0

for AZ in us-west-2a us-west-2b us-west-2c us-west-2d; do
  SUBNET_ID="${SUBNET_MAP[$AZ]}"
  echo "[INFO] Attempting launch in $AZ (subnet: $SUBNET_ID)..."

  set +e
  LAUNCH_ARGS=(
    --image-id "$AMI_ID"
    --count 1
    --instance-type "$INSTANCE_TYPE"
    --key-name "$KEY_NAME"
    --security-group-ids "$SECURITY_GROUP"
    --subnet-id "$SUBNET_ID"
    --iam-instance-profile Name="$INSTANCE_PROFILE"
    --user-data file://"$USER_DATA_FILE"
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TAG_NAME}]"
    --region "$AWS_REGION"
    --profile "$AWS_PROFILE"
    --block-device-mappings "$BLOCK_DEVICE_MAPPINGS"
  )

  if [[ "$MARKET_TYPE" == "spot" ]]; then
    LAUNCH_ARGS+=(--instance-market-options 'MarketType=spot')
  fi

  LAUNCH_OUTPUT=$(aws ec2 run-instances "${LAUNCH_ARGS[@]}" 2>&1)
  STATUS=$?
  set -e

  if [[ $STATUS -eq 0 ]]; then
    echo "✅ $MARKET_TYPE instance requested successfully in $AZ"
    echo "$LAUNCH_OUTPUT" | jq '.Instances[] | {InstanceId, InstanceType, LaunchTime, State}'
    echo "$LAUNCH_OUTPUT" > .last_launch.json
    SUCCESS=1
    break
  else
    echo "❌ Launch failed in $AZ:"
    echo "$LAUNCH_OUTPUT"
  fi
done

rm -f "$USER_DATA_FILE"

if [[ $SUCCESS -ne 1 ]]; then
  echo "❌ All AZs failed. No capacity available in any subnet."
  exit 1
fi
