# Docker Quick Start Guide

## Files Created ✅

- ✅ `Dockerfile.api` - API container image
- ✅ `Dockerfile.computer-use` - Computer use container image
- ✅ `computer_use_server.py` - FastAPI server for computer control
- ✅ `docker-entrypoint.sh` - Startup script for computer-use container
- ✅ `docker-compose.yml` - Local testing orchestration
- ✅ `.dockerignore` - Build optimization

---

## Quick Start (5 minutes)

### Step 1: Build and Run

```bash
# Navigate to the directory
cd C:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase

# Build and start both containers
docker-compose up --build
```

**Expected output**:
```
[+] Building computer-use ...
[+] Building api ...
computer-use    | Starting Xvfb on display :99...
computer-use    | Starting x11vnc on port 5900...
computer-use    | Starting fluxbox window manager...
computer-use    | Starting computer use API server on port 8080...
computer-use    | INFO:     Uvicorn running on http://0.0.0.0:8080
api             | INFO:     Uvicorn running on http://0.0.0.0:8003
```

### Step 2: Verify Health

Open a new terminal:

```bash
# Check API health
curl http://localhost:8003/health

# Expected: {"status":"healthy","agent_initialized":true}

# Check computer-use health
curl http://localhost:8080/health

# Expected: {"status":"healthy","display":":99","service":"computer-use"}
```

### Step 3: Test Screenshot via API

```bash
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Take a screenshot and tell me the resolution",
    "max_turns": 5,
    "use_computer_tools": true
  }'
```

**Expected**:
- API calls computer-use container
- Screenshot taken from virtual display (1920x1080)
- Claude describes the resolution

### Step 4: View Logs

```bash
# View API logs
docker logs -f dynamic-agent-api

# View computer-use logs
docker logs -f computer-use
```

### Step 5: Stop

```bash
# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## VNC Access (Optional)

To see the virtual desktop:

1. Install VNC viewer (TigerVNC, RealVNC, etc.)
2. Connect to: `localhost:5900`
3. No password required
4. You'll see the virtual desktop with fluxbox window manager

---

## Architecture

```
┌────────────────────────────────────────┐
│  docker-compose up                     │
│                                        │
│  ┌──────────────┐  ┌────────────────┐ │
│  │ api          │  │ computer-use   │ │
│  │ (Port 8003)  │◄─┤ (Port 8080)    │ │
│  │              │  │                │ │
│  │ - agent      │  │ - Xvfb :99     │ │
│  │ - tools      │  │ - VNC :5900    │ │
│  │ - routing    │  │ - pyautogui    │ │
│  └──────────────┘  └────────────────┘ │
│         │               │              │
│         └───────────────┘              │
│       http://computer-use:8080         │
└────────────────────────────────────────┘
```

---

## Troubleshooting

### Issue: "Cannot connect to Docker daemon"

**Solution**:
```bash
# Start Docker Desktop
# Wait for it to be running
docker ps
```

### Issue: "Port 8003 already in use"

**Solution**:
```bash
# Stop the running API server
# Find process on port 8003
netstat -ano | findstr :8003

# Kill the process
taskkill /PID <PID> /F

# Then retry docker-compose up
```

### Issue: "Build failed - Dockerfile not found"

**Solution**:
```bash
# Make sure you're in the correct directory
cd C:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase

# Verify files exist
dir Dockerfile.*
```

### Issue: "Container exits immediately"

**Solution**:
```bash
# Check logs
docker logs computer-use
docker logs dynamic-agent-api

# Common fixes:
# 1. Make sure .env file has ANTHROPIC_API_KEY
# 2. Check docker-entrypoint.sh has LF line endings (not CRLF)
```

---

## Testing Checklist

After `docker-compose up`, test these:

- [ ] Health check passes: `curl http://localhost:8003/health`
- [ ] Computer-use responds: `curl http://localhost:8080/health`
- [ ] Screenshot works: Test via `/execute` endpoint
- [ ] Bash works: "List Python files" test
- [ ] Text editor works: "Create test file" test
- [ ] MCP works: "Show Electronics products" test

---

## Next Steps

Once local Docker testing passes:

1. ✅ **Push to ECR** (see ECS_DEPLOYMENT.md)
2. ✅ **Deploy to ECS** (see ECS_DEPLOYMENT.md)
3. ✅ **Configure ALB**
4. ✅ **Production testing**

---

## Files Reference

| File | Purpose |
|------|---------|
| `Dockerfile.api` | Builds API container (Python 3.11, your code) |
| `Dockerfile.computer-use` | Builds computer-use container (Ubuntu + X11) |
| `computer_use_server.py` | FastAPI server for computer control |
| `docker-entrypoint.sh` | Startup script (Xvfb, VNC, API) |
| `docker-compose.yml` | Local testing orchestration |
| `.dockerignore` | Excludes unnecessary files from build |

---

## Resource Usage

| Container | CPU | Memory | Notes |
|-----------|-----|--------|-------|
| api | 1 vCPU | 2 GB | Main API server |
| computer-use | 1 vCPU | 2 GB | Virtual display + browser |
| **Total** | **2 vCPU** | **4 GB** | Both containers running |

---

Ready to test! Run: `docker-compose up --build`
