# Option C: Integrated Architecture

## Overview

Computer use is now **one of many optional MCP servers** in the marketplace platform. Users control it via `settings.json` - no code changes needed.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    MARKETPLACE PLATFORM                         │
│                   (DynamicAgent / ClaudeAgentOptions)           │
│                                                                 │
│  User enables/disables features via .claude/settings.json      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MCPClient (Dynamic Discovery)                           │  │
│  │  - Reads settings.json                                   │  │
│  │  - Connects to enabled MCP servers                       │  │
│  │  - Aggregates tools                                      │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│       Discovers tools from enabled servers:                    │
│                   │                                             │
│     ┌─────────────┼─────────────┬──────────────┐              │
│     │             │              │              │              │
│ ┌───▼────┐   ┌──▼──────┐   ┌──▼──────┐   ┌──▼──────┐        │
│ │Computer│   │Retail   │   │Skills   │   │Future   │        │
│ │Use     │   │Data     │   │         │   │Servers  │        │
│ │OPTIONAL│   │         │   │         │   │         │        │
│ └────────┘   └─────────┘   └─────────┘   └─────────┘        │
│   ↑ User                                                       │
│   enables/                                                     │
│   disables                                                     │
└────────────────────────────────────────────────────────────────┘

Enable/Disable Computer Use:
  Edit .claude/settings.json → "computer-use": { "enabled": true/false }
```

---

## Data Flow (Original Multi-Turn Loop)

### Your Exact Flow - Now Through Marketplace

```
USER SENDS REQUEST
     ↓
DynamicAgent (marketplace platform)
     ↓
Loads .claude/settings.json
     ↓
MCPClient discovers enabled servers:
  ✓ computer-use (if enabled) → 4 tools
  ✓ retail-data → 7 tools
  ✓ skills → 3 tools
     ↓
Claude API (acts as brain, decides tools)
     ↓
═══════════════════════════════════════════════════════════
ROUND 1: Initial Screenshot
═══════════════════════════════════════════════════════════
Claude thinks: "Let me see the screen"
Claude decides: Use "computer_20250124" (screenshot action)
     ↓
MCPClient routes to: computer-use MCP server (port 8081)
     ↓
POST http://localhost:8081/
  {"method": "tools/call",
   "params": {"name": "computer_20250124",
              "arguments": {"action": "screenshot"}}}
     ↓
MCP server executes: screenshot_tool.py
Returns: Base64 PNG image
     ↓
Claude sees: [Blank desktop image]
     ↓
═══════════════════════════════════════════════════════════
ROUND 2: Navigate to Hacker News
═══════════════════════════════════════════════════════════
Claude thinks: "Now open Hacker News"
Claude decides: Use "browser" (navigate action)
     ↓
MCPClient routes to: computer-use MCP server
     ↓
POST http://localhost:8081/
  {"method": "tools/call",
   "params": {"name": "browser",
              "arguments": {"action": "navigate",
                           "params": {"url": "https://news.ycombinator.com"}}}}
     ↓
MCP server executes: browser_tool.py (Playwright)
Returns: {status: "success"}
     ↓
Claude sees: "Navigation successful"
     ↓
═══════════════════════════════════════════════════════════
ROUND 3: Screenshot Hacker News
═══════════════════════════════════════════════════════════
Claude thinks: "Capture the page"
Claude decides: Use "computer_20250124" (screenshot)
     ↓
MCPClient routes to: computer-use MCP server
     ↓
MCP server executes: screenshot_tool.py
Returns: Base64 PNG (Hacker News visible!)
     ↓
Claude sees: [Image of Hacker News with stories]
Claude REMEMBERS: Story titles from screenshot
     ↓
═══════════════════════════════════════════════════════════
ROUND 4: Check System Info
═══════════════════════════════════════════════════════════
Claude thinks: "Get system info"
Claude decides: Use "bash_20250124"
     ↓
MCPClient routes to: computer-use MCP server
     ↓
POST http://localhost:8081/
  {"method": "tools/call",
   "params": {"name": "bash_20250124",
              "arguments": {"command": "date && uname -a"}}}
     ↓
MCP server executes: bash_tool.py
Returns: Date and system info
     ↓
Claude sees: "Wed Feb 5 2026, Linux container..."
Claude REMEMBERS: Date and system info
     ↓
═══════════════════════════════════════════════════════════
ROUND 5: Create Report File
═══════════════════════════════════════════════════════════
Claude thinks: "Create report with all collected info"
Claude decides: Use "text_editor_20250728" (create)
     ↓
MCPClient routes to: computer-use MCP server
     ↓
POST http://localhost:8081/
  {"method": "tools/call",
   "params": {"name": "text_editor_20250728",
              "arguments": {"command": "create",
                           "path": "/workspace/hacker_news_report.txt",
                           "file_text": "Date: Feb 5 2026\nSystem: Linux...\n\nTop Stories:\n1. ..."}}}
     ↓
MCP server executes: file_tool.py
Returns: File created
     ↓
Claude sees: "File created successfully"
     ↓
═══════════════════════════════════════════════════════════
ROUND 6: Verify File Contents
═══════════════════════════════════════════════════════════
Claude thinks: "Read back to verify"
Claude decides: Use "text_editor_20250728" (view)
     ↓
MCPClient routes to: computer-use MCP server
     ↓
MCP server executes: file_tool.py (read)
Returns: File contents
     ↓
Claude sees: Full file contents, verifies correctness
     ↓
═══════════════════════════════════════════════════════════
DONE: Final Response
═══════════════════════════════════════════════════════════
Claude returns: "Task completed:
  ✓ Opened Hacker News
  ✓ Captured screenshots
  ✓ Got system info
  ✓ Created report at /workspace/hacker_news_report.txt
  ✓ Verified contents"
     ↓
USER RECEIVES RESPONSE
```

---

## Configuration: Enable/Disable Computer Use

### File: `.claude/settings.json`

```json
{
  "mcpServers": {
    "computer-use": {
      "httpUrl": "http://localhost:8081",
      "enabled": true,           ← SET TO false TO DISABLE
      "description": "4 tools: computer, bash, text_editor, browser"
    },
    "retail-data": {
      "httpUrl": "https://...",
      "enabled": true
    },
    "skills": {
      "httpUrl": "http://localhost:8082",
      "enabled": true
    }
  }
}
```

### When Enabled (enabled: true)
```
✓ computer_20250124 available
✓ bash_20250124 available
✓ text_editor_20250728 available
✓ browser available

Total: 14 tools (4 + 7 + 3)
```

### When Disabled (enabled: false)
```
✗ Computer use tools NOT available

Total: 10 tools (7 + 3)
Agent can still use retail-data and skills
```

---

## How Multi-Turn Loop Works

### Key Component: DynamicAgent.execute_task()

**File**: `orchestrator/agent_runner.py`

```python
async def execute_task(self, task: str, max_turns: int = 25):
    """
    Multi-turn agentic loop (your exact flow)
    """
    conversation_history = [{"role": "user", "content": task}]

    for turn in range(max_turns):
        # Call Claude with all available tools
        response = await self.anthropic_client.messages.create(
            model=self.model,
            messages=conversation_history,
            tools=self.tools,  # From enabled MCP servers
            max_tokens=4096
        )

        if response.stop_reason == "end_turn":
            # Task complete
            return result

        elif response.stop_reason == "tool_use":
            # Execute tools
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    # Route to correct MCP server
                    result = self.mcp_client.call_tool(
                        tool_name,
                        tool_input
                    )

                    # Add to conversation
                    conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })

            # Continue to next turn (Round 2, 3, 4...)
```

**This IS the multi-turn agentic loop you described!**

---

## Manual Testing

### Test Original Flow (Your Exact Example)

**Step 1**: Start MCP Servers (2 terminals)

Terminal 1:
```bash
cd container
python mcp_server.py
# Port 8081 - Computer use
```

Terminal 2:
```bash
python skills_mcp_server.py
# Port 8082 - Skills
```

**Step 2**: Ensure Computer Use Enabled

Edit `.claude/settings.json`:
```json
"computer-use": {
  "enabled": true    ← Make sure this is true
}
```

**Step 3**: Run Test

Terminal 3:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python test_original_flow.py
```

**Expected Output**:
```
ROUND 1: Claude takes screenshot
ROUND 2: Claude navigates to HN
ROUND 3: Claude takes screenshot (sees HN)
ROUND 4: Claude runs bash command
ROUND 5: Claude creates report file
ROUND 6: Claude reads file back

✅ Original flow executed via marketplace!
```

---

## Comparison: Old vs New

### OLD (Before Marketplace)

**File**: `agent/computer_use_agent.py`

```python
# Hardcoded to computer use only
agent = ComputerUseAgent(container_url)
result = await agent.run(task)
```

- ❌ Only computer use tools
- ❌ Can't add other tools
- ❌ Hardcoded logic

### NEW (Integrated Architecture - Option C)

**File**: `orchestrator/agent_runner.py`

```python
# Marketplace with optional computer use
agent = DynamicAgent(settings_path=".claude/settings.json")
result = await agent.execute_task(task)
```

- ✅ Computer use + retail + skills + ...
- ✅ Add tools via settings.json
- ✅ Computer use is optional
- ✅ Same multi-turn loop
- ✅ Unified platform

---

## Benefits of Option C

### 1. Backward Compatible ✅
- Original flow still works
- Same multi-turn loop
- Claude decides tools same way

### 2. Optional Computer Use ✅
- User controls via settings.json
- No code changes to enable/disable
- `"enabled": true/false`

### 3. Extended Capabilities ✅
- Computer use + data tools + business tools
- All work together
- Cross-server workflows possible

### 4. Future-Proof ✅
- Add new MCP servers anytime
- No code changes
- Scalable architecture

---

## Quick Reference

### Enable Computer Use
```json
// .claude/settings.json
"computer-use": { "enabled": true }
```

### Disable Computer Use
```json
// .claude/settings.json
"computer-use": { "enabled": false }
```

### Use via Code
```python
from orchestrator.claude_options import ClaudeAgentOptions, query

options = ClaudeAgentOptions(
    api_key=api_key,
    settings_path=".claude/settings.json"
)

# Computer use tools available if enabled in settings
result = await query(task=your_task, options=options)
```

### Multi-Turn Loop
✅ **Automatic** - DynamicAgent handles it
- Claude sees screenshots
- Claude maintains context
- Claude decides next tool
- Repeat until done

---

## Summary

### What Changed
- ✅ Computer use → MCP server (one of many)
- ✅ Enable/disable via settings.json
- ✅ Unified marketplace interface
- ✅ Multi-turn loop preserved

### What Stayed Same
- ✅ Original flow (screenshot → think → tool)
- ✅ Claude as decision-making brain
- ✅ Context maintained across rounds
- ✅ Tool execution logic

### User Experience
**Before**: Computer use only (hardcoded)
**After**: Computer use + data + skills (configurable)

**Control**: `settings.json` → `"enabled": true/false`

---

---

## IMPORTANT: MCP Server Implementation Details

### Corrected Implementation (2026-02-09)

The `container/mcp_server.py` file has been **corrected** to be a thin wrapper around the official Anthropic computer use implementation.

#### What It Does

**MCP Server (port 8081)** acts as a protocol adapter:
- Exposes official Anthropic tool IDs via MCP protocol
- Routes tool calls to container server (port 8080) via HTTP
- Does NOT reimplement tools - just translates MCP to HTTP API
- Preserves Docker + Xvfb desktop environment

**Container Server (port 8080)** executes the official tools:
- Runs inside Docker with Xvfb virtual display
- Uses official Anthropic tool implementations
- Provides HTTP API: /tools/bash, /tools/browser, /tools/file/*, /tools/screenshot

#### Architecture Flow

```
┌─────────────────────────────────────────────────────────┐
│  Marketplace Platform (DynamicAgent + MCPClient)        │
└────────────────────┬────────────────────────────────────┘
                     │ MCP Protocol (JSON-RPC 2.0)
                     ↓
┌─────────────────────────────────────────────────────────┐
│  MCP Server (container/mcp_server.py) - Port 8081      │
│  - Exposes: computer_20250124, bash_20250124,          │
│             text_editor_20250728, browser               │
│  - Thin wrapper: MCP → HTTP translation                │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP API
                     ↓
┌─────────────────────────────────────────────────────────┐
│  Container Server (container/server.py) - Port 8080    │
│  - Docker container with Xvfb (virtual display)        │
│  - Official Anthropic tool implementations             │
│  - Endpoints: /tools/bash, /tools/browser, etc.        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴───────────┬─────────────┐
        ↓                        ↓             ↓
    Xvfb Display          Playwright      Bash Shell
    (Virtual X11)         (Chromium)      (/workspace)
```

#### Key Differences from Simplified Version

**❌ Previous (WRONG)**:
- Reimplemented tools using simplified Playwright
- Called tool implementations directly
- Lost Docker + Xvfb architecture

**✅ Current (CORRECT)**:
- Wraps official Anthropic implementation
- Routes to container server via HTTP
- Preserves Docker + Xvfb + multi-turn loop

See [MCP_WRAPPER_FIX.md](MCP_WRAPPER_FIX.md) for detailed explanation.

---

**Date**: 2026-02-09
**Status**: ✅ Integrated Architecture Complete (Official Tools Wrapped)
**Architecture**: Option C - Unified Marketplace Platform
**Implementation**: MCP wrapper around official Anthropic computer use tools
