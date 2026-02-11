# End-to-End Testing Guide - Postman + Terminal Logging

Complete procedure for testing the entire system via Postman with detailed terminal logs.

---

## 🚀 Quick Start

### Prerequisites

1. **All MCP servers running**
2. **AWS credentials configured** (for S3 skills)
3. **Anthropic API key** set
4. **Postman** installed

### Start All Services

```bash
# Terminal 1: Computer Use Server
cd container
python server.py

# Terminal 2: Retail Data Server
cd retail_mcp_server
python main.py

# Terminal 3: Skills Server
cd skills_mcp_server
python main.py

# Terminal 4: API Server (this shows all logs)
cd computer_use_codebase
set ANTHROPIC_API_KEY=your-key-here
python api_server.py
```

---

## 📋 Step-by-Step Testing Procedure

### Step 1: Start API Server with Logging

```bash
cd C:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase

# Set environment variable
set ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Start API server (this terminal will show ALL execution logs)
python api_server.py
```

**You will see startup logs:**
```
================================================================================
🚀 STARTING API SERVER
================================================================================
📋 Initializing DynamicAgent...
   Settings: .claude/settings.json
   S3 Skills: Enabled
   S3 Bucket: cerebricks-studio-agent-skills
   S3 Prefix: skills_phase3/

================================================================================
✅ AGENT INITIALIZED SUCCESSFULLY
================================================================================
   MCP Servers: 3
      • computer-use: 4 tools
      • retail-data: 7 tools
      • skills: 3 tools
   S3 Skills Loaded: True
      • Skills: ['pdf_report_generator']
   Total Tools: 14
================================================================================
```

### Step 2: Import Postman Collection

1. Open **Postman**
2. Click **Import**
3. Select file: `postman_collection.json`
4. Collection appears: **"Computer Use + S3 Skills - E2E Testing"**

### Step 3: Test Each Category

The collection is organized by feature category:

---

## 🧪 Test Categories

### Category 1: Health & Status

**Purpose**: Verify system is ready

#### Test 1.1: Health Check
- **Request**: `GET http://localhost:8000/health`
- **Expected**: `{"status": "healthy", "agent_initialized": true}`
- **Terminal**: Minimal logging

#### Test 1.2: System Status
- **Request**: `GET http://localhost:8000/status`
- **Expected**: Full system details
- **Terminal logs**:
```
================================================================================
📊 STATUS CHECK REQUESTED
================================================================================
MCP Servers: 3
S3 Skills: 1
Total Tools: 14
================================================================================
```

---

### Category 2: Computer Use Tools

**Purpose**: Test all official Anthropic computer use tools

#### Test 2.1: Screenshot + Visual Analysis

**Request Body**:
```json
{
  "prompt": "Take a screenshot of the current desktop. Analyze what applications are visible, identify any text you can read, describe the color scheme, and tell me if there are any browser windows open.",
  "max_turns": 5,
  "include_s3_skills": true,
  "temperature": 1.0
}
```

**Expected Terminal Logs**:
```
================================================================================
🤖 NEW AGENT EXECUTION REQUEST
================================================================================
Prompt: Take a screenshot of the current desktop...
Max Turns: 5
S3 Skills: True
Temperature: 1.0
================================================================================

📝 System Prompt Generated
   Length: 12000 characters
   Contains S3 Skills: True
   MCP Tools Available: 14

🔄 Starting Multi-Turn Execution Loop

================================================================================
TURN 1/5
================================================================================
📡 Calling Claude API...
✅ Response received (stop_reason: tool_use)

🔧 TOOL CALLS REQUESTED:

   Tool: computer
   Input: {'action': 'screenshot'}
   ⚙️  Executing via MCP...
   ✅ Success

================================================================================
TURN 2/5
================================================================================
📡 Calling Claude API...
✅ Response received (stop_reason: end_turn)

📄 FINAL RESPONSE:
I can see the desktop with...
[Claude's analysis here]

================================================================================
✅ EXECUTION COMPLETE
================================================================================
Total Turns: 2
Tools Used: ['computer']
Execution Time: 3.45s
================================================================================
```

#### Test 2.2: Browser Navigation + Data Extraction

**Request Body**:
```json
{
  "prompt": "Open a browser and navigate to https://news.ycombinator.com. Extract the titles of the top 5 posts, their scores, and number of comments. Navigate to the highest-scored post's comments and summarize discussion points.",
  "max_turns": 15,
  "include_s3_skills": true,
  "temperature": 1.0
}
```

**Expected Terminal Logs** (multi-turn):
```
================================================================================
TURN 1/15
================================================================================
🔧 TOOL CALLS REQUESTED:
   Tool: browser
   Input: {'action': 'navigate', 'url': 'https://news.ycombinator.com'}
   ⚙️  Executing via MCP...
   ✅ Success

================================================================================
TURN 2/15
================================================================================
🔧 TOOL CALLS REQUESTED:
   Tool: browser
   Input: {'action': 'screenshot'}
   ⚙️  Executing via MCP...
   ✅ Success

[... more turns ...]

================================================================================
✅ EXECUTION COMPLETE
================================================================================
Total Turns: 8
Tools Used: ['browser', 'computer']
Execution Time: 15.67s
================================================================================
```

#### Test 2.3: Bash Commands + File Analysis

**Request Body**:
```json
{
  "prompt": "Execute sequence: 1) Use bash to list Python files. 2) Count lines in each using 'wc -l'. 3) Find largest file. 4) Read and summarize it. 5) Check for TODO comments.",
  "max_turns": 10,
  "include_s3_skills": true,
  "temperature": 1.0
}
```

**Expected Terminal Logs**:
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

================================================================================
TURN 5/10
================================================================================
🔧 TOOL CALLS REQUESTED:
   Tool: str_replace_based_edit_tool
   Input: {'command': 'view', 'path': 'orchestrator/agent_runner.py'}
   ⚙️  Executing via MCP...
   ✅ Success

================================================================================
✅ EXECUTION COMPLETE
================================================================================
Total Turns: 7
Tools Used: ['bash', 'str_replace_based_edit_tool']
Execution Time: 8.23s
================================================================================
```

#### Test 2.4: Text Editor Operations

**Request Body**:
```json
{
  "prompt": "Using text editor: 1) Create 'test_analysis.py'. 2) Write log analyzer function with docstrings. 3) Add type hints. 4) Add unit tests. 5) Read back and verify syntax.",
  "max_turns": 12,
  "include_s3_skills": true,
  "temperature": 1.0
}
```

**Expected Terminal Logs**:
```
================================================================================
🔧 TOOL CALLS REQUESTED:
   Tool: str_replace_based_edit_tool
   Input: {'command': 'create', 'path': 'test_analysis.py', 'file_text': '...'}
   ⚙️  Executing via MCP...
   ✅ Success

[... multiple edit operations ...]

Tools Used: ['str_replace_based_edit_tool', 'bash']
```

---

### Category 3: Retail Data Tools

**Purpose**: Test database integration

#### Test 3.1: Sales Data Aggregations

**Request Body**:
```json
{
  "prompt": "Query retail database: 1) Total sales by category (30 days). 2) Average order value by segment. 3) Top 10 products by revenue. 4) Products with declining sales. 5) Summarize insights.",
  "max_turns": 10,
  "include_s3_skills": true,
  "temperature": 1.0
}
```

**Expected Terminal Logs**:
```
================================================================================
🔧 TOOL CALLS REQUESTED:
   Tool: query_sales_data
   Input: {'timeframe': '30d', 'group_by': 'category'}
   ⚙️  Executing via MCP...
   ✅ Success

[... multiple retail tool calls ...]

Tools Used: ['query_sales_data', 'query_customers', 'query_products']
```

#### Test 3.2: Customer Behavior Analysis

**Complex query with 6 steps** - tests chaining multiple retail tools.

#### Test 3.3: Inventory + Sales Correlation

**Cross-analysis** - tests combining data from multiple sources.

---

### Category 4: S3 Skills Testing

**Purpose**: Verify S3 skills loaded and usable

#### Test 4.1: PDF Report Generation

**Request Body**:
```json
{
  "prompt": "Using pdf_report_generator skill: 1) Query Q4 2025 sales. 2) Analyze key metrics. 3) Create executive PDF with title, summary, charts, metrics, recommendations. 4) Verify PDF created.",
  "max_turns": 15,
  "include_s3_skills": true,
  "temperature": 1.0
}
```

**Expected Terminal Logs**:
```
📝 System Prompt Generated
   Contains S3 Skills: True

[Claude will reference the pdf_report_generator skill from S3]

🔧 TOOL CALLS REQUESTED:
   Tool: code_executor
   Input: {'code': '... pdf_report_generator script ...'}
   ⚙️  Executing via MCP...
   ✅ Success

Tools Used: ['query_sales_data', 'code_executor']
```

#### Test 4.2: S3 Skill Discovery

**Tests Claude's understanding** of loaded S3 skills.

---

### Category 5: Legacy Skills

**Purpose**: Test local skills (query_database)

#### Test 5.1: Query Database Skill (DynamoDB)

**Request Body**:
```json
{
  "prompt": "Using query_database skill: 1) Query alerts from scraper_engine for project 'Maria'. 2) Filter last 7 days. 3) Group by severity. 4) Count by source. 5) Find patterns. 6) Create summary report.",
  "max_turns": 10,
  "include_s3_skills": true,
  "temperature": 1.0
}
```

**Expected Terminal Logs**:
```
🔧 TOOL CALLS REQUESTED:
   Tool: query_database
   Input: {'project_id': 'Maria', 'days': 7}
   ⚙️  Executing via MCP...
   ✅ Success

Tools Used: ['query_database']
```

---

### Category 6: Complex Multi-Tool Workflows

**Purpose**: Test orchestration of multiple tools

#### Test 6.1: Full Business Intelligence Pipeline

**8-step workflow** combining:
- Retail data queries
- Bash file operations
- Text editor script creation
- Script execution
- PDF generation
- Screenshots
- Verification

**Expected**: 15-25 turns, uses 6+ different tools.

#### Test 6.2: Research + Analysis + Reporting

**8-step workflow** combining:
- Browser research (multiple sites)
- Database queries
- DynamoDB alerts
- Markdown creation
- PDF conversion
- Screenshots
- Logging

**Expected**: 20-30 turns, full tool suite.

#### Test 6.3: Automated Monitoring + Alerting

**8-step system health check** workflow.

---

### Category 7: Stress Testing

**Purpose**: Test limits and reliability

#### Test 7.1: Max Turns Test

**Request**: `max_turns: 50`
- Tests every tool systematically
- Creates comprehensive test report
- Logs each operation

#### Test 7.2: Parallel Operations Test

**Request**: Concurrent tool invocations
- Background bash commands
- Multiple browser tabs
- Large database queries
- Multiple file operations
- Periodic screenshots

---

## 📊 What to Look For in Terminal Logs

### Successful Execution Pattern

```
================================================================================
🤖 NEW AGENT EXECUTION REQUEST
================================================================================
[Request details]

📝 System Prompt Generated
   [Prompt stats with S3 skills confirmation]

🔄 Starting Multi-Turn Execution Loop

[For each turn:]
================================================================================
TURN X/Y
================================================================================
📡 Calling Claude API...
✅ Response received (stop_reason: tool_use or end_turn)

[If tool_use:]
🔧 TOOL CALLS REQUESTED:
   Tool: <tool_name>
   Input: <tool_input>
   ⚙️  Executing via MCP...
   ✅ Success

[If end_turn:]
📄 FINAL RESPONSE:
<Claude's response>

================================================================================
✅ EXECUTION COMPLETE
================================================================================
Total Turns: X
Tools Used: [list]
Execution Time: X.XXs
================================================================================
```

### Error Pattern

```
================================================================================
❌ EXECUTION FAILED
================================================================================
Error: <error message>
================================================================================
```

---

## 🎯 Key Metrics to Track

### Per Request

- ✅ **Success**: `success: true`
- 🔢 **Turns**: How many API calls
- 🔧 **Tools Used**: Which tools executed
- ⏱️ **Execution Time**: Performance
- 🏢 **MCP Servers**: Which servers used
- 📦 **S3 Skills**: Skills referenced

### System Health

- 🟢 **All MCP servers responding**
- 🟢 **S3 skills loaded successfully**
- 🟢 **No tool execution errors**
- 🟢 **Reasonable execution times**

---

## 🐛 Troubleshooting

### No Terminal Logs

**Problem**: API server running but no logs appearing.

**Solution**: Check console handler is attached:
```python
# In api_server.py line ~30
console = logging.StreamHandler()
console.setLevel(logging.INFO)
```

### MCP Server Connection Failed

**Terminal shows**:
```
✗ Failed to connect to 'computer-use': Connection refused
```

**Solution**: Start that MCP server first.

### S3 Skills Not Loading

**Terminal shows**:
```
S3 Skills Loaded: False
```

**Solution**:
1. Check AWS credentials: `aws s3 ls s3://cerebricks-studio-agent-skills/`
2. Verify bucket/prefix in code

### Tool Execution Errors

**Terminal shows**:
```
❌ Error: Tool 'xyz' failed
```

**Solution**: Check MCP server logs for that tool.

---

## 📁 Files Created

```
computer_use_codebase/
├── api_server.py                    # FastAPI server with logging
├── postman_collection.json          # All test requests
├── E2E_TESTING_GUIDE.md            # This guide
└── examples/
    └── s3_skills_configuration.py   # Configuration examples
```

---

## ✅ Complete Test Sequence

### Recommended Order

1. **Health & Status** (2 requests) - Verify setup
2. **Computer Use Tools** (5 requests) - Test core tools
3. **Retail Data Tools** (3 requests) - Test database
4. **S3 Skills** (2 requests) - Verify S3 skills
5. **Legacy Skills** (1 request) - Test local skills
6. **Complex Workflows** (3 requests) - Integration tests
7. **Stress Testing** (2 requests) - Limits testing

**Total**: 18 comprehensive test requests

**Expected Time**: 30-60 minutes for full suite

---

## 🎉 Success Criteria

### ✅ System is Working If:

1. **Status endpoint** shows all servers + skills
2. **Screenshot test** completes successfully
3. **Retail query test** returns data
4. **S3 skill test** shows pdf_report_generator available
5. **Multi-tool workflow** completes without errors
6. **Terminal logs** show clear execution flow
7. **No tool execution failures**

### 📊 Expected Results Summary

```
Total Requests: 18
Expected Success Rate: >95%
Total Tools Available: 14
S3 Skills Available: 1+
Average Execution Time: 5-20s per request
Max Execution Time: <60s per request
```

---

## 🚀 Start Testing Now

```bash
# 1. Start API server
cd C:\Users\MohitTripathi(Quadra\Downloads\Manus\computer_use_codebase
set ANTHROPIC_API_KEY=your-key
python api_server.py

# 2. Open Postman
# 3. Import postman_collection.json
# 4. Start with "Health Check" request
# 5. Watch terminal for detailed logs
# 6. Execute each test category in order
```

**Your terminal will show complete execution traces for every request!**

