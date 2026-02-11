# ECS Deployment with Docker Computer Use Container

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS ECS CLUSTER                               │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  ECS TASK (Fargate)                                       │  │
│  │                                                           │  │
│  │  ┌─────────────────────┐    ┌─────────────────────────┐  │  │
│  │  │ Container 1:        │    │ Container 2:            │  │  │
│  │  │ YOUR API            │◄───┤ COMPUTER USE            │  │  │
│  │  │                     │    │                         │  │  │
│  │  │ - api_server.py     │    │ - X11 virtual display   │  │  │
│  │  │ - agent_runner.py   │    │ - VNC server            │  │  │
│  │  │ - tool handlers     │    │ - Chromium browser      │  │  │
│  │  │                     │    │ - REST API (:8080)      │  │  │
│  │  │ Port: 8003          │    │ Ports: 8080, 5900       │  │  │
│  │  └─────────────────────┘    └─────────────────────────┘  │  │
│  │         │                              ▲                  │  │
│  │         └──────────────────────────────┘                  │  │
│  │           HTTP: http://localhost:8080                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Application Load Balancer                                │  │
│  │  - Target: API Container (port 8003)                      │  │
│  │  - Health Check: /health                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
                   Internet Gateway
                          │
                          ▼
                    Users/Clients
```

---

## Deployment Strategy: Option A vs Option B

### **Option A: Single Task with Two Containers (Recommended)**

**Pros**:
- ✅ Localhost communication (fast, no network overhead)
- ✅ Simplified networking (no service discovery)
- ✅ Automatic lifecycle management (both start/stop together)
- ✅ Lower cost (single task)

**Cons**:
- ❌ Both containers share same CPU/memory allocation
- ❌ If computer-use crashes, whole task restarts

### **Option B: Two Separate ECS Services**

**Pros**:
- ✅ Independent scaling (scale API separately from computer-use)
- ✅ Independent health checks
- ✅ If one fails, other continues running

**Cons**:
- ❌ Requires service discovery (Cloud Map or internal ALB)
- ❌ Network latency between services
- ❌ Higher cost (two tasks running)

**Recommendation**: Start with **Option A** (simpler), move to **Option B** if you need independent scaling.

---

## Option A: ECS Task Definition (Two Containers)

### File: `ecs-task-definition.json`

```json
{
  "family": "dynamic-agent-marketplace",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "api-server",
      "image": "ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/dynamic-agent-api:latest",
      "cpu": 1024,
      "memory": 2048,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8003,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "AWS_REGION", "value": "us-west-2"},
        {"name": "COMPUTER_USE_CONTAINER_URL", "value": "http://localhost:8080"},
        {"name": "S3_BUCKET", "value": "cerebricks-studio-agent-skills"}
      ],
      "secrets": [
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:anthropic-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/dynamic-agent-marketplace",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "api"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8003/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "dependsOn": [
        {
          "containerName": "computer-use",
          "condition": "HEALTHY"
        }
      ]
    },
    {
      "name": "computer-use",
      "image": "ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/computer-use-server:latest",
      "cpu": 1024,
      "memory": 2048,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        },
        {
          "containerPort": 5900,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DISPLAY", "value": ":99"},
        {"name": "DISPLAY_WIDTH", "value": "1920"},
        {"name": "DISPLAY_HEIGHT", "value": "1080"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/dynamic-agent-marketplace",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "computer-use"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

---

## Docker Compose for Local Testing

Before deploying to ECS, test locally with Docker Compose:

### File: `docker-compose.yml`

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8003:8003"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - COMPUTER_USE_CONTAINER_URL=http://computer-use:8080
      - AWS_REGION=us-west-2
      - S3_BUCKET=cerebricks-studio-agent-skills
    volumes:
      - ./.claude:/app/.claude
    depends_on:
      computer-use:
        condition: service_healthy
    networks:
      - agent-network

  computer-use:
    build:
      context: .
      dockerfile: Dockerfile.computer-use
    ports:
      - "8080:8080"
      - "5900:5900"
    environment:
      - DISPLAY=:99
      - DISPLAY_WIDTH=1920
      - DISPLAY_HEIGHT=1080
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 60s
    networks:
      - agent-network

networks:
  agent-network:
    driver: bridge
```

### File: `Dockerfile.api`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8003/health || exit 1

# Run application
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8003"]
```

### File: `Dockerfile.computer-use`

```dockerfile
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    xvfb \
    x11vnc \
    fluxbox \
    chromium-browser \
    scrot \
    xdotool \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install fastapi uvicorn pillow pyautogui mss

# Create app directory
WORKDIR /app

# Copy server code
COPY computer_use_server.py .

# Expose ports
EXPOSE 8080 5900

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start X server and API
CMD Xvfb :99 -screen 0 1920x1080x24 & \
    x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -xkb & \
    DISPLAY=:99 fluxbox & \
    DISPLAY=:99 uvicorn computer_use_server:app --host 0.0.0.0 --port 8080
```

---

## Deployment Steps

### Step 1: Test Locally with Docker Compose

```bash
# Build and run
docker-compose up --build

# Test in another terminal
curl http://localhost:8003/health
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Take a screenshot and tell me the resolution",
    "max_turns": 5,
    "use_computer_tools": true
  }'

# Check logs
docker-compose logs -f api
docker-compose logs -f computer-use

# Stop
docker-compose down
```

### Step 2: Build and Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

# Create repositories
aws ecr create-repository --repository-name dynamic-agent-api
aws ecr create-repository --repository-name computer-use-server

# Build images
docker build -f Dockerfile.api -t dynamic-agent-api:latest .
docker build -f Dockerfile.computer-use -t computer-use-server:latest .

# Tag images
docker tag dynamic-agent-api:latest ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/dynamic-agent-api:latest
docker tag computer-use-server:latest ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/computer-use-server:latest

# Push images
docker push ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/dynamic-agent-api:latest
docker push ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/computer-use-server:latest
```

### Step 3: Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name dynamic-agent-cluster --region us-west-2
```

### Step 4: Create CloudWatch Log Group

```bash
aws logs create-log-group \
  --log-group-name /ecs/dynamic-agent-marketplace \
  --region us-west-2
```

### Step 5: Store Secrets

```bash
aws secretsmanager create-secret \
  --name anthropic-api-key \
  --secret-string "sk-ant-api03-..." \
  --region us-west-2
```

### Step 6: Register Task Definition

```bash
# Update ecs-task-definition.json with your ACCOUNT_ID

aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json \
  --region us-west-2
```

### Step 7: Create ALB and Target Group

```bash
# Create target group
aws elbv2 create-target-group \
  --name dynamic-agent-tg \
  --protocol HTTP \
  --port 8003 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30

# Create ALB (omitted for brevity - use AWS Console or full CLI)
```

### Step 8: Create ECS Service

```bash
aws ecs create-service \
  --cluster dynamic-agent-cluster \
  --service-name dynamic-agent-service \
  --task-definition dynamic-agent-marketplace:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=api-server,containerPort=8003" \
  --region us-west-2
```

### Step 9: Verify Deployment

```bash
# Check service status
aws ecs describe-services \
  --cluster dynamic-agent-cluster \
  --services dynamic-agent-service

# Check tasks
aws ecs list-tasks --cluster dynamic-agent-cluster

# Test via ALB
curl http://your-alb-url.us-west-2.elb.amazonaws.com/health

# Test computer use
curl -X POST http://your-alb-url.us-west-2.elb.amazonaws.com/execute \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Take a screenshot",
    "use_computer_tools": true
  }'
```

---

## Monitoring

### CloudWatch Logs

```bash
# API logs
aws logs tail /ecs/dynamic-agent-marketplace --follow --filter-pattern "api"

# Computer-use logs
aws logs tail /ecs/dynamic-agent-marketplace --follow --filter-pattern "computer-use"
```

### CloudWatch Metrics

Monitor:
- CPU utilization
- Memory utilization
- Request count
- Error rate
- Task health

---

## Cost Estimate (Monthly)

| Resource | Configuration | Cost |
|----------|---------------|------|
| ECS Fargate (2 tasks) | 2 vCPU, 4GB RAM | ~$80-100 |
| Application Load Balancer | Standard ALB | ~$20 |
| ECR Storage | 2 images, ~2GB | ~$1 |
| CloudWatch Logs | 10GB/month | ~$5 |
| Anthropic API | Pay-per-use | Variable |
| **Total** | | **~$106-126/month** |

---

## Next Steps

1. ✅ Test locally with `docker-compose up`
2. ✅ Build and push images to ECR
3. ✅ Deploy to ECS
4. ✅ Configure ALB
5. ✅ Test production endpoint
6. ✅ Monitor and optimize

Ready to proceed? Let me know if you want me to create the actual Docker files!
