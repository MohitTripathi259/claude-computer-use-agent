# 🚀 Computer-Use Agent Deployment Plan

## ✅ Cleanup Status: COMPLETE

**Removed:**
- ✅ screenshots/ (2.8MB test data)
- ✅ ci_competitive_report.txt
- ✅ ci_competitive_report_NEW.txt
- ✅ ci_competitor_urls.txt
- ✅ ci_competitor_urls_NEW.txt
- ✅ Python cache files (__pycache__, *.pyc)

**Security Check:**
- ⚠️  `.env` file exists with secrets - **WILL NOT BE DEPLOYED** (in .gitignore)

---

## 📦 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AWS CLOUD                            │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │              API GATEWAY / ALB                   │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │          ORCHESTRATOR (ECS Fargate)             │   │
│  │    - FastAPI application                         │   │
│  │    - Session management                          │   │
│  │    - Agent coordination                          │   │
│  │    Port: 8000                                    │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │       CONTAINER (ECS Fargate Task)              │   │
│  │    - Xvfb virtual display                        │   │
│  │    - Playwright/Chromium browser                 │   │
│  │    - Computer-use tools                          │   │
│  │    - Per-session isolation                       │   │
│  │    Port: 8080                                    │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │              STORAGE                             │   │
│  │    S3: Screenshots, artifacts                    │   │
│  │    DynamoDB: Session data, metadata              │   │
│  │    CloudWatch: Logs, metrics                     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Pre-Deployment Checklist

### 1. AWS Prerequisites

- [ ] AWS CLI configured (`aws configure`)
- [ ] Docker installed and running
- [ ] `jq` installed for JSON parsing
- [ ] AWS account with appropriate permissions:
  - ECR (create repository, push images)
  - ECS (create cluster, register tasks, run tasks)
  - IAM (create roles, attach policies)
  - CloudWatch Logs (create log groups)
  - VPC (create/configure networking - optional)
  - S3 (create buckets for screenshots)
  - DynamoDB (create tables for sessions)

### 2. Environment Configuration

**Required Environment Variables:**

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...         # REQUIRED - Get from Anthropic Console

# AWS Configuration
AWS_REGION=us-east-1                 # Your AWS region
AWS_ACCOUNT_ID=123456789012          # Your AWS account ID

# ECS Configuration
ECS_CLUSTER=computer-use-cluster
ECS_TASK_DEFINITION=computer-use-agent
ECS_SUBNETS=subnet-xxx,subnet-yyy    # Your VPC subnets
ECS_SECURITY_GROUPS=sg-xxx           # Your security group

# Deployment Mode
USE_LOCAL_CONTAINER=false            # Set to false for production

# S3 Storage
S3_BUCKET=computer-use-screenshots-{account-id}

# DynamoDB
DDB_TABLE_SNAPSHOTS=computer-use-sessions
```

### 3. Networking Setup

- [ ] VPC created with public/private subnets
- [ ] Security groups configured:
  - Orchestrator: Allow inbound 8000 from ALB/API Gateway
  - Container: Allow inbound 8080 from Orchestrator
  - Both: Allow outbound to internet (for Anthropic API)
- [ ] NAT Gateway (if using private subnets)
- [ ] Application Load Balancer (optional, for public access)

### 4. Storage Setup

**S3 Bucket:**
```bash
aws s3 mb s3://computer-use-screenshots-${AWS_ACCOUNT_ID}
```

**DynamoDB Table:**
```bash
aws dynamodb create-table \
    --table-name computer-use-sessions \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
    --key-schema AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

---

## 🚀 Deployment Steps

### Option 1: Automated Deployment (Recommended)

```bash
# 1. Navigate to project root
cd computer_use_codebase

# 2. Set AWS region
export AWS_REGION=us-east-1

# 3. Run deployment script
bash infrastructure/deploy.sh
```

**This script will:**
1. ✅ Create ECR repository
2. ✅ Build container image
3. ✅ Push image to ECR
4. ✅ Create ECS cluster
5. ✅ Create IAM roles
6. ✅ Register task definition
7. ✅ Create CloudWatch log group

### Option 2: Manual Deployment

#### Step 1: Build and Push Container Image

```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1

# Create ECR repository
aws ecr create-repository \
    --repository-name computer-use-container \
    --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build container image
docker build -t computer-use-container:latest ./container

# Tag for ECR
docker tag computer-use-container:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/computer-use-container:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/computer-use-container:latest
```

#### Step 2: Build and Push Orchestrator Image

```bash
# Build orchestrator image
docker build -f Dockerfile.orchestrator -t computer-use-orchestrator:latest .

# Create ECR repository for orchestrator
aws ecr create-repository \
    --repository-name computer-use-orchestrator \
    --region $AWS_REGION

# Tag and push
docker tag computer-use-orchestrator:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/computer-use-orchestrator:latest

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/computer-use-orchestrator:latest
```

#### Step 3: Create ECS Cluster

```bash
aws ecs create-cluster \
    --cluster-name computer-use-cluster \
    --region $AWS_REGION \
    --capacity-providers FARGATE FARGATE_SPOT
```

#### Step 4: Register Task Definitions

```bash
# Update task definition with your account ID and region
sed -e "s/\${AWS_ACCOUNT_ID}/$AWS_ACCOUNT_ID/g" \
    -e "s/\${AWS_REGION}/$AWS_REGION/g" \
    infrastructure/task-definition.json > /tmp/task-def.json

# Register task definition
aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-def.json \
    --region $AWS_REGION
```

#### Step 5: Run Orchestrator Service

```bash
# Create ECS service for orchestrator
aws ecs create-service \
    --cluster computer-use-cluster \
    --service-name computer-use-orchestrator \
    --task-definition computer-use-orchestrator:1 \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --region $AWS_REGION
```

---

## 🔒 Security Configuration

### IAM Role Permissions

**Task Execution Role** (ecsTaskExecutionRole):
- AmazonECSTaskExecutionRolePolicy (managed)

**Task Role** (computerUseTaskRole) - Add these policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/ecs/computer-use-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::computer-use-screenshots-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/computer-use-sessions"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:RunTask",
        "ecs:StopTask",
        "ecs:DescribeTasks"
      ],
      "Resource": "*"
    }
  ]
}
```

### Secrets Management

**DO NOT commit secrets to repository!**

Store secrets in AWS Systems Manager Parameter Store or Secrets Manager:

```bash
# Store Anthropic API key
aws secretsmanager create-secret \
    --name /computer-use/anthropic-api-key \
    --secret-string "sk-ant-..." \
    --region $AWS_REGION

# Reference in task definition
# "secrets": [
#   {
#     "name": "ANTHROPIC_API_KEY",
#     "valueFrom": "arn:aws:secretsmanager:region:account:secret:/computer-use/anthropic-api-key"
#   }
# ]
```

---

## 📊 Monitoring & Logging

### CloudWatch Logs

**Log Groups:**
- `/ecs/computer-use-orchestrator` - Orchestrator logs
- `/ecs/computer-use-agent` - Container/agent logs

**View logs:**
```bash
# Orchestrator logs
aws logs tail /ecs/computer-use-orchestrator --follow

# Container logs
aws logs tail /ecs/computer-use-agent --follow
```

### CloudWatch Metrics

Monitor these metrics:
- ECS Task CPU/Memory utilization
- API Gateway request count (if using)
- ECS Task failure count
- S3 storage usage

### Alarms

Set up CloudWatch alarms for:
- High CPU/memory usage (> 80%)
- Task failure rate
- API error rate
- S3 storage approaching limits

---

## 🧪 Testing Deployment

### Health Check

```bash
# Get orchestrator task IP/URL
ORCHESTRATOR_URL="http://your-alb-or-public-ip:8000"

# Health check
curl $ORCHESTRATOR_URL/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "active_sessions": 0
# }
```

### Test Task Execution

```bash
curl -X POST $ORCHESTRATOR_URL/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Use the browser tool to navigate to https://example.com and tell me the page title."
  }'

# Expected response:
# {
#   "session_id": "...",
#   "task": "...",
#   "result": "The page title is: Example Domain",
#   "tool_calls": X,
#   "status": "completed"
# }
```

---

## 💰 Cost Estimation

### ECS Fargate Pricing (us-east-1)

**Orchestrator** (always running):
- 0.5 vCPU, 1 GB memory
- ~$15/month (0.5 vCPU × $0.04048 + 1 GB × $0.004445 × 730 hours)

**Container Tasks** (on-demand):
- 1 vCPU, 2 GB memory per task
- ~$0.05 per hour per task
- Example: 100 tasks/day × 2 min avg = ~$5/month

**Storage:**
- S3: $0.023/GB/month (assuming 10GB screenshots = $0.23/month)
- DynamoDB: Pay-per-request (minimal cost for sessions)

**Total Estimate:** $20-30/month for moderate usage

---

## 🔄 CI/CD Pipeline (Optional)

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Run deployment script
        run: bash infrastructure/deploy.sh
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Container fails to start**
- Check CloudWatch logs: `aws logs tail /ecs/computer-use-agent --follow`
- Verify Xvfb is starting correctly
- Check DISPLAY environment variable is set to `:99`

**2. Browser tool not working**
- Verify Playwright/Chromium installed in container
- Check GPU flags removed from browser_tool.py
- Ensure sufficient memory allocated (2GB+ recommended)

**3. API returns 500 errors**
- Check orchestrator logs for Python exceptions
- Verify ANTHROPIC_API_KEY is set correctly
- Check network connectivity to Anthropic API

**4. Screenshots are blank**
- Verify Xvfb is running: `ps aux | grep Xvfb`
- Check GPU flags removed from Chromium launch args
- Ensure window manager (Fluxbox) is running

**5. High costs**
- Enable task auto-scaling based on demand
- Use FARGATE_SPOT for non-critical workloads
- Set idle task timeout to stop unused containers
- Monitor S3 storage and set lifecycle policies

---

## 📚 Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Playwright Documentation](https://playwright.dev/)
- [Xvfb Documentation](https://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml)

---

## ✅ Post-Deployment Checklist

- [ ] Orchestrator service running and healthy
- [ ] Container tasks can be spawned successfully
- [ ] Browser tool working (verified with test task)
- [ ] Screenshots rendering properly
- [ ] Tool call counting accurate
- [ ] S3 bucket configured for screenshots
- [ ] DynamoDB table created for sessions
- [ ] CloudWatch logs streaming
- [ ] Monitoring alarms configured
- [ ] Cost tracking enabled
- [ ] Documentation updated
- [ ] Team notified of deployment

---

## 🎉 You're Ready to Deploy!

Follow the steps above and your Computer-Use Agent will be running on AWS ECS with full browser automation capabilities.

**Questions or issues?** Check the troubleshooting section or review the logs in CloudWatch.
