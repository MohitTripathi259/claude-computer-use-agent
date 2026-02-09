# Quick Start - 5 Minute Test

Fast track to test your Computer-Use Agent in 5 minutes.

---

## Prerequisites

- ✅ Docker Desktop running
- ✅ Anthropic API key ready

---

## 1. Setup (30 seconds)

```bash
# Navigate to project
cd c:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
```

**⚠️ Replace `sk-ant-your-key-here` with your actual Anthropic API key**

---

## 2. Start Containers (2 minutes)

```bash
# Build and start
docker-compose up -d

# Watch logs in separate terminal
docker-compose logs -f orchestrator
```

**Wait for**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
ORCHESTRATOR — STARTUP COMPLETE
```

---

## 3. Create Session (Postman or curl)

### Option A: Postman

1. **POST** `http://localhost:8000/sessions`
2. **Body** (raw JSON):
   ```json
   {"name": "test"}
   ```
3. **Send**
4. **Copy** the `session_id` from response

### Option B: curl (Git Bash)

```bash
SESSION_ID=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}' | jq -r '.session_id')

echo "Session ID: $SESSION_ID"
```

---

## 4. Run Test Task (2 minutes)

### Option A: Postman

1. **POST** `http://localhost:8000/sessions/{SESSION_ID}/run`
   - Replace `{SESSION_ID}` with your ID
2. **Body** (raw JSON):
   ```json
   {
     "task": "Take a screenshot, then use bash to check the date and system info (uname -a), then create a file at /workspace/test_report.txt with today's date and system info. Finally, read the file back to verify."
   }
   ```
3. **Send**
4. **Wait** 60-120 seconds
5. **Watch** the orchestrator logs terminal - you'll see every step!

### Option B: curl

```bash
curl -X POST "http://localhost:8000/sessions/$SESSION_ID/run" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Take a screenshot, then use bash to check the date and system info (uname -a), then create a file at /workspace/test_report.txt with todays date and system info. Finally, read the file back to verify."
  }'
```

---

## 5. Verify Results

**Expected Response**:
```json
{
  "session_id": "...",
  "status": "completed",
  "result": "I completed all the steps: 1) Took a screenshot...",
  "task_count": 1,
  "screenshots": ["https://..."]
}
```

**Verify file created**:
```bash
# Enter container
docker exec -it computer-use-container cat /workspace/test_report.txt

# Should show date and system info
```

---

## What You'll See in Logs

### Turn 1 - Screenshot
```
TURN 1/50
>> Calling Anthropic API...
<< API responded in 2.3s
   Stop reason: tool_use
>> Executing tool calls...
  ┌─ Tool Call #1
  │  Tool: computer
  │  Input: {"action": "screenshot"}
    ├─ _exec_computer
    │  HTTP: 0.45s
    │  Image: 1920x1080, base64 length=123456
    └─ Returning image block
  │  Result: [image] 1 block(s)
  └─ [OK]
```

### Turn 2 - Bash Command
```
TURN 2/50
  ┌─ Tool Call #2
  │  Tool: bash
  │  Input: {"command": "date && uname -a"}
    ├─ _exec_bash
    │  HTTP: 0.08s
    │  Exit code: 0
    │  STDOUT length: 156 chars
    └─ Result: 189 chars
  └─ [OK]
```

### Turn 3 - Create File
```
TURN 3/50
  ┌─ Tool Call #3
  │  Tool: str_replace_based_edit_tool
  │  Input: {"command": "create", "path": "/workspace/test_report.txt", ...}
    ├─ _exec_editor
    │  HTTP: 0.05s
    └─ File created
  └─ [OK]
```

### Done
```
======================================================================
  TASK COMPLETE  [AGENT-ABC123]
======================================================================
  Total turns: 5
  Total tool calls: 5
  Total time: 45.2s
======================================================================
```

---

## Troubleshooting

### "Connection refused"
```bash
# Check containers are running
docker-compose ps

# Both should show "Up"
# If not:
docker-compose logs computer
docker-compose logs orchestrator
```

### "ANTHROPIC_API_KEY is missing"
```bash
# Verify .env exists
cat .env

# Should show: ANTHROPIC_API_KEY=sk-ant-...
# If wrong:
echo "ANTHROPIC_API_KEY=your-real-key" > .env
docker-compose restart orchestrator
```

### "Postman timeout"
- Increase timeout: Settings → General → Request timeout → 300000ms
- Or use curl (no timeout)

---

## Next Steps

✅ **Works?** See [LOCAL_TESTING_GUIDE.md](./LOCAL_TESTING_GUIDE.md) for:
- Full Hacker News test case
- VNC desktop viewing
- Advanced debugging
- Production deployment

❌ **Issues?** Check:
1. Docker Desktop has 4GB+ RAM allocated
2. Ports 8000, 8080, 5900 are not in use
3. API key is correct and has credits

---

## Cleanup

```bash
# Stop containers
docker-compose down

# Remove workspace data too
docker-compose down -v
```

---

**That's it! You just ran a Claude agent with computer-use capabilities! 🎉**

For the **full test** with Hacker News research task, see [LOCAL_TESTING_GUIDE.md](./LOCAL_TESTING_GUIDE.md)
