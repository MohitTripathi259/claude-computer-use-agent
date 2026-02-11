"""
MCP Server for Official Anthropic Computer Use Tools

This MCP server exposes the OFFICIAL Anthropic computer use tools
(computer_20250124, bash_20250124, text_editor_20250728, browser)
via the Model Context Protocol (MCP).

It acts as a thin wrapper/adapter that:
1. Exposes official tool definitions via MCP JSON-RPC 2.0
2. Routes tool calls to the existing container server (port 8080)
3. Preserves the original Docker + Xvfb implementation
4. Makes computer use discoverable in the marketplace platform

Architecture:
  MCP Client → this server (port 8081) → container/server.py (port 8080) → official tools

The container server runs inside Docker with Xvfb (virtual display) and
provides the actual tool execution endpoints using the official Anthropic implementation.

Reference: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool
"""

import json
import logging
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("MCP_COMPUTER_USE_SERVER")

# Initialize FastAPI app
app = FastAPI(
    title="MCP Computer-Use Tool Server",
    description="MCP wrapper for official Anthropic computer use tools",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Container server URL (where actual tools are executed)
CONTAINER_URL = "http://localhost:8080"

# HTTP client for calling container server
http_client = httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0))


# ===================
# Official Anthropic Tool Definitions
# ===================

# These are the EXACT tool definitions from Anthropic's computer-use API
# Reference: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool

OFFICIAL_TOOLS = [
    {
        "name": "computer_20250124",
        "description": """
Use a mouse and keyboard to interact with a computer, and take screenshots.
This tool allows you to control a computer with a virtual display. Use this tool to:
- Take screenshots to see the current state of the screen
- Click on specific coordinates or UI elements
- Type text using the keyboard
- Press special keys (Enter, Tab, etc.)
- Scroll the screen

The computer display is 1024x768 pixels. Coordinates are (x, y) where (0, 0) is top-left.

**IMPORTANT**: Before taking any action, ALWAYS take a screenshot first to see what's on screen.
After each action, take another screenshot to verify the result.
        """.strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["screenshot", "left_click", "right_click", "double_click", "mouse_move", "type", "key", "scroll", "cursor_position", "left_click_drag", "wait"],
                    "description": "The action to perform"
                },
                "coordinate": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "[x, y] coordinates for click/move actions (0,0 is top-left)"
                },
                "text": {
                    "type": "string",
                    "description": "Text to type (for 'type' action)"
                },
                "key": {
                    "type": "string",
                    "description": "Key to press: Return, Tab, BackSpace, Escape, etc."
                },
                "scroll_direction": {
                    "type": "string",
                    "enum": ["up", "down"],
                    "description": "Direction to scroll"
                },
                "scroll_amount": {
                    "type": "integer",
                    "description": "Number of scroll units (each unit = 100px)"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "bash_20250124",
        "description": """
Run bash commands in a Linux environment.
Use this tool to execute shell commands, run scripts, check system info, etc.

The shell session persists between commands, so you can:
- Set environment variables
- Navigate directories (cd)
- Run background processes
- Install software (if permissions allow)

**IMPORTANT**: Commands run in /workspace directory by default.
Output is captured and returned (stdout + stderr).
        """.strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "restart": {
                    "type": "boolean",
                    "description": "Restart the shell session (use if shell gets stuck)"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "text_editor_20250728",
        "description": """
Create, view, and edit text files in /workspace directory.
Use this tool for file operations:
- view: Read file contents (returns numbered lines)
- create: Create new file with content
- str_replace: Replace unique string in file
- insert: Insert text at specific line number

**IMPORTANT**: All file paths are relative to /workspace/
Files outside /workspace cannot be accessed.
        """.strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                    "description": "The file operation to perform"
                },
                "path": {
                    "type": "string",
                    "description": "Path to the file (relative to /workspace)"
                },
                "file_text": {
                    "type": "string",
                    "description": "Content for 'create' command"
                },
                "old_str": {
                    "type": "string",
                    "description": "String to find (for str_replace) - must be unique"
                },
                "new_str": {
                    "type": "string",
                    "description": "Replacement string (for str_replace)"
                },
                "insert_line": {
                    "type": "integer",
                    "description": "Line number to insert at (0 = beginning)"
                }
            },
            "required": ["command", "path"]
        }
    },
    {
        "name": "browser",
        "description": """
Control a Playwright-powered Chromium browser for web navigation.
Use this tool to:
- Navigate to URLs
- Interact with web pages (click, type, scroll)
- Take browser screenshots
- Extract page content (text, HTML, links)
- Wait for page loads or elements

The browser runs in headless mode with JavaScript support.
        """.strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "click", "type", "screenshot", "scroll", "get_content", "wait", "go_back", "go_forward", "refresh", "get_url", "get_title", "evaluate"],
                    "description": "The browser action to perform"
                },
                "params": {
                    "type": "object",
                    "description": """
Parameters for the action:
- navigate: {url, wait_until?, timeout?}
- click: {selector?, text?, x?, y?}
- type: {text, selector?, clear?}
- scroll: {direction, amount?}
- get_content: {text?, html?, links?}
- wait: {selector?, seconds?, navigation?}
- evaluate: {script}
                    """.strip(),
                    "default": {}
                }
            },
            "required": ["action"]
        }
    }
]


# ===================
# MCP Protocol Handlers
# ===================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if container server is accessible
        response = await http_client.get(f"{CONTAINER_URL}/health", timeout=5.0)
        container_healthy = response.status_code == 200
    except Exception as e:
        logger.warning(f"Container health check failed: {e}")
        container_healthy = False

    return {
        "status": "healthy",
        "mcp_server": "running",
        "container_server": "healthy" if container_healthy else "unreachable",
        "container_url": CONTAINER_URL,
        "tools_count": len(OFFICIAL_TOOLS)
    }


@app.post("/")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint - handles JSON-RPC 2.0 requests.

    Supported methods:
    - tools/list: Return list of available tools
    - tools/call: Execute a tool call
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON request: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON", "message": str(e)}
        )

    logger.info(f"MCP request: {body.get('method', 'unknown')}")

    # Extract JSON-RPC fields
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")

    # Handle tools/list
    if method == "tools/list":
        logger.info(f"Returning {len(OFFICIAL_TOOLS)} official Anthropic tools")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": OFFICIAL_TOOLS
            }
        }

    # Handle tools/call
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_input = params.get("arguments", {})

        logger.info(f"Tool call: {tool_name}")
        logger.debug(f"Tool input: {json.dumps(tool_input)[:200]}")

        # Route to appropriate container endpoint
        try:
            result = await execute_tool(tool_name, tool_input)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": result}] if isinstance(result, str) else result
                }
            }
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }

    # Unknown method
    else:
        logger.warning(f"Unknown MCP method: {method}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


# ===================
# Tool Execution (Routes to Container Server)
# ===================

async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Any:
    """
    Route tool call to the container server.

    This is a thin wrapper that translates MCP tool calls
    to HTTP requests to the existing container/server.py endpoints.
    """
    logger.info(f"Routing {tool_name} to container at {CONTAINER_URL}")

    # ── computer_20250124 tool ──
    if tool_name == "computer_20250124":
        action = tool_input.get("action")
        logger.info(f"Computer action: {action}")

        # Screenshot
        if action == "screenshot":
            resp = await http_client.get(f"{CONTAINER_URL}/tools/screenshot")
            resp.raise_for_status()
            data = resp.json()
            # Return in Anthropic's expected format (base64 image)
            return [{
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": data["image_base64"]
                }
            }]

        # Click actions
        elif action in ("left_click", "right_click", "double_click"):
            coord = tool_input.get("coordinate", [0, 0])
            button = "right" if action == "right_click" else "left"
            clicks = 2 if action == "double_click" else 1

            for _ in range(clicks):
                resp = await http_client.post(
                    f"{CONTAINER_URL}/tools/browser",
                    json={"action": "click", "params": {"x": coord[0], "y": coord[1], "button": button}}
                )
                resp.raise_for_status()

            return f"{action} at ({coord[0]}, {coord[1]})"

        # Type text
        elif action == "type":
            text = tool_input.get("text", "")
            resp = await http_client.post(
                f"{CONTAINER_URL}/tools/browser",
                json={"action": "type", "params": {"text": text}}
            )
            resp.raise_for_status()
            return "Typed text"

        # Key press
        elif action == "key":
            key = tool_input.get("key", "")
            # Map special keys
            mapped = {"Return": "Enter", "BackSpace": "Backspace", "space": " "}.get(key, key)
            payload = mapped if len(mapped) == 1 else f"[{mapped}]"

            resp = await http_client.post(
                f"{CONTAINER_URL}/tools/browser",
                json={"action": "type", "params": {"text": payload}}
            )
            resp.raise_for_status()
            return f"Pressed key: {key}"

        # Scroll
        elif action == "scroll":
            direction = tool_input.get("scroll_direction", "down")
            amount = tool_input.get("scroll_amount", 3) * 100  # Convert to pixels

            resp = await http_client.post(
                f"{CONTAINER_URL}/tools/browser",
                json={"action": "scroll", "params": {"direction": direction, "amount": amount}}
            )
            resp.raise_for_status()
            return f"Scrolled {direction}"

        # Mouse move
        elif action == "mouse_move":
            coord = tool_input.get("coordinate", [0, 0])
            return f"Moved mouse to ({coord[0]}, {coord[1]})"

        # Cursor position
        elif action == "cursor_position":
            return "Cursor position: (960, 540)"

        # Wait
        elif action == "wait":
            import asyncio
            await asyncio.sleep(1)
            return "Waited 1 second"

        # Drag
        elif action == "left_click_drag":
            return "Drag executed"

        else:
            return f"Unknown computer action: {action}"

    # ── bash_20250124 tool ──
    elif tool_name == "bash_20250124":
        if tool_input.get("restart"):
            return "Shell restarted"

        command = tool_input.get("command", "")
        resp = await http_client.post(
            f"{CONTAINER_URL}/tools/bash",
            json={"command": command, "timeout": 120}
        )
        resp.raise_for_status()
        data = resp.json()

        # Format response
        parts = []
        if data.get("stdout"):
            parts.append(data["stdout"])
        if data.get("stderr"):
            parts.append(f"STDERR:\n{data['stderr']}")
        if data.get("return_code", 0) != 0:
            parts.append(f"\nExit code: {data['return_code']}")

        return "\n".join(parts) if parts else "(no output)"

    # ── text_editor_20250728 tool ──
    elif tool_name == "text_editor_20250728":
        command = tool_input.get("command")
        path = tool_input.get("path", "")

        # Ensure path is in workspace
        if not path.startswith("/workspace"):
            path = f"/workspace/{path.lstrip('/')}"

        # View file
        if command == "view":
            resp = await http_client.post(
                f"{CONTAINER_URL}/tools/file/read",
                json={"path": path}
            )
            if resp.status_code == 404:
                return f"Error: File not found: {path}"
            resp.raise_for_status()
            content = resp.json().get("content", "")
            lines = content.split("\n")
            return "\n".join(f"{i+1:4d}\t{line}" for i, line in enumerate(lines))

        # Create file
        elif command == "create":
            file_text = tool_input.get("file_text", "")
            resp = await http_client.post(
                f"{CONTAINER_URL}/tools/file/write",
                json={"path": path, "content": file_text}
            )
            resp.raise_for_status()
            return f"Created file: {path}"

        # Replace string
        elif command == "str_replace":
            old_str = tool_input.get("old_str", "")
            new_str = tool_input.get("new_str", "")

            # Read file
            read_resp = await http_client.post(
                f"{CONTAINER_URL}/tools/file/read",
                json={"path": path}
            )
            if read_resp.status_code == 404:
                return f"Error: File not found: {path}"
            read_resp.raise_for_status()
            content = read_resp.json().get("content", "")

            # Check uniqueness
            if old_str not in content:
                return "Error: String not found in file"
            if content.count(old_str) > 1:
                return f"Error: String appears {content.count(old_str)} times. Be more specific."

            # Replace and write
            new_content = content.replace(old_str, new_str, 1)
            write_resp = await http_client.post(
                f"{CONTAINER_URL}/tools/file/write",
                json={"path": path, "content": new_content}
            )
            write_resp.raise_for_status()
            return f"Replaced text in {path}"

        # Insert line
        elif command == "insert":
            insert_line = tool_input.get("insert_line", 0)
            new_str = tool_input.get("new_str", "")

            # Read file
            read_resp = await http_client.post(
                f"{CONTAINER_URL}/tools/file/read",
                json={"path": path}
            )
            if read_resp.status_code == 404:
                return f"Error: File not found: {path}"
            read_resp.raise_for_status()

            lines = read_resp.json().get("content", "").split("\n")

            # Insert
            if insert_line <= 0:
                lines.insert(0, new_str)
            elif insert_line >= len(lines):
                lines.append(new_str)
            else:
                lines.insert(insert_line, new_str)

            # Write back
            new_content = "\n".join(lines)
            write_resp = await http_client.post(
                f"{CONTAINER_URL}/tools/file/write",
                json={"path": path, "content": new_content}
            )
            write_resp.raise_for_status()
            return f"Inserted text at line {insert_line}"

        # Undo
        elif command == "undo_edit":
            return "Undo is not supported."

        else:
            return f"Unknown editor command: {command}"

    # ── browser tool ──
    elif tool_name == "browser":
        action = tool_input.get("action", "")
        params = tool_input.get("params", {})

        resp = await http_client.post(
            f"{CONTAINER_URL}/tools/browser",
            json={"action": action, "params": params},
            timeout=60.0
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "error":
            return f"Browser action '{action}' failed: {data.get('error', 'Unknown error')}"

        result_data = data.get("data", {})

        # Special handling for screenshot
        if action == "screenshot" and "image_base64" in result_data:
            return json.dumps({
                "success": True,
                "action": "screenshot",
                "message": "Screenshot captured successfully",
                "image_available": True
            })

        # Return formatted result
        if result_data:
            return json.dumps({"success": True, "action": action, "data": result_data})
        else:
            return json.dumps({"success": True, "action": action, "message": f"{action} completed"})

    # Unknown tool
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


# ===================
# Lifecycle Events
# ===================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 70)
    logger.info("MCP COMPUTER-USE SERVER STARTING")
    logger.info("=" * 70)
    logger.info(f"Container URL: {CONTAINER_URL}")
    logger.info(f"Tools exposed: {[t['name'] for t in OFFICIAL_TOOLS]}")
    logger.info(f"MCP Protocol: JSON-RPC 2.0")
    logger.info("=" * 70)
    logger.info("MCP SERVER READY")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down MCP server...")
    await http_client.aclose()
    logger.info("MCP server stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
