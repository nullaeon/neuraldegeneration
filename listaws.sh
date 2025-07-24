aws ec2 describe-instances \
  --filters Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' \
  --output table \
  --region "$AWS_REGION" \
  --profile "$AWS_PROFILE"
