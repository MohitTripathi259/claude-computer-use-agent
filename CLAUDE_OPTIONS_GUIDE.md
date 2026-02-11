# ClaudeAgentOptions Wrapper Guide

## Overview

The `ClaudeAgentOptions` wrapper provides an API-compatible interface similar to the official `claude-agent-sdk`, while keeping our custom MCP client implementation underneath.

This allows us to:
1. ✅ Match the official SDK's `ClaudeAgentOptions` structure
2. ✅ Keep our working dynamic MCP discovery implementation
3. ✅ Provide an easy migration path to the official SDK later if needed
4. ✅ Support both simple queries and continuous conversations

---

## Installation

No additional dependencies needed! The wrapper uses our existing implementation.

```bash
# Just make sure you have the base requirements
pip install -r requirements.txt
```

---

## Quick Start

### 1. Basic Usage with `query()` Function

```python
import asyncio
import os
from orchestrator.claude_options import ClaudeAgentOptions, query

async def main():
    # Create options
    options = ClaudeAgentOptions(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        settings_path=".claude/settings.json",
        max_turns=10,
        verbose=True
    )

    # Execute a single task
    result = await query(
        task="List all available tools from MCP servers",
        options=options
    )

    print(f"Status: {result['status']}")
    print(f"Result: {result['result']}")
    print(f"Tool calls: {result['tool_calls']}")

asyncio.run(main())
```

### 2. Continuous Conversation with `ClaudeAgentClient`

```python
from orchestrator.claude_options import ClaudeAgentOptions, ClaudeAgentClient

async def main():
    # Create options
    options = ClaudeAgentOptions(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        settings_path=".claude/settings.json"
    )

    # Create client for continuous conversation
    client = ClaudeAgentClient(options=options)

    # First interaction
    result1 = await client.query("What MCP servers are available?")
    print(result1['result'])

    # Second interaction (maintains context!)
    result2 = await client.query("How many tools do they have?")
    print(result2['result'])

    # Get conversation summary
    summary = client.get_conversation_summary()
    print(f"Total interactions: {summary['total_interactions']}")
    print(f"Total tool calls: {summary['total_tool_calls']}")

asyncio.run(main())
```

---

## ClaudeAgentOptions Parameters

### Core Configuration

```python
options = ClaudeAgentOptions(
    # Required
    api_key="sk-ant-...",                    # Anthropic API key

    # MCP Server Configuration
    settings_path=".claude/settings.json",   # Path to settings
    enable_mcp_servers=True,                 # Load MCP servers
    mcp_servers=None,                        # Explicit server config (optional)

    # Tool Configuration
    allowed_tools=None,                      # Filter to specific tools (None = all)

    # System Prompt
    system_prompt=None,                      # Custom system prompt
    system_prompt_preset=None,               # "default" | "minimal" | "custom"

    # Permissions
    permission_mode="auto",                  # "auto" | "ask" | "manual"

    # Model Configuration
    model="claude-sonnet-4-20250514",        # Claude model ID
    max_turns=25,                            # Max conversation turns
    max_tokens=4096,                         # Max response tokens
    temperature=1.0,                         # Model temperature

    # Context
    cwd=None,                                # Working directory

    # Logging
    verbose=False,                           # Enable verbose logging
    log_tool_calls=True                      # Log tool executions
)
```

### MCP Server Configuration

You can configure MCP servers in two ways:

#### Option A: Load from settings.json (Recommended)

Create `.claude/settings.json`:

```json
{
  "mcpServers": {
    "computer-use": {
      "httpUrl": "http://container:8080",
      "authProviderType": "none",
      "description": "Computer automation tools",
      "enabled": true
    },
    "retail-data": {
      "httpUrl": "https://api.example.com/mcp",
      "authProviderType": "none",
      "description": "Retail data tools",
      "enabled": false
    }
  }
}
```

Then create options:

```python
options = ClaudeAgentOptions(
    api_key=api_key,
    settings_path=".claude/settings.json"  # Auto-loads MCP servers
)
```

#### Option B: Explicit Configuration

```python
from orchestrator.claude_options import McpServerConfig

options = ClaudeAgentOptions(
    api_key=api_key,
    mcp_servers={
        "my-server": McpServerConfig(
            httpUrl="http://localhost:8080/mcp",
            authProviderType="none",
            description="My custom MCP server",
            enabled=True
        )
    }
)
```

---

## Advanced Usage

### Filter to Specific Tools

```python
# Only allow specific tools
options = ClaudeAgentOptions(
    api_key=api_key,
    settings_path=".claude/settings.json",
    allowed_tools=["tool1", "tool2", "tool3"]  # Filter to these tools only
)
```

### Custom System Prompt

```python
options = ClaudeAgentOptions(
    api_key=api_key,
    settings_path=".claude/settings.json",
    system_prompt="""
    You are a specialized agent for retail data analysis.
    Always provide data-driven insights and cite your sources.
    """
)
```

### Serialize/Deserialize Options

```python
# Serialize to dict
options_dict = options.to_dict()

# Save to JSON
import json
with open("agent_config.json", "w") as f:
    json.dump(options_dict, f, indent=2)

# Restore from dict
options_restored = ClaudeAgentOptions.from_dict(
    data=options_dict,
    api_key=api_key  # API key not serialized for security
)
```

---

## API Endpoint Usage

The orchestrator API now has a `/task/with-options` endpoint:

```bash
# Test the endpoint
curl -X POST http://localhost:8000/task/with-options \
  -H "Content-Type: application/json" \
  -d '{
    "task": "List all available MCP tools",
    "enable_mcp_servers": true,
    "max_turns": 10
  }'
```

Response:

```json
{
  "task": "List all available MCP tools",
  "result": "...",
  "status": "completed",
  "tool_calls": 0,
  "turns": 1,
  "mcp_servers_used": ["computer-use"],
  "error": null
}
```

---

## Testing

Run the test suite:

```bash
# Test ClaudeAgentOptions functionality
python test_claude_options.py
```

Expected output:

```
============================================================
   CLAUDE AGENT OPTIONS TEST SUITE
============================================================

============================================================
  TEST 1: Create ClaudeAgentOptions
============================================================
✓ Options created
  - Model: claude-sonnet-4-20250514
  - MCP Servers: 2
  - Max Turns: 25
...

============================================================
   TEST RESULTS
============================================================
✅ PASS  create_options
✅ PASS  query_function
✅ PASS  client_conversation
✅ PASS  compatibility

============================================================
  ✅ ALL TESTS PASSED
============================================================
```

---

## Comparison: ClaudeAgentOptions vs Direct DynamicAgent

### Before (Direct DynamicAgent):

```python
from orchestrator.agent_runner import DynamicAgent

agent = DynamicAgent(
    anthropic_api_key=api_key,
    settings_path=".claude/settings.json",
    model="claude-sonnet-4-20250514"
)

result = await agent.execute_task(task="...", max_turns=25)
```

### After (ClaudeAgentOptions):

```python
from orchestrator.claude_options import ClaudeAgentOptions, query

options = ClaudeAgentOptions(
    api_key=api_key,
    settings_path=".claude/settings.json",
    model="claude-sonnet-4-20250514",
    max_turns=25
)

result = await query(task="...", options=options)
```

**Benefits**:
- ✅ More configuration options (allowed_tools, system_prompt, permission_mode)
- ✅ Compatible with official SDK structure
- ✅ Easier to serialize/deserialize
- ✅ Built-in conversation client (ClaudeAgentClient)
- ✅ Better documentation and type hints

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         ClaudeAgentOptions (Wrapper Layer)              │
│  - ClaudeAgentOptions dataclass                         │
│  - query() function                                     │
│  - ClaudeAgentClient class                              │
│  - McpServerConfig                                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│      DynamicAgent (Implementation Layer)                │
│  - MCPClient (MCP discovery & tool calling)             │
│  - DynamicAgent (Anthropic API integration)             │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌───▼────┐ ┌───▼────┐
    │MCP      │ │MCP     │ │MCP     │
    │Server 1 │ │Server 2│ │Server 3│
    └─────────┘ └────────┘ └────────┘
```

---

## Migration Path to Official SDK

If/when you want to migrate to the official `claude-agent-sdk`:

1. **Install official SDK**:
   ```bash
   pip install claude-agent-sdk
   ```

2. **Minimal code changes**:
   ```python
   # Change import
   # from orchestrator.claude_options import ClaudeAgentOptions, query
   from claude import ClaudeAgentOptions, query  # Official SDK

   # Rest of code stays the same!
   options = ClaudeAgentOptions(...)
   result = await query(task="...", options=options)
   ```

3. **Our wrapper provides**:
   - Same parameter names
   - Same data structures
   - Same function signatures
   - Easy transition path

---

## FAQ

### Q: Should I use ClaudeAgentOptions or DynamicAgent directly?

**A:** Use `ClaudeAgentOptions` for new code. It provides:
- More configuration options
- Better compatibility with official SDK patterns
- Easier serialization/deserialization
- Conversation client support

### Q: Does this use the real claude-agent-sdk?

**A:** No, this is a wrapper around our custom implementation. However, it matches the official SDK's API structure, making future migration easy.

### Q: Can I use both approaches in the same project?

**A:** Yes! Both endpoints are available:
- `/task/dynamic` - Uses `DynamicAgent` directly
- `/task/with-options` - Uses `ClaudeAgentOptions` wrapper

### Q: How do I filter tools to a specific subset?

**A:**
```python
options = ClaudeAgentOptions(
    api_key=api_key,
    settings_path=".claude/settings.json",
    allowed_tools=["get_products", "get_inventory"]  # Only these tools
)
```

### Q: How do I add a new MCP server?

**A:** Just add it to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "existing-server": {...},
    "new-skill": {
      "httpUrl": "https://new-skill.example.com/mcp",
      "enabled": true,
      "description": "My new skill"
    }
  }
}
```

No code changes needed!

---

## Next Steps

✅ **Phase 1 Complete**: ClaudeAgentOptions wrapper implemented

🔜 **Phase 2**: Expose computer use tools as MCP server
- Create `container/mcp_server.py`
- Implement MCP endpoints (GET /mcp/tools, POST /mcp/call-tool)
- Test with ClaudeAgentOptions

---

**Created**: 2026-02-09
**Status**: ✅ Ready for Use
**Compatibility**: Official claude-agent-sdk API structure
