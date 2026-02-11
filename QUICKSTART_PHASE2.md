# Quick Start: Phase 2 - Computer Use MCP Server

Get the computer use MCP server running in 3 simple steps!

---

## Step 1: Start the MCP Server

Open a terminal and run:

```bash
cd computer_use_codebase/container
python mcp_server.py
```

**Expected Output**:
```
INFO:     Started server process
INFO:     Starting Computer-Use MCP Server...
INFO:     Browser initialized successfully
INFO:     MCP Server ready with 4 tools!
INFO:     Uvicorn running on http://0.0.0.0:8081
```

✅ **MCP Server is now running on port 8081**

---

## Step 2: Test the MCP Server

Open a **second terminal** and run:

```bash
cd computer_use_codebase
python test_mcp_server.py
```

**Expected Output**:
```
======================================================================
   COMPUTER USE MCP SERVER TEST SUITE
======================================================================

✅ PASS  health_check
✅ PASS  tools_list
✅ PASS  tools_call_bash
✅ PASS  tools_call_text_editor
✅ PASS  integration

======================================================================
  ✅ ALL TESTS PASSED
======================================================================
```

---

## Step 3: Test Integration with DynamicAgent

Still in the **second terminal**:

```bash
python test_dynamic_agent.py
```

**Expected Output**:
```
TEST 2: MCP Client
✓ MCPClient initialized
✓ Connection complete
  • Servers connected: 1
  • Total tools discovered: 4

  Server: computer-use
    URL: http://localhost:8081
    Tools: 4
    Sample tools:
      - computer_20250124
      - bash_20250124
      - text_editor_20250728
```

**Before Phase 2**: 0 tools discovered
**After Phase 2**: 4 tools discovered ✅

---

## What Just Happened?

1. **MCP Server Started**: Computer use tools now exposed via MCP protocol
2. **Tools Discovered**: DynamicAgent can now find and use 4 computer use tools
3. **Protocol Verified**: JSON-RPC 2.0 communication working

---

## Available Tools

The MCP server now exposes these 4 tools:

### 1. `computer_20250124`
- **Purpose**: Mouse, keyboard, and screenshots
- **Actions**: click, type, screenshot, mouse_move, etc.

### 2. `bash_20250124`
- **Purpose**: Execute shell commands
- **Usage**: Run bash commands in /workspace

### 3. `text_editor_20250728`
- **Purpose**: File operations
- **Commands**: view, create, str_replace, insert

### 4. `browser`
- **Purpose**: Web automation
- **Actions**: navigate, click, type, screenshot, get_content

---

## Next Steps

### Option A: Test with ClaudeAgentOptions

```python
from orchestrator.claude_options import ClaudeAgentOptions, query
import os

options = ClaudeAgentOptions(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    settings_path=".claude/settings.json",
    max_turns=10
)

# Agent now has access to 4 computer use tools!
result = await query(
    task="List all available tools",
    options=options
)
```

### Option B: Test via API Endpoint

```bash
# Start orchestrator API
uvicorn orchestrator.main:app --reload

# In another terminal:
curl -X POST http://localhost:8000/task/with-options \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Take a screenshot and list the files in /workspace",
    "enable_mcp_servers": true
  }'
```

### Option C: Proceed to Phase 3

Enable the retail-data MCP server and test multi-server workflows!

See [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md) for full documentation.

---

## Troubleshooting

### "Cannot connect to MCP server"

**Problem**: Test fails with connection error

**Solution**:
1. Make sure MCP server is running (Step 1)
2. Check that port 8081 is not blocked
3. Verify URL in `.claude/settings.json` is `http://localhost:8081`

### "0 tools discovered"

**Problem**: No tools found by DynamicAgent

**Checklist**:
- [ ] MCP server running on port 8081
- [ ] settings.json has correct URL
- [ ] Server enabled in settings.json
- [ ] No errors in MCP server logs

### "Browser not initialized"

**Not an error!** Browser initialization is lazy - it will initialize on first use.

---

## Summary

✅ **Phase 2 Complete**
- MCP server running on port 8081
- 4 tools exposed and discoverable
- JSON-RPC 2.0 protocol working
- Integration with DynamicAgent verified

**What's Next**: Phase 3 - Multi-server integration with retail-data MCP server

---

**Date**: 2026-02-09
**Status**: Ready for Testing
**Port**: 8081
**Tools**: 4
