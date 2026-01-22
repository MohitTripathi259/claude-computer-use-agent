"""
Claude Computer-Use Agent package.

This package provides the Claude agent with computer-use capabilities
using Claude Agent SDK (ClaudeSDKClient + ClaudeAgentOptions).

The agent can:
- Execute bash commands
- Control a browser (navigate, click, type)
- Take screenshots
- Read/write files
- Interact with the desktop
"""

from .computer_use_agent import ComputerUseAgent
from .config import config, AgentConfig
from .tools import (
    ALLOWED_TOOLS,
    TOOL_DEFINITIONS,
    COMPUTER_USE_MCP_SERVER,
    set_reasoning_callback,
    set_reasoning_enabled,
)

__all__ = [
    # Agent
    'ComputerUseAgent',
    # Config
    'config',
    'AgentConfig',
    # Tools
    'ALLOWED_TOOLS',
    'TOOL_DEFINITIONS',
    'COMPUTER_USE_MCP_SERVER',
    'set_reasoning_callback',
    'set_reasoning_enabled',
]
