"""
Computer-Use Tools Configuration.

Defines the MCP server configuration and allowed tools for the
Claude Computer-Use Agent using the Claude Agent SDK.
"""

import os
from typing import Dict, Any, List

# Container URL for tool execution
CONTAINER_URL = os.getenv("CONTAINER_URL", os.getenv("LOCAL_CONTAINER_URL", "http://localhost:8080"))

# ===================
# MCP Server Configuration
# ===================

# MCP Server that proxies tool calls to the container
COMPUTER_USE_MCP_SERVER: Dict[str, Any] = {
    "command": "python",
    "args": ["-m", "agent.mcp_tool_server"],
    "env": {
        "CONTAINER_URL": CONTAINER_URL,
        "PYTHONPATH": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    },
}

# Alternative: Direct HTTP-based tool execution (no MCP)
# This is used when running without MCP server
DIRECT_TOOLS_CONFIG = {
    "container_url": CONTAINER_URL,
    "tools": {
        "computer": {
            "endpoint": "/tools/screenshot",
            "actions": ["screenshot", "left_click", "right_click", "double_click",
                       "type", "key", "scroll", "mouse_move", "wait"]
        },
        "bash": {
            "endpoint": "/tools/bash",
        },
        "browser": {
            "endpoint": "/tools/browser",
            "actions": ["navigate", "click", "type", "screenshot", "scroll",
                       "get_content", "wait", "go_back", "go_forward", "refresh"]
        },
        "str_replace_editor": {
            "read_endpoint": "/tools/file/read",
            "write_endpoint": "/tools/file/write",
            "commands": ["view", "create", "str_replace", "insert", "undo_edit"]
        }
    }
}

# ===================
# Allowed Tools
# ===================

# Tools the agent is allowed to use
ALLOWED_TOOLS: List[str] = [
    "computer",           # Screenshot, mouse, keyboard
    "bash",               # Shell commands
    "browser",            # Web automation
    "str_replace_editor", # File operations
]

# Tool definitions for Claude (when not using MCP)
TOOL_DEFINITIONS = [
    {
        "type": "computer_20250124",
        "name": "computer",
        "display_width_px": int(os.getenv("DISPLAY_WIDTH", "1920")),
        "display_height_px": int(os.getenv("DISPLAY_HEIGHT", "1080")),
        "display_number": 1,
    },
    {
        "type": "bash_20250124",
        "name": "bash"
    },
    {
        "type": "text_editor_20250124",
        "name": "str_replace_editor"
    },
    {
        "name": "browser",
        "description": """Control a web browser for navigation and interaction.

Actions:
- navigate: Go to a URL. Params: {"url": "https://example.com"}
- click: Click element. Params: {"selector": "button.submit"} or {"x": 100, "y": 200} or {"text": "Click me"}
- type: Type text. Params: {"text": "hello", "selector": "#input"} (selector optional)
- screenshot: Take page screenshot. Params: {"full_page": false}
- scroll: Scroll page. Params: {"direction": "down", "amount": 500}
- get_content: Get page text/HTML. Params: {"text": true, "html": false, "links": false}
- wait: Wait for element or time. Params: {"selector": "#loaded"} or {"seconds": 2}
- go_back: Navigate back. No params.
- go_forward: Navigate forward. No params.
- refresh: Refresh page. No params.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "click", "type", "screenshot", "scroll",
                             "get_content", "wait", "go_back", "go_forward", "refresh"],
                    "description": "The browser action to perform"
                },
                "params": {
                    "type": "object",
                    "description": "Parameters for the action"
                }
            },
            "required": ["action"]
        }
    }
]

# ===================
# Reasoning Callbacks
# ===================

_reasoning_callback = None
_reasoning_enabled = True


def set_reasoning_callback(callback):
    """Set callback function for reasoning/thinking output."""
    global _reasoning_callback
    _reasoning_callback = callback


def set_reasoning_enabled(enabled: bool):
    """Enable or disable reasoning output."""
    global _reasoning_enabled
    _reasoning_enabled = enabled


def get_reasoning_callback():
    """Get the current reasoning callback."""
    return _reasoning_callback if _reasoning_enabled else None


def is_reasoning_enabled() -> bool:
    """Check if reasoning is enabled."""
    return _reasoning_enabled
