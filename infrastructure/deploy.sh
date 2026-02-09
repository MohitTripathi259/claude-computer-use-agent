#!/bin/bash
#
# Deploy Computer-Use Agent to AWS ECS
#
# This script:
# 1. Creates ECR repository
# 2. Builds and pushes the container image
# 3. Creates ECS cluster
# 4. Creates IAM roles
# 5. Registers task definition
# 6. Optionally creates VPC resources
#
# Prerequisites:
# - AWS CLI configured with appropriate permissions
# - Docker installed and running
# - jq installed for JSON parsing

set -e

# Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
ECR_REPO="computer-use-container"
ECS_CLUSTER="computer-use-cluster"
TASK_FAMILY="computer-use-agent"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=============================================="
echo "Computer-Use Agent Deployment"
echo "=============================================="
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo "ECR Repo: $ECR_REPO"
echo "ECS Cluster: $ECS_CLUSTER"
echo "=============================================="

# Change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# ===================
# 1. Create ECR Repository
# ===================
echo ""
echo ">>> Creating ECR repository..."

aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository \
        --repository-name $ECR_REPO \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256

echo "✓ ECR repository ready"

# ===================
# 2. Build and Push Container Image
# ===================
echo ""
echo ">>> Building container image..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build image
docker build -t $ECR_REPO:latest ./container

# Tag for ECR
docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# Push to ECR
echo ">>> Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

echo "✓ Container image pushed"

# ===================
# 3. Create ECS Cluster
# ===================
echo ""
echo ">>> Creating ECS cluster..."

aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION 2>/dev/null | \
    grep -q '"status": "ACTIVE"' || \
    aws ecs create-cluster \
        --cluster-name $ECS_CLUSTER \
        --region $AWS_REGION \
        --capacity-providers FARGATE FARGATE_SPOT \
        --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1

echo "✓ ECS cluster ready"

# ===================
# 4. Create IAM Roles (if needed)
# ===================
echo ""
echo ">>> Checking IAM roles..."

# Task Execution Role
if ! aws iam get-role --role-name ecsTaskExecutionRole 2>/dev/null; then
    echo "Creating ecsTaskExecutionRole..."

    cat > /tmp/trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    aws iam create-role \
        --role-name ecsTaskExecutionRole \
        --assume-role-policy-document file:///tmp/trust-policy.json

    aws iam attach-role-policy \
        --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
fi

# Task Role (for container to access AWS services)
if ! aws iam get-role --role-name computerUseTaskRole 2>/dev/null; then
    echo "Creating computerUseTaskRole..."

    aws iam create-role \
        --role-name computerUseTaskRole \
        --assume-role-policy-document file:///tmp/trust-policy.json

    # Add minimal permissions (expand as needed)
    cat > /tmp/task-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name computerUseTaskRole \
        --policy-name ComputerUseTaskPolicy \
        --policy-document file:///tmp/task-policy.json
fi

echo "✓ IAM roles ready"

# ===================
# 5. Create CloudWatch Log Group
# ===================
echo ""
echo ">>> Creating CloudWatch log group..."

aws logs create-log-group \
    --log-group-name /ecs/computer-use-agent \
    --region $AWS_REGION 2>/dev/null || true

echo "✓ Log group ready"

# ===================
# 6. Register Task Definition
# ===================
echo ""
echo ">>> Registering task definition..."

# Process task definition template
sed -e "s/\${AWS_ACCOUNT_ID}/$AWS_ACCOUNT_ID/g" \
    -e "s/\${AWS_REGION}/$AWS_REGION/g" \
    infrastructure/task-definition.json > /tmp/task-def.json

aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-def.json \
    --region $AWS_REGION

echo "✓ Task definition registered"

# ===================
# Summary
# ===================
echo ""
echo "=============================================="
echo "Deployment Complete!"
echo "=============================================="
echo ""
echo "ECR Image: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest"
echo "ECS Cluster: $ECS_CLUSTER"
echo "Task Definition: $TASK_FAMILY"
echo ""
echo "Next steps:"
echo "1. Configure networking (VPC, subnets, security groups)"
echo "2. Set environment variables:"
echo "   export AWS_REGION=$AWS_REGION"
echo "   export ECS_CLUSTER=$ECS_CLUSTER"
echo "   export ECS_TASK_DEFINITION=$TASK_FAMILY"
echo "   export ECS_SUBNETS=subnet-xxx,subnet-yyy"
echo "   export ECS_SECURITY_GROUPS=sg-xxx"
echo "   export USE_LOCAL_CONTAINER=false"
echo ""
echo "3. Run the orchestrator API"
echo "=============================================="
