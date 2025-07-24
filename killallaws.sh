aws ec2 describe-instances \
  --filters Name=instance-state-name,Values=running \
  --region "$AWS_REGION" \
  --profile "$AWS_PROFILE" \
  --query 'Reservations[*].Instances[*].InstanceId' \
  --output text | xargs -r aws ec2 terminate-instances \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --instance-ids
