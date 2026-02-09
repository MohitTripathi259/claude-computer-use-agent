# Local Testing Guide - Computer-Use Agent

Complete step-by-step guide for testing the Claude Computer-Use Agent locally with **maximum visibility** into every process.

---

## Prerequisites

Before you start, ensure you have:

- ✅ **Docker Desktop** installed and running
- ✅ **Postman** (or any REST client)
- ✅ **Anthropic API Key** with Claude Sonnet 4 access
- ✅ **Git Bash** or PowerShell (for command-line testing)

---

## Step 1: Environment Setup

### 1.1 Create `.env` File

Navigate to the project folder and create `.env`:

```bash
cd c:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase
```

Create the `.env` file with your API key:

```bash
# Create .env file (Windows PowerShell)
@"
ANTHROPIC_API_KEY=your-actual-api-key-here
"@ | Out-File -FilePath .env -Encoding UTF8

# Or using Git Bash
echo "ANTHROPIC_API_KEY=your-actual-api-key-here" > .env
```

**Expected result**: File `.env` created in the project root

### 1.2 Verify `.env` Contents

```bash
# View the file
cat .env

# Expected output:
# ANTHROPIC_API_KEY=sk-ant-...your-key...
```

**⚠️ IMPORTANT**: Replace `your-actual-api-key-here` with your real Anthropic API key

---

## Step 2: Start the Containers

### 2.1 Build and Start Services

```bash
# Build images (first time or after code changes)
docker-compose build

# Start services in detached mode
docker-compose up -d
```

**Expected output**:
```
[+] Building 45.2s (18/18) FINISHED
[+] Running 3/3
 ✔ Network computer-use-network  Created
 ✔ Container computer-use-container      Started
 ✔ Container computer-use-orchestrator   Started
```

**What's happening**:
- Docker builds two images: `computer` (execution environment) and `orchestrator` (API server)
- Creates network `computer-use-network`
- Starts container with virtual desktop (Xvfb + Chromium + tools)
- Starts orchestrator API server on port 8000
- Container exposes port 8080 (tools) and 5900 (VNC)

### 2.2 Monitor Startup Logs

Open **3 separate terminal windows** to monitor logs:

**Terminal 1 - Computer Container Logs**:
```bash
docker-compose logs -f computer
```

**Terminal 2 - Orchestrator Logs**:
```bash
docker-compose logs -f orchestrator
```

**Terminal 3 - Combined Logs**:
```bash
docker-compose logs -f
```

**What to look for** (Terminal 1 - Computer Container):
```
computer  | ======================================================================
computer  |   CONTAINER STARTING
computer  | ======================================================================
computer  |   [init] Starting Xvfb on :99...
computer  |   [init] Starting Fluxbox window manager...
computer  |   [init] Launching Chromium browser...
computer  |   [init] Starting x11vnc server on :5900...
computer  |   [init] Starting FastAPI tool server...
computer  | INFO:     Uvicorn running on http://0.0.0.0:8080
computer  | ======================================================================
computer  |   CONTAINER READY
computer  | ======================================================================
```

**What to look for** (Terminal 2 - Orchestrator):
```
orchestrator  | ======================================================================
orchestrator  |   ORCHESTRATOR — LOADING MODULES
orchestrator  | ======================================================================
orchestrator  |   [init] Creating SessionManager...
orchestrator  |   [init] SessionManager created
orchestrator  |   [init] Creating ECSManager...
orchestrator  |   [init] ECSManager created (mode=local)
orchestrator  |   [init] HTTP client created
orchestrator  | INFO:     Started server process [1]
orchestrator  | INFO:     Waiting for application startup.
orchestrator  | ======================================================================
orchestrator  |   ORCHESTRATOR — STARTUP COMPLETE
orchestrator  | ======================================================================
orchestrator  | INFO:     Application startup complete.
orchestrator  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Expected timing**: Container starts in 15-45 seconds

---

## Step 3: Health Check

### 3.1 Check Container Status

```bash
docker-compose ps
```

**Expected output**:
```
NAME                       STATUS          PORTS
computer-use-container     Up 2 minutes    0.0.0.0:5900->5900/tcp, 0.0.0.0:8080->8080/tcp
computer-use-orchestrator  Up 2 minutes    0.0.0.0:8000->8000/tcp
```

Both containers should show `Up` status.

### 3.2 Test Container Health Endpoint

```bash
curl http://localhost:8080/health
```

**Expected response**:
```json
{"status":"healthy"}
```

### 3.3 Test Orchestrator Health Endpoint

```bash
curl http://localhost:8000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "sessions_active": 0
}
```

### 3.4 Test Orchestrator Root Endpoint

```bash
curl http://localhost:8000/
```

**Expected response**:
```json
{
  "name": "Computer-Use Agent Orchestrator",
  "version": "2.0.0",
  "agent_type": "Anthropic Computer-Use API",
  "docs": "/docs",
  "health": "/health"
}
```

**If any health check fails**:
- Wait 30 more seconds (startup takes time)
- Check logs: `docker-compose logs computer` or `docker-compose logs orchestrator`
- Common issue: Anthropic API key not set correctly in `.env`

---

## Step 4: Test with Postman (Step-by-Step)

### 4.1 Create a Session

**Postman Setup**:
- Method: `POST`
- URL: `http://localhost:8000/sessions`
- Headers:
  - `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "name": "hacker-news-test"
}
```

**Click "Send"**

**Expected Response** (status 200):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "hacker-news-test",
  "container_url": "http://computer:8080",
  "status": "running",
  "created_at": "2025-02-06T12:34:56.789Z"
}
```

**What happens in the logs** (Terminal 2):
```
orchestrator  | ============================================================
orchestrator  |   POST /sessions  — Creating new session
orchestrator  | ============================================================
orchestrator  |   Session name: hacker-news-test
orchestrator  |   Timestamp: 2025-02-06T12:34:56.789012
orchestrator  |   [step 1/4] Creating session record in SessionManager...
orchestrator  |   [step 1/4] Session ID: 550e8400-e29b-41d4-a716-446655440000
orchestrator  |   [step 2/4] Spawning container via ECSManager...
orchestrator  |   [step 2/4] Container URL: http://computer:8080
orchestrator  |   [step 2/4] Task ARN: None (local mode)
orchestrator  |   [step 3/4] Updating session with container info...
orchestrator  |   [step 3/4] Session updated: status=running
orchestrator  |   [step 4/4] Creating agent instance...
orchestrator  |
orchestrator  | ======================================================================
orchestrator  |   COMPUTER USE AGENT — INITIALIZING
orchestrator  | ======================================================================
orchestrator  |   [OK] API key loaded (ends with ...abc123)
orchestrator  |   [OK] Container URL: http://computer:8080
orchestrator  |   [OK] Model: claude-sonnet-4-20250514
orchestrator  |   [OK] Anthropic async client created
orchestrator  |   [OK] HTTP client created (timeout=180s, connect=10s)
orchestrator  |   [OK] Tools registered: ['computer', 'bash', 'str_replace_based_edit_tool']
orchestrator  |   [OK] Display: 1920x1080
orchestrator  |   [OK] Max turns: 50
orchestrator  | ======================================================================
orchestrator  |   AGENT READY
orchestrator  | ======================================================================
orchestrator  |
orchestrator  |   [step 4/4] Agent instance created and stored
orchestrator  |
orchestrator  |   SESSION CREATED SUCCESSFULLY
orchestrator  |   Session ID: 550e8400-e29b-41d4-a716-446655440000
orchestrator  |   Container URL: http://computer:8080
orchestrator  |   Status: running
orchestrator  | ============================================================
```

**⚠️ SAVE THE SESSION_ID**: You'll need it for the next request. Example: `550e8400-e29b-41d4-a716-446655440000`

---

### 4.2 Run the Hacker News Task

**Postman Setup**:
- Method: `POST`
- URL: `http://localhost:8000/sessions/{SESSION_ID}/run`
  - Replace `{SESSION_ID}` with the ID from step 4.1
  - Example: `http://localhost:8000/sessions/550e8400-e29b-41d4-a716-446655440000/run`
- Headers:
  - `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "task": "I need you to complete a multi-step research and documentation task: 1) First, open the browser and navigate to news.ycombinator.com (Hacker News) and take a screenshot of the current front page, 2) Then use bash to check the current date, time, and system information (uname -a), 3) Next, create a file at /workspace/hacker_news_report.txt that includes: today's date, the system info, and a brief description of what you see on the Hacker News screenshot (top 3 story titles if visible), 4) Finally, read back the file you created to verify the contents are correct. Make sure to take screenshots at key steps so I can see what's happening."
}
```

**Click "Send"**

**⏱️ This will take 1-3 minutes**. Watch the Terminal 2 logs to see real-time progress!

---

### 4.3 Watch the Logs (Terminal 2)

You'll see **extensive logging** showing every step:

**Initial Request**:
```
orchestrator  | ############################################################
orchestrator  |   POST /sessions/550e8400-e29b-41d4-a716-446655440000/run
orchestrator  | ############################################################
orchestrator  |   Task: I need you to complete a multi-step research and documentation task: 1) First, open the browser...
orchestrator  |   Timestamp: 2025-02-06T12:35:10.123456
orchestrator  |   [OK] Session found: status=SessionStatus.RUNNING
orchestrator  |   [OK] Agent found for session
orchestrator  |   [OK] Container URL: http://computer:8080
orchestrator  |
orchestrator  |   >>> HANDING OFF TO AGENT (this may take a while)... <<<
```

**Agent Starts**:
```
orchestrator  |
orchestrator  | ######################################################################
orchestrator  |   NEW TASK  [AGENT-A1B2C3D4]
orchestrator  | ######################################################################
orchestrator  |   Task: I need you to complete a multi-step research and documentation task...
orchestrator  |   Model: claude-sonnet-4-20250514
orchestrator  |   Container: http://computer:8080
orchestrator  |   Timestamp: 2025-02-06 12:35:10
orchestrator  | ######################################################################
```

**Turn 1 - First API Call**:
```
orchestrator  | ────────────────────────────────────────────────────────────
orchestrator  |   TURN 1/50  [AGENT-A1B2C3D4]
orchestrator  | ────────────────────────────────────────────────────────────
orchestrator  |   Messages in conversation: 1
orchestrator  |   Total tool calls so far: 0
orchestrator  |   Elapsed: 0.0s
orchestrator  |
orchestrator  |   >> Calling Anthropic API (claude-sonnet-4-20250514)...
orchestrator  |      Beta flags: ['computer-use-2025-01-24']
orchestrator  |      Tools: ['computer', 'bash', 'str_replace_based_edit_tool']
orchestrator  |      Max tokens: 4096
orchestrator  |   << API responded in 3.2s
orchestrator  |      Stop reason: tool_use
orchestrator  |      Content blocks: 2
orchestrator  |      Usage: input=1245 output=234 tokens
orchestrator  |      Block 1: type=text
orchestrator  |        Text: I'll help you complete this multi-step task. Let me start by taking a screenshot...
orchestrator  |      Block 2: type=tool_use
orchestrator  |        Tool: computer
orchestrator  |        Input keys: ['action']
```

**Tool Execution**:
```
orchestrator  |   >> Executing tool calls...
orchestrator  |
orchestrator  |     ┌─ Tool Call #1  [toolu_01AbC...]
orchestrator  |     │  Tool: computer
orchestrator  |     │  Input: {"action": "screenshot"}...
orchestrator  |
orchestrator  |       → _execute_tool(tool=computer)
orchestrator  |         ├─ _exec_computer
orchestrator  |         │  Action: screenshot
orchestrator  |         │  Params: {"action": "screenshot"}
orchestrator  |         │  Endpoint: http://computer:8080/tools/screenshot
orchestrator  |         │  HTTP: 0.45s
orchestrator  |         │  Image: 1920x1080, base64 length=123456
orchestrator  |         └─ Returning image block
orchestrator  |     │  Result: [image] 1 block(s)
orchestrator  |     │         base64 data length: 123456 chars
orchestrator  |     │  Elapsed: 0.47s
orchestrator  |     └─ [OK]
```

**Turn 2 - Navigate to Hacker News**:
```
orchestrator  | ────────────────────────────────────────────────────────────
orchestrator  |   TURN 2/50  [AGENT-A1B2C3D4]
orchestrator  | ────────────────────────────────────────────────────────────
orchestrator  |
orchestrator  |   >> Calling Anthropic API...
orchestrator  |   << API responded in 2.8s
orchestrator  |      Stop reason: tool_use
orchestrator  |      Block 1: type=text
orchestrator  |        Text: Now I'll navigate to Hacker News...
orchestrator  |      Block 2: type=tool_use
orchestrator  |        Tool: computer
orchestrator  |        Input keys: ['action', 'coordinate']
orchestrator  |
orchestrator  |   >> Executing tool calls...
orchestrator  |     ┌─ Tool Call #2  [toolu_02XyZ...]
orchestrator  |     │  Tool: computer
orchestrator  |     │  Input: {"action": "left_click", "coordinate": [960, 60]}...
orchestrator  |       → _execute_tool(tool=computer)
orchestrator  |         ├─ _exec_computer
orchestrator  |         │  Action: left_click
orchestrator  |         │  Params: {"action": "left_click", "coordinate": [960, 60]}
orchestrator  |         │  Endpoint: http://computer:8080/tools/browser
orchestrator  |         │  HTTP: 0.12s
orchestrator  |         └─ Clicked at (960, 60)
orchestrator  |     │  Result: Clicked at (960, 60)
orchestrator  |     │  Elapsed: 0.13s
orchestrator  |     └─ [OK]
```

**Turn 3 - Type URL**:
```
orchestrator  |     ┌─ Tool Call #3  [toolu_03AbC...]
orchestrator  |     │  Tool: computer
orchestrator  |     │  Input: {"action": "type", "text": "news.ycombinator.com"}...
orchestrator  |       → _execute_tool(tool=computer)
orchestrator  |         ├─ _exec_computer
orchestrator  |         │  Action: type
orchestrator  |         │  Params: {"action": "type", "text": "news.ycombinator.com"}
orchestrator  |         │  Endpoint: http://computer:8080/tools/browser
orchestrator  |         │  HTTP: 0.23s
orchestrator  |         └─ Typed: news.ycombinator.com
orchestrator  |     │  Result: Typed: news.ycombinator.com
orchestrator  |     │  Elapsed: 0.24s
orchestrator  |     └─ [OK]
```

**Bash Command**:
```
orchestrator  |     ┌─ Tool Call #8  [toolu_08XyZ...]
orchestrator  |     │  Tool: bash
orchestrator  |     │  Input: {"command": "date && uname -a"}...
orchestrator  |       → _execute_tool(tool=bash)
orchestrator  |         ├─ _exec_bash
orchestrator  |         │  Command: date && uname -a
orchestrator  |         │  Container: http://computer:8080/tools/bash
orchestrator  |         │  HTTP: 0.08s
orchestrator  |         │  Exit code: 0
orchestrator  |         │  STDOUT length: 156 chars
orchestrator  |         │  STDERR length: 0 chars
orchestrator  |         └─ Result: 189 chars
orchestrator  |     │  Result: Command succeeded STDOUT: Thu Feb  6 12:35:45 UTC 2025 Linux 43a21f...
orchestrator  |     │  Elapsed: 0.09s
orchestrator  |     └─ [OK]
```

**File Creation**:
```
orchestrator  |     ┌─ Tool Call #10  [toolu_10AbC...]
orchestrator  |     │  Tool: str_replace_based_edit_tool
orchestrator  |     │  Input: {"command": "create", "path": "/workspace/hacker_news_report.txt", "file_text": "..."}...
orchestrator  |       → _execute_tool(tool=str_replace_based_edit_tool)
orchestrator  |         ├─ _exec_editor
orchestrator  |         │  Command: create
orchestrator  |         │  Path: /workspace/hacker_news_report.txt
orchestrator  |         │  Content length: 345 chars
orchestrator  |         │  Endpoint: http://computer:8080/tools/file/write
orchestrator  |         │  HTTP: 0.05s
orchestrator  |         └─ File created
orchestrator  |     │  Result: Created file: /workspace/hacker_news_report.txt
orchestrator  |     │  Elapsed: 0.06s
orchestrator  |     └─ [OK]
```

**Task Complete**:
```
orchestrator  |   [DONE] Agent finished (stop_reason=end_turn)
orchestrator  |
orchestrator  | ======================================================================
orchestrator  |   TASK COMPLETE  [AGENT-A1B2C3D4]
orchestrator  | ======================================================================
orchestrator  |   Total turns: 12
orchestrator  |   Total tool calls: 15
orchestrator  |   Total time: 87.3s
orchestrator  |   Final response length: 1234 chars
orchestrator  | ======================================================================
orchestrator  |
orchestrator  |   >>> AGENT RETURNED <<<
orchestrator  |   Task execution time: 87.3s
orchestrator  |   Result length: 1234 chars
orchestrator  |   Result preview: I've completed all the steps you requested. Here's what I did: 1. Navigated to news.ycombinator.com...
orchestrator  |   [OK] Session task count incremented
orchestrator  |   [S3] Uploading screenshots...
orchestrator  |   [S3] Uploaded 4 screenshots
orchestrator  |
orchestrator  |   TASK COMPLETED SUCCESSFULLY
orchestrator  |   Session: 550e8400-e29b-41d4-a716-446655440000
orchestrator  |   Tool calls: ~7
orchestrator  |   Status: completed
orchestrator  | ############################################################
```

---

### 4.4 Expected Postman Response

After 1-3 minutes, you'll receive:

**Status**: 200 OK

**Response Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": "I've completed all the steps you requested. Here's what I did:\n\n1. Navigated to news.ycombinator.com and took a screenshot of the front page\n2. Checked the system information:\n   - Date: Thu Feb  6 12:35:45 UTC 2025\n   - System: Linux 5.15.0-1052-aws x86_64 GNU/Linux\n3. Created /workspace/hacker_news_report.txt with:\n   - Today's date and time\n   - System information\n   - Description of the top 3 Hacker News stories:\n     * \"Show HN: New AI coding assistant\"\n     * \"Startup raises $50M Series A\"\n     * \"How we scaled to 1M users\"\n4. Read back the file to verify - contents match what was written\n\nAll tasks completed successfully. The report file is ready at /workspace/hacker_news_report.txt",
  "task_count": 1,
  "screenshots": [
    "https://your-s3-bucket.s3.us-west-2.amazonaws.com/sessions/550e8400-e29b-41d4-a716-446655440000/screenshot_001.png",
    "https://your-s3-bucket.s3.us-west-2.amazonaws.com/sessions/550e8400-e29b-41d4-a716-446655440000/screenshot_002.png",
    "https://your-s3-bucket.s3.us-west-2.amazonaws.com/sessions/550e8400-e29b-41d4-a716-446655440000/screenshot_003.png",
    "https://your-s3-bucket.s3.us-west-2.amazonaws.com/sessions/550e8400-e29b-41d4-a716-446655440000/screenshot_004.png"
  ]
}
```

---

## Step 5: Alternative Testing with curl

If you prefer command-line testing:

### 5.1 Create Session

```bash
# Store session ID in variable (PowerShell)
$response = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/sessions" -Body '{"name":"test"}' -ContentType "application/json"
$sessionId = $response.session_id
Write-Host "Session ID: $sessionId"

# Or using Git Bash
SESSION_ID=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}' | jq -r '.session_id')
echo "Session ID: $SESSION_ID"
```

### 5.2 Run Task

```bash
# PowerShell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/sessions/$sessionId/run" `
  -Body '{"task":"Take a screenshot and tell me what you see"}' `
  -ContentType "application/json"

# Git Bash
curl -X POST "http://localhost:8000/sessions/$SESSION_ID/run" \
  -H "Content-Type: application/json" \
  -d '{"task":"Take a screenshot and tell me what you see"}'
```

---

## Step 6: View the Virtual Desktop (Optional)

You can watch the agent in action using a VNC viewer.

### 6.1 Install VNC Viewer

Download TigerVNC or RealVNC Viewer:
- TigerVNC: https://tigervnc.org/
- RealVNC: https://www.realvnc.com/en/connect/download/viewer/

### 6.2 Connect to VNC

- Open VNC Viewer
- Server: `localhost:5900`
- Password: (none - no password required)

You'll see the Linux desktop with Chromium browser in action!

---

## Step 7: Verify File Creation

### 7.1 Check the Report File

```bash
# Enter the container
docker exec -it computer-use-container /bin/bash

# Inside the container - view the file
cat /workspace/hacker_news_report.txt

# Expected output:
# Date: Thu Feb  6 12:35:45 UTC 2025
# System: Linux 5.15.0-1052-aws x86_64 GNU/Linux
#
# Hacker News Top Stories:
# 1. Show HN: New AI coding assistant
# 2. Startup raises $50M Series A
# 3. How we scaled to 1M users
#
# Screenshot shows the front page of Hacker News with the standard orange header...

# Exit container
exit
```

---

## Step 8: Cleanup

### 8.1 Delete Session

```bash
# Postman: DELETE http://localhost:8000/sessions/{SESSION_ID}
# Or curl:
curl -X DELETE "http://localhost:8000/sessions/$SESSION_ID"
```

**Expected response**:
```json
{
  "message": "Session deleted",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 8.2 Stop Containers

```bash
docker-compose down

# To also remove volumes (⚠️ deletes workspace data):
docker-compose down -v
```

---

## Troubleshooting

### Container Won't Start

**Symptom**: `docker-compose ps` shows `Exited` or `Restarting`

**Solution**:
```bash
# Check logs
docker-compose logs computer

# Common issues:
# 1. Port 8080 or 5900 already in use
#    → Stop conflicting service or change ports in docker-compose.yml

# 2. Insufficient memory
#    → Increase Docker Desktop memory limit (Settings → Resources)

# 3. Xvfb fails to start
#    → Restart Docker Desktop
```

### API Key Error

**Symptom**: Logs show `ANTHROPIC_API_KEY is missing!` or `401 Unauthorized`

**Solution**:
```bash
# Verify .env file exists
cat .env

# Verify it contains your key
# If missing or wrong, update it:
echo "ANTHROPIC_API_KEY=sk-ant-your-actual-key" > .env

# Restart orchestrator
docker-compose restart orchestrator

# Watch logs
docker-compose logs -f orchestrator
```

### Task Times Out

**Symptom**: Postman shows "no response" or times out after 60 seconds

**Solution**:
- Increase Postman timeout: Settings → General → Request timeout → 300000ms
- Or use curl (no timeout by default)
- The task may still be running - check Terminal 2 logs

### Container Network Error

**Symptom**: Logs show `Connection refused` or `Name or service not known`

**Solution**:
```bash
# Verify both containers are on same network
docker network inspect computer-use-network

# Should show both containers

# If not, recreate network:
docker-compose down
docker-compose up -d
```

### No Screenshots in Response

**Symptom**: `screenshots` array is empty in response

**Reason**: S3 upload is configured but AWS credentials are missing (expected in local mode)

**Solution**: Screenshots are saved locally in `./screenshots` folder:
```bash
# View local screenshots
ls -lh screenshots/

# Open in browser
start screenshots/screenshot_001.png  # Windows
open screenshots/screenshot_001.png   # macOS
```

---

## Expected Behavior Summary

✅ **What you should see**:

1. **Session Creation (5-10 seconds)**:
   - Orchestrator logs show session creation flow
   - Agent initialization with tools registered
   - Response with `session_id`

2. **Task Execution (60-180 seconds)**:
   - 10-20 turns (depends on task complexity)
   - Each turn shows:
     - API call timing
     - Tool calls with inputs
     - HTTP requests to container
     - Tool results
   - Final response with task summary

3. **Tool Calls**:
   - **computer/screenshot**: ~0.4-0.8s per screenshot
   - **computer/click, type, key**: ~0.1-0.3s each
   - **bash**: ~0.05-0.5s depending on command
   - **editor/create, view**: ~0.05-0.2s each

4. **Total Time**:
   - Simple task (1 screenshot): ~10-20 seconds
   - Medium task (browse + bash): ~30-60 seconds
   - Complex task (multi-step like Hacker News): ~60-180 seconds

---

## API Reference Quick Guide

### Create Session
```
POST /sessions
Body: {"name": "optional-session-name"}
Response: {session_id, name, container_url, status, created_at}
```

### Run Task
```
POST /sessions/{session_id}/run
Body: {"task": "your task description here"}
Response: {session_id, status, result, task_count, screenshots[]}
```

### Get Session Info
```
GET /sessions/{session_id}
Response: {session_id, name, status, created_at, task_count, ...}
```

### List Sessions
```
GET /sessions
Response: [{session_id, name, status, ...}, ...]
```

### Delete Session
```
DELETE /sessions/{session_id}
Response: {message, session_id}
```

### Health Check
```
GET /health
Response: {status, version, sessions_active}
```

---

## Next Steps

After successful local testing:

1. **Deploy to AWS**: See `README.md` for CloudFormation deployment
2. **Production Testing**: Use ECS containers instead of local docker-compose
3. **Scale**: Adjust ECS task count and session management
4. **Monitor**: Set up CloudWatch dashboards and alarms

---

## Support

If you encounter issues not covered here:

1. Check full logs: `docker-compose logs > full_logs.txt`
2. Verify Docker Desktop is running and has sufficient resources
3. Ensure Anthropic API key is valid and has credits
4. Review `README.md` for additional context

---

**Happy Testing! 🚀**
