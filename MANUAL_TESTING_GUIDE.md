# Complete Manual Testing Guide - End-to-End

**Goal**: Test the entire codebase manually from scratch with step-by-step instructions.

---

## 📋 **Prerequisites Checklist**

Before starting, verify you have:

- [ ] Docker Desktop running
- [ ] Python 3.11+ installed
- [ ] Postman installed
- [ ] AWS credentials configured (for S3 skills)
- [ ] Terminal/Command Prompt ready

---

## 🚀 **Phase 1: Environment Setup**

### **Step 1.1: Open Terminal**

Open Command Prompt or PowerShell as Administrator.

```cmd
Windows Key + R → type "cmd" → Enter
```

### **Step 1.2: Navigate to Project**

```cmd
cd C:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase
```

### **Step 1.3: Verify .env File**

```cmd
type .env
```

**Expected Output:**
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx
```

✅ **If you see the API key, proceed. Otherwise, set it:**

```cmd
echo ANTHROPIC_API_KEY=sk-ant-your-key-here > .env
```

---

## 🐳 **Phase 2: Docker Services**

### **Step 2.1: Check Docker Status**

```cmd
docker --version
```

**Expected:** `Docker version 20.x.x` or higher

### **Step 2.2: Verify Docker Containers**

```cmd
docker ps -a
```

**Expected Output:**
```
CONTAINER ID   IMAGE                                    STATUS
55849320c5c6   computer_use_codebase-computer          Up (healthy)
c61ac55c6ced   computer_use_codebase-orchestrator      Up (healthy)
```

### **Step 2.3: Start Containers (if not running)**

If containers are stopped:

```cmd
cd container
docker-compose up -d
cd ..
```

Wait 30 seconds for containers to be healthy.

### **Step 2.4: Test Computer Use Container**

```cmd
curl http://localhost:8080/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "display": ":99",
  "workspace": "/workspace",
  "browser_initialized": true
}
```

✅ **If you see "healthy", continue. Otherwise:**

```cmd
cd container
docker-compose restart
cd ..
```

---

## 🖥️ **Phase 3: Start API Server**

### **Step 3.1: Open New Terminal Window**

Keep Docker logs terminal open, open a **new** terminal window:

```cmd
Windows Key + R → type "cmd" → Enter
```

### **Step 3.2: Navigate to Project**

```cmd
cd C:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase
```

### **Step 3.3: Start API Server**

```cmd
python api_server.py
```

**Expected Startup Logs:**
```
================================================================================
🚀 Starting FastAPI Server - E2E Testing API
================================================================================
Endpoints:
  - http://localhost:8003/
  - http://localhost:8003/status
  - http://localhost:8003/execute
  - http://localhost:8003/health
================================================================================

Loaded environment variables from .env file

================================================================================
📋 Initializing DynamicAgent...
================================================================================
   Settings: .claude/settings.json
   S3 Skills: Enabled
   S3 Bucket: cerebricks-studio-agent-skills
   S3 Prefix: skills_phase3/

[... MCP server connections ...]

================================================================================
✅ AGENT INITIALIZED SUCCESSFULLY
================================================================================
   MCP Servers: 3
      • computer-use: 0 tools
      • retail-data: 11 tools
      • skills: 0 tools
   S3 Skills Loaded: True
      • Skills: ['pdf_report_generator']
   Total Tools: 11
================================================================================

INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8003 (Press CTRL+C to quit)
```

✅ **Key Success Indicators:**
- ✅ "AGENT INITIALIZED SUCCESSFULLY"
- ✅ "S3 Skills Loaded: True"
- ✅ "retail-data: 11 tools"
- ✅ "Uvicorn running on http://0.0.0.0:8003"

⚠️ **Common Issues:**

**Issue 1:** Port 8003 already in use
```
Error: [Errno 10048] error while attempting to bind
```
**Fix:** Kill existing process:
```cmd
netstat -ano | findstr :8003
taskkill /PID <process_id> /F
```

**Issue 2:** S3 Skills Loaded: False
```
S3 Skills Loaded: False
```
**Fix:** Check AWS credentials:
```cmd
aws s3 ls s3://cerebricks-studio-agent-skills/
```

**Issue 3:** Module not found
```
ModuleNotFoundError: No module named 'fastapi'
```
**Fix:** Install dependencies:
```cmd
pip install fastapi uvicorn pydantic python-dotenv anthropic httpx boto3 pyyaml
```

---

## 🔍 **Phase 4: Verify Services**

### **Step 4.1: Open THIRD Terminal Window**

Keep API server running, open another terminal for testing:

```cmd
Windows Key + R → type "cmd" → Enter
```

### **Step 4.2: Test Health Endpoint**

```cmd
curl http://localhost:8003/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "agent_initialized": true,
  "timestamp": "2026-02-10T14:30:00.123456"
}
```

✅ **Success!** API server is working.

### **Step 4.3: Test Status Endpoint**

```cmd
curl http://localhost:8003/status
```

**Expected Response (abbreviated):**
```json
{
  "status": "operational",
  "mcp_servers": {
    "retail-data": {
      "url": "https://m1qk67awy4.execute-api.us-west-2.amazonaws.com/prod/mcp_server",
      "enabled": true,
      "tools_count": 11,
      "tools": ["get_products", "get_stores", ...]
    }
  },
  "s3_skills": {
    "enabled": true,
    "skills": [{
      "name": "pdf_report_generator",
      "version": "1.0.0"
    }]
  },
  "total_tools": 11
}
```

✅ **Success!** All services are operational.

---

## 📬 **Phase 5: Postman Setup**

### **Step 5.1: Open Postman**

Launch Postman application.

### **Step 5.2: Import Collection**

1. Click **Import** button (top left)
2. Click **Choose Files**
3. Navigate to: `C:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase`
4. Select: `postman_collection.json`
5. Click **Open**
6. Click **Import**

**Expected:** Collection appears in left sidebar:
```
📁 Computer Use + S3 Skills - E2E Testing
   📁 1. Health & Status
   📁 2. Computer Use Tools
   📁 3. Retail Data Tools
   📁 4. S3 Skills Testing
   📁 5. Legacy Skills
   📁 6. Complex Multi-Tool Workflows
   📁 7. Stress Testing
```

✅ **18 test requests imported**

---

## 🧪 **Phase 6: Manual Testing Sequence**

### **Test 1: Health Check** ⏱️ <5 seconds

**Steps:**
1. In Postman, expand: **"1. Health & Status"**
2. Click: **"Health Check"**
3. Verify URL: `http://localhost:8003/health`
4. Click: **Send** button

**Expected Response:**
```json
{
  "status": "healthy",
  "agent_initialized": true,
  "timestamp": "2026-02-10T..."
}
```

**Terminal Logs (API Server Window):**
```
[No extensive logs - just simple health check]
```

✅ **Pass Criteria:** Status 200, "healthy" response

---

### **Test 2: System Status** ⏱️ <5 seconds

**Steps:**
1. In Postman, click: **"System Status (Full Details)"**
2. Verify URL: `http://localhost:8003/status`
3. Click: **Send**

**Expected Response:**
```json
{
  "status": "operational",
  "mcp_servers": {...},
  "s3_skills": {
    "enabled": true,
    "skills": [{"name": "pdf_report_generator"}]
  },
  "total_tools": 11
}
```

**Terminal Logs:**
```
================================================================================
📊 STATUS CHECK REQUESTED
================================================================================
MCP Servers: 3
S3 Skills: 1
Total Tools: 11
================================================================================
```

✅ **Pass Criteria:**
- Status 200
- "operational" status
- S3 skills enabled: true
- Total tools: 11

---

### **Test 3: S3 Skill Discovery** ⏱️ 10-20 seconds

**Purpose:** Verify S3 skills loaded and Claude can see them.

**Steps:**
1. Expand: **"4. S3 Skills Testing"**
2. Click: **"S3 Skill Discovery + Context Understanding"**
3. Click: **Send**

**Expected Response Structure:**
```json
{
  "success": true,
  "response": "I can see that there is 1 skill loaded from S3:\n\n1. pdf_report_generator...",
  "turns": 2,
  "tools_used": [],
  "mcp_servers_active": ["computer-use", "retail-data", "skills"],
  "s3_skills_loaded": ["pdf_report_generator"],
  "execution_time_seconds": 5.23
}
```

**Terminal Logs (Watch Carefully):**
```
================================================================================
🤖 NEW AGENT EXECUTION REQUEST
================================================================================
Prompt: Demonstrate your knowledge of S3 skills...
Max Turns: 8

📝 System Prompt Generated
   Length: ~12000 characters
   Contains S3 Skills: True
   MCP Tools Available: 11

🔄 Starting Multi-Turn Execution Loop

================================================================================
TURN 1/8
================================================================================
📡 Calling Claude API...
✅ Response received (stop_reason: end_turn)

📄 FINAL RESPONSE:
I can see that there is 1 skill loaded from S3:

1. **pdf_report_generator** (Version 1.0.0)
   - Description: Generates professional PDF reports, presentations...
   [Claude's full explanation]

================================================================================
✅ EXECUTION COMPLETE
================================================================================
Total Turns: 2
Tools Used: []
Execution Time: 5.23s
================================================================================
```

✅ **Pass Criteria:**
- Success: true
- Response mentions "pdf_report_generator"
- Claude explains what the skill does
- S3 skills loaded: ["pdf_report_generator"]
- Execution completes

---

### **Test 4: Retail Data Query** ⏱️ 30-60 seconds

**Purpose:** Test retail MCP tools and multi-turn execution.

**Steps:**
1. Expand: **"3. Retail Data Tools"**
2. Click: **"Query Sales Data with Aggregations"**
3. Click: **Send**

**Expected Response:**
```json
{
  "success": true,
  "response": "Based on the retail database analysis...",
  "turns": 5-8,
  "tools_used": ["query_sales_data", "get_products", "smart_query"],
  "mcp_servers_active": ["retail-data"],
  "execution_time_seconds": 25.67
}
```

**Terminal Logs (Multi-Turn Example):**
```
================================================================================
🤖 NEW AGENT EXECUTION REQUEST
================================================================================
Prompt: Query the retail database for the following analysis...

================================================================================
TURN 1/10
================================================================================
📡 Calling Claude API...
✅ Response received (stop_reason: tool_use)

🔧 TOOL CALLS REQUESTED:

   Tool: get_products
   Input: {'limit': 100}
   ⚙️  Executing via MCP...
   ✅ Success

================================================================================
TURN 2/10
================================================================================
📡 Calling Claude API...
✅ Response received (stop_reason: tool_use)

🔧 TOOL CALLS REQUESTED:

   Tool: get_sales_summary
   Input: {'days': 30, 'group_by': 'category'}
   ⚙️  Executing via MCP...
   ✅ Success

[... more turns ...]

================================================================================
TURN 5/10
================================================================================
📡 Calling Claude API...
✅ Response received (stop_reason: end_turn)

📄 FINAL RESPONSE:
Based on my analysis of the retail database:

1. **Total Sales by Category (Last 30 Days)**
   - Electronics: $125,340
   - Clothing: $98,220
   [...]

2. **Average Order Value by Segment**
   [...]

================================================================================
✅ EXECUTION COMPLETE
================================================================================
Total Turns: 5
Tools Used: ['get_products', 'get_sales_summary', 'smart_query']
Execution Time: 28.45s
================================================================================
```

✅ **Pass Criteria:**
- Success: true
- Multiple turns (5-10)
- Tools used: retail data tools
- Response includes data analysis
- No errors

---

### **Test 5: Bash Commands** ⏱️ 30-60 seconds

**Purpose:** Test computer use bash tool.

**Steps:**
1. Expand: **"2. Computer Use Tools"**
2. Click: **"Bash Commands + File Analysis"**
3. Click: **Send**

**Expected Response:**
```json
{
  "success": true,
  "response": "I found X Python files in the codebase...",
  "turns": 8-12,
  "tools_used": ["bash"],
  "execution_time_seconds": 45.23
}
```

**Terminal Logs:**
```
================================================================================
TURN 1/10
================================================================================
🔧 TOOL CALLS REQUESTED:

   Tool: bash
   Input: {'command': 'ls *.py'}
   ⚙️  Executing via MCP...
   ✅ Success

================================================================================
TURN 2/10
================================================================================
🔧 TOOL CALLS REQUESTED:

   Tool: bash
   Input: {'command': 'wc -l *.py'}
   ⚙️  Executing via MCP...
   ✅ Success

[... more bash commands ...]
```

✅ **Pass Criteria:**
- Bash commands execute successfully
- File listing works
- Line counting works
- Analysis is provided

---

### **Test 6: Complex Workflow** ⏱️ 2-5 minutes

**Purpose:** Test multi-tool orchestration with S3 skills.

**Steps:**
1. Expand: **"6. Complex Multi-Tool Workflows"**
2. Click: **"Full Business Intelligence Pipeline"**
3. **⚠️ Warning:** This takes 2-5 minutes
4. Click: **Send**

**Expected Process (8 Steps):**
```
Step 1: Query retail sales data → retail MCP tools
Step 2: Create data directory → bash
Step 3: Save to CSV → bash + file operations
Step 4: Analyze data → retail tools
Step 5: Create Python script → text editor
Step 6: Execute script → bash
Step 7: Generate PDF report → S3 pdf_report_generator skill
Step 8: Verify files → bash
```

**Terminal Logs (Will be extensive):**
```
================================================================================
🤖 NEW AGENT EXECUTION REQUEST
================================================================================
Prompt: Complete BI pipeline: 1) Query retail sales data...
Max Turns: 25

[TURN 1] Query sales data...
[TURN 2] Create directory...
[TURN 3] Save CSV...
[TURN 4] Analyze data...
[TURN 5-15] Multiple tool calls...
[TURN 20] Generate PDF with S3 skill...
[TURN 25] Verification...

================================================================================
✅ EXECUTION COMPLETE
================================================================================
Total Turns: 22
Tools Used: ['query_sales_data', 'bash', 'str_replace_based_edit_tool', ...]
Execution Time: 156.78s
================================================================================
```

✅ **Pass Criteria:**
- Success: true
- 20-25 turns
- Multiple tools used
- S3 skill referenced/attempted
- Completes without errors

---

## 📊 **Phase 7: Results Analysis**

### **Step 7.1: Review Test Results**

For each test, check:

| Test | Expected Turns | Expected Tools | Pass/Fail |
|------|---------------|----------------|-----------|
| Health Check | 0 | None | ✅ |
| System Status | 0 | None | ✅ |
| S3 Skill Discovery | 1-2 | None | ✅ |
| Retail Data Query | 5-10 | Retail tools | ✅ |
| Bash Commands | 8-12 | bash | ✅ |
| Complex Workflow | 20-25 | Multiple | ✅ |

### **Step 7.2: Verify Terminal Logs**

Check that terminal shows:
- ✅ Turn-by-turn execution
- ✅ Tool calls with inputs
- ✅ Success confirmations
- ✅ Final responses
- ✅ Execution times

### **Step 7.3: Check Postman Responses**

Each response should have:
- ✅ `success: true`
- ✅ `response` field with Claude's answer
- ✅ `turns` field showing turn count
- ✅ `tools_used` array
- ✅ `s3_skills_loaded` array

---

## 🎯 **Phase 8: Validation Checklist**

### **Core Functionality**
- [ ] API server starts successfully
- [ ] Docker containers running and healthy
- [ ] Health endpoint returns healthy
- [ ] Status endpoint shows all tools
- [ ] S3 skills loaded (pdf_report_generator)
- [ ] Retail MCP tools working (11 tools)

### **Execution Flow**
- [ ] Multi-turn execution works
- [ ] Tool calls execute successfully
- [ ] Terminal shows detailed logs
- [ ] Responses are meaningful
- [ ] No critical errors

### **S3 Skills Integration**
- [ ] S3 skills loaded on startup
- [ ] Claude knows about pdf_report_generator
- [ ] Skills appear in system prompt
- [ ] Skills can be referenced in prompts

### **MCP Integration**
- [ ] Retail data MCP working (AWS)
- [ ] Computer use MCP working (Docker)
- [ ] Tools discovered automatically
- [ ] Tool execution succeeds

---

## 📝 **Phase 9: Document Issues**

### **Create Test Report**

Create a file: `test_results.txt`

```txt
=== E2E Test Results ===
Date: [Today's date]
Tester: [Your name]

Test 1: Health Check
Status: PASS / FAIL
Notes: [Any issues]

Test 2: System Status
Status: PASS / FAIL
S3 Skills Loaded: YES / NO
Total Tools: [Number]
Notes: [Any issues]

Test 3: S3 Skill Discovery
Status: PASS / FAIL
Claude Response: [Summary]
Notes: [Any issues]

Test 4: Retail Data Query
Status: PASS / FAIL
Turns: [Number]
Tools Used: [List]
Notes: [Any issues]

Test 5: Bash Commands
Status: PASS / FAIL
Execution: SUCCESSFUL / FAILED
Notes: [Any issues]

Test 6: Complex Workflow
Status: PASS / FAIL
Duration: [Seconds]
Completeness: FULL / PARTIAL
Notes: [Any issues]

=== Summary ===
Total Tests: 6
Passed: [Number]
Failed: [Number]
Success Rate: [Percentage]%

=== Key Findings ===
1. [Finding 1]
2. [Finding 2]
3. [Finding 3]

=== Recommendations ===
1. [Recommendation 1]
2. [Recommendation 2]
```

---

## 🔧 **Phase 10: Troubleshooting**

### **Common Issues and Fixes**

#### **Issue 1: API Server Won't Start**

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Fix:**
```cmd
pip install fastapi uvicorn pydantic python-dotenv anthropic httpx boto3 pyyaml
```

#### **Issue 2: S3 Skills Not Loading**

**Symptom:**
```
S3 Skills Loaded: False
```

**Diagnosis:**
```cmd
aws s3 ls s3://cerebricks-studio-agent-skills/skills_phase3/
```

**Fix:** Configure AWS credentials:
```cmd
aws configure
```

#### **Issue 3: Docker Containers Not Running**

**Symptom:**
```
Failed to connect to 'computer-use'
```

**Fix:**
```cmd
cd container
docker-compose up -d
docker ps
```

#### **Issue 4: Tool Execution Fails**

**Symptom:**
```
Tool execution error: Connection refused
```

**Diagnosis:** Check which MCP server is failing.

**Fix:** Restart specific service.

#### **Issue 5: Slow Responses**

**Symptom:** Tests taking >2 minutes.

**Possible Causes:**
- Network latency to AWS
- Claude API throttling
- Large data processing

**Fix:** Reduce `max_turns` in Postman requests.

---

## ✅ **Phase 11: Cleanup**

### **Step 11.1: Stop API Server**

In API server terminal:
```
Press: Ctrl + C
```

**Expected:**
```
INFO:     Shutting down
INFO:     Finished server process
```

### **Step 11.2: Stop Docker Containers (Optional)**

```cmd
cd container
docker-compose down
```

### **Step 11.3: Save Postman Collection**

1. In Postman, right-click collection
2. Select **Export**
3. Save as: `test_results_[date].json`

---

## 📚 **Additional Resources**

### **Documentation Files**
- `E2E_TESTING_GUIDE.md` - Detailed testing procedures
- `CONFIGURATION_GUIDE.md` - Configuration reference
- `S3_SKILLS_READY.md` - S3 skills documentation
- `IMPLEMENTATION_COMPLETE.md` - Implementation summary

### **Postman Collection**
- `postman_collection.json` - 18 test requests
- All tests include complex multi-step queries
- Terminal logs enabled for all executions

### **Log Files**
- API Server: Console output (save with `tee` if needed)
- Docker Containers: `docker logs <container_id>`

---

## 🎓 **Learning Points**

### **What You Tested**

1. **API Integration**
   - FastAPI server with multiple endpoints
   - Health checks and status monitoring
   - Request/response handling

2. **S3 Skills**
   - Dynamic skill loading from S3
   - System prompt injection
   - Skill discovery and usage

3. **MCP Integration**
   - Multiple MCP server connections
   - Tool discovery and execution
   - AWS and local server integration

4. **Multi-Turn Execution**
   - Agentic loop with Claude
   - Tool orchestration
   - Complex workflows

5. **Terminal Logging**
   - Detailed execution traces
   - Turn-by-turn progress
   - Tool call monitoring

---

## 🏆 **Success Criteria**

### **Minimum Passing Grade: 4/6 tests passing**

Your system is working if:
- ✅ API server starts
- ✅ S3 skills load
- ✅ At least one MCP server works
- ✅ Multi-turn execution completes
- ✅ Terminal logs appear correctly

### **Excellent Grade: 6/6 tests passing**

Full functionality confirmed if:
- ✅ All services start cleanly
- ✅ S3 skills fully integrated
- ✅ All MCP servers operational
- ✅ Complex workflows complete
- ✅ No errors in logs

---

## 📞 **Support**

If you encounter issues:

1. Check terminal logs for error messages
2. Verify all services are running
3. Review test_results.txt
4. Check Docker container health
5. Verify AWS credentials

---

**🎉 You're ready to test the entire codebase manually!**

**Estimated Total Time:** 20-30 minutes for all 6 tests

**Start with Phase 1 and work through each phase sequentially.**

