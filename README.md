# Claude Computer-Use Agent Trial

A trial/learning implementation of a Claude computer-use agent that executes commands in a containerized environment running on AWS ECS Fargate.

## Overview

This project demonstrates how to build a Claude agent with computer-use capabilities. The agent can:

- **Execute bash commands** in a Linux environment
- **Control a web browser** (navigate, click, type, scroll)
- **Take screenshots** to see what's on screen
- **Read and write files** in a sandboxed workspace

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator API (:8000)                  │
│          FastAPI service managing agent sessions            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Claude Agent                                │
│      Uses Anthropic API with computer-use-2025-01-24        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ Tool Calls
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Execution Container (:8080)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Xvfb (Virtual Display :99)                          │   │
│  │  ├── Fluxbox (Window Manager)                        │   │
│  │  ├── Chromium Browser (via Playwright)               │   │
│  │  └── x11vnc (VNC Server for debugging)               │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Tool Server (FastAPI)                               │   │
│  │  ├── /tools/bash      - Execute shell commands       │   │
│  │  ├── /tools/browser   - Browser automation           │   │
│  │  ├── /tools/file/*    - File operations              │   │
│  │  └── /tools/screenshot - Capture display             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  /workspace                                          │   │
│  │  Sandboxed directory for agent file operations       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Anthropic API key

### 1. Clone and Setup

```bash
cd claude-computer-use-trial

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=your-key-here
```

### 2. Start with Docker Compose

```bash
# Build and start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Test the API

```bash
# Check health
curl http://localhost:8000/health

# Create a session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "test-session"}'

# Run a task (replace SESSION_ID with the returned session_id)
curl -X POST http://localhost:8000/sessions/SESSION_ID/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Take a screenshot and tell me what you see",
    "max_iterations": 10
  }'
```

### 4. View the Virtual Desktop (Optional)

Connect with a VNC viewer to `localhost:5900` to watch the agent in action.

## Project Structure

```
claude-computer-use-trial/
├── agent/                      # Claude Agent code
│   ├── computer_use_agent.py   # Main agent with computer-use tools
│   ├── tool_executor.py        # Executes tool calls in container
│   └── config.py               # Configuration
│
├── container/                  # Execution environment container
│   ├── Dockerfile              # Container image definition
│   ├── server.py               # FastAPI tool server
│   ├── entrypoint.sh           # Startup script
│   └── tools/                  # Tool implementations
│       ├── bash_tool.py        # Shell command execution
│       ├── browser_tool.py     # Playwright browser automation
│       ├── file_tool.py        # File operations
│       └── screenshot_tool.py  # Display capture
│
├── orchestrator/               # API that manages agent + container
│   ├── main.py                 # FastAPI application
│   ├── ecs_manager.py          # ECS task management
│   ├── session_manager.py      # Session tracking
│   └── schemas.py              # Pydantic models
│
├── infrastructure/             # AWS infrastructure
│   ├── task-definition.json    # ECS task definition
│   ├── deploy.sh               # Deployment script
│   └── cloudformation.yml      # Full infrastructure as code
│
├── tests/                      # Test suite
│   ├── test_local.py           # Integration tests
│   └── test_agent.py           # Unit tests
│
├── docker-compose.yml          # Local development setup
└── Dockerfile.orchestrator     # Orchestrator container
```

## API Reference

### Sessions

#### Create Session

```http
POST /sessions
Content-Type: application/json

{
  "name": "optional-session-name"
}
```

#### List Sessions

```http
GET /sessions
```

#### Get Session

```http
GET /sessions/{session_id}
```

#### Delete Session

```http
DELETE /sessions/{session_id}
```

### Tasks

#### Run Task

```http
POST /sessions/{session_id}/run
Content-Type: application/json

{
  "task": "Navigate to example.com and take a screenshot",
  "max_iterations": 20
}
```

#### Reset Conversation

```http
POST /sessions/{session_id}/reset
```

### Health

```http
GET /health
GET /sessions/{session_id}/container-health
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key (required) | - |
| `CLAUDE_MODEL` | Model to use | claude-sonnet-4-20250514 |
| `USE_LOCAL_CONTAINER` | Use local docker container | true |
| `LOCAL_CONTAINER_URL` | Local container URL | http://localhost:8080 |
| `DISPLAY_WIDTH` | Virtual display width | 1920 |
| `DISPLAY_HEIGHT` | Virtual display height | 1080 |
| `MAX_ITERATIONS` | Default max iterations | 20 |

### AWS ECS Variables (for cloud deployment)

| Variable | Description |
|----------|-------------|
| `AWS_REGION` | AWS region |
| `ECS_CLUSTER` | ECS cluster name |
| `ECS_TASK_DEFINITION` | Task definition name |
| `ECS_SUBNETS` | Comma-separated subnet IDs |
| `ECS_SECURITY_GROUPS` | Comma-separated security group IDs |

## AWS Deployment

### Option 1: Using CloudFormation

```bash
# Deploy infrastructure
aws cloudformation create-stack \
  --stack-name computer-use-trial \
  --template-body file://infrastructure/cloudformation.yml \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name computer-use-trial

# Get outputs (contains environment variables to set)
aws cloudformation describe-stacks \
  --stack-name computer-use-trial \
  --query 'Stacks[0].Outputs'
```

### Option 2: Using Deploy Script

```bash
# Make executable
chmod +x infrastructure/deploy.sh

# Run deployment
./infrastructure/deploy.sh
```

### After Deployment

```bash
# Set environment variables (from CloudFormation outputs)
export AWS_REGION=us-east-1
export ECS_CLUSTER=computer-use-trial-cluster
export ECS_TASK_DEFINITION=computer-use-agent
export ECS_SUBNETS=subnet-xxx,subnet-yyy
export ECS_SECURITY_GROUPS=sg-xxx
export USE_LOCAL_CONTAINER=false

# Run orchestrator
cd orchestrator
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Testing

```bash
# Run unit tests
pytest tests/test_agent.py -v

# Run integration tests (requires docker-compose up)
pytest tests/test_local.py -v

# Run all tests
pytest -v
```

## How It Works

### Agent Loop

1. User submits a task via the API
2. The orchestrator creates a session and spawns a container
3. The Claude agent receives the task and plans actions
4. For each action:
   - Claude generates a tool call (bash, browser, screenshot, etc.)
   - The tool executor sends the request to the container
   - The container executes the action and returns the result
   - Claude sees the result and plans the next action
5. The loop continues until Claude completes the task or hits max iterations

### Computer-Use Tools

The agent has access to these tools:

- **computer** (built-in): Screenshot, mouse clicks, keyboard input
- **bash** (built-in): Shell command execution
- **str_replace_editor** (built-in): File viewing and editing
- **browser** (custom): High-level browser control

### Security

- File operations are restricted to `/workspace` directory
- Commands run in an isolated container
- Sessions have configurable timeouts
- Each session gets its own container (when using ECS)

## Troubleshooting

### Container won't start

```bash
# Check Docker status
docker info

# Check container logs
docker-compose logs computer
```

### Agent errors

```bash
# Check orchestrator logs
docker-compose logs orchestrator

# Verify API key
echo $ANTHROPIC_API_KEY
```

### Can't connect to VNC

```bash
# Verify port is exposed
docker-compose ps

# Check VNC server inside container
docker-compose exec computer ps aux | grep x11vnc
```

## Limitations

This is a **trial/learning implementation**. For production use, consider:

- Adding authentication and authorization
- Implementing rate limiting
- Using persistent storage for sessions
- Adding monitoring and alerting
- Implementing proper error recovery
- Adding cost controls for API usage

## License

This project is for educational purposes.

## Acknowledgments

- [Anthropic Claude](https://anthropic.com) - Computer-use capabilities
- [Playwright](https://playwright.dev) - Browser automation
- [FastAPI](https://fastapi.tiangolo.com) - API framework
