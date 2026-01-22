"""
MCP Tool Server for Computer-Use Agent.

This MCP server exposes computer-use tools (computer, bash, browser, str_replace_editor)
to the Claude Agent SDK. It proxies tool calls to the container's HTTP API.

Run as: python -m agent.mcp_tool_server
"""

import os
import sys
import json
import asyncio
import logging
from typing import Any, Dict

import httpx

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP_TOOL_SERVER")

# Container URL from environment
CONTAINER_URL = os.getenv("CONTAINER_URL", "http://localhost:8080")

# HTTP client for container communication
http_client = None


async def get_client():
    """Get or create HTTP client."""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0))
    return http_client


# ===================
# Tool Implementations
# ===================

async def execute_computer(action: str, **kwargs) -> Dict[str, Any]:
    """Execute computer actions (screenshot, mouse, keyboard)."""
    client = await get_client()
    logger.info(f"Computer action: {action}")

    if action == "screenshot":
        response = await client.get(f"{CONTAINER_URL}/tools/screenshot")
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return {"error": data["error"]}

        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": data["image_base64"]
            }
        }

    elif action in ("left_click", "right_click", "double_click"):
        coordinate = kwargs.get("coordinate", [0, 0])
        button = "right" if action == "right_click" else "left"

        if action == "double_click":
            for _ in range(2):
                await client.post(
                    f"{CONTAINER_URL}/tools/browser",
                    json={"action": "click", "params": {"x": coordinate[0], "y": coordinate[1]}}
                )
        else:
            await client.post(
                f"{CONTAINER_URL}/tools/browser",
                json={"action": "click", "params": {"x": coordinate[0], "y": coordinate[1], "button": button}}
            )
        return {"output": f"{action} at ({coordinate[0]}, {coordinate[1]})"}

    elif action == "type":
        text = kwargs.get("text", "")
        await client.post(
            f"{CONTAINER_URL}/tools/browser",
            json={"action": "type", "params": {"text": text}}
        )
        return {"output": f"Typed: {text[:50]}..."}

    elif action == "key":
        key = kwargs.get("key", "")
        key_mapping = {"Return": "Enter", "BackSpace": "Backspace", "space": " "}
        mapped_key = key_mapping.get(key, key)
        await client.post(
            f"{CONTAINER_URL}/tools/browser",
            json={"action": "type", "params": {"text": f"[{mapped_key}]" if len(mapped_key) > 1 else mapped_key}}
        )
        return {"output": f"Pressed key: {key}"}

    elif action == "scroll":
        coordinate = kwargs.get("coordinate", [960, 540])
        direction = kwargs.get("direction", "down")
        amount = kwargs.get("amount", 3) * 100

        await client.post(
            f"{CONTAINER_URL}/tools/browser",
            json={"action": "scroll", "params": {"direction": direction, "amount": amount}}
        )
        return {"output": f"Scrolled {direction}"}

    elif action == "mouse_move":
        coordinate = kwargs.get("coordinate", [0, 0])
        return {"output": f"Moved mouse to ({coordinate[0]}, {coordinate[1]})"}

    elif action == "wait":
        await asyncio.sleep(1)
        return {"output": "Waited 1 second"}

    else:
        return {"error": f"Unknown computer action: {action}"}


async def execute_bash(command: str, timeout: int = 120, restart: bool = False) -> Dict[str, Any]:
    """Execute bash command."""
    client = await get_client()
    logger.info(f"Bash command: {command[:100]}")

    if restart:
        return {"output": "Shell session restarted"}

    response = await client.post(
        f"{CONTAINER_URL}/tools/bash",
        json={"command": command, "timeout": timeout}
    )
    response.raise_for_status()
    result = response.json()

    output_parts = []
    if result.get("stdout"):
        output_parts.append(result["stdout"])
    if result.get("stderr"):
        output_parts.append(f"STDERR:\n{result['stderr']}")

    return_code = result.get("return_code", 0)
    if return_code != 0:
        output_parts.append(f"\nExit code: {return_code}")

    return {"output": "\n".join(output_parts) if output_parts else "(no output)"}


async def execute_browser(action: str, params: Dict = None) -> Dict[str, Any]:
    """Execute browser action."""
    client = await get_client()
    params = params or {}
    logger.info(f"Browser action: {action}")

    response = await client.post(
        f"{CONTAINER_URL}/tools/browser",
        json={"action": action, "params": params}
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") == "error":
        return {"error": data.get("error", "Unknown error")}

    result_data = data.get("data", {})

    if "image_base64" in result_data:
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": result_data["image_base64"]
            }
        }

    return {"output": json.dumps(result_data, indent=2)}


async def execute_editor(command: str, path: str, **kwargs) -> Dict[str, Any]:
    """Execute text editor operations."""
    client = await get_client()
    logger.info(f"Editor command: {command} on {path}")

    # Ensure path is in workspace
    if not path.startswith("/workspace"):
        path = f"/workspace/{path.lstrip('/')}"

    if command == "view":
        response = await client.post(
            f"{CONTAINER_URL}/tools/file/read",
            json={"path": path}
        )

        if response.status_code == 404:
            return {"output": f"Error: File not found: {path}"}

        response.raise_for_status()
        content = response.json().get("content", "")
        lines = content.split('\n')
        numbered = '\n'.join(f"{i+1:4d}\t{line}" for i, line in enumerate(lines))
        return {"output": numbered}

    elif command == "create":
        file_text = kwargs.get("file_text", "")
        response = await client.post(
            f"{CONTAINER_URL}/tools/file/write",
            json={"path": path, "content": file_text}
        )
        response.raise_for_status()
        return {"output": f"Created file: {path}"}

    elif command == "str_replace":
        # Read current content
        read_response = await client.post(
            f"{CONTAINER_URL}/tools/file/read",
            json={"path": path}
        )

        if read_response.status_code == 404:
            return {"output": f"Error: File not found: {path}"}

        read_response.raise_for_status()
        content = read_response.json().get("content", "")

        old_str = kwargs.get("old_str", "")
        new_str = kwargs.get("new_str", "")

        if old_str not in content:
            return {"output": f"Error: String not found in file"}

        count = content.count(old_str)
        if count > 1:
            return {"output": f"Error: String appears {count} times. Please provide more context."}

        new_content = content.replace(old_str, new_str, 1)

        write_response = await client.post(
            f"{CONTAINER_URL}/tools/file/write",
            json={"path": path, "content": new_content}
        )
        write_response.raise_for_status()
        return {"output": f"Successfully replaced text in {path}"}

    elif command == "insert":
        read_response = await client.post(
            f"{CONTAINER_URL}/tools/file/read",
            json={"path": path}
        )

        if read_response.status_code == 404:
            return {"output": f"Error: File not found: {path}"}

        read_response.raise_for_status()
        content = read_response.json().get("content", "")

        insert_line = kwargs.get("insert_line", 0)
        new_str = kwargs.get("new_str", "")

        lines = content.split('\n')
        if insert_line <= 0:
            lines.insert(0, new_str)
        elif insert_line >= len(lines):
            lines.append(new_str)
        else:
            lines.insert(insert_line, new_str)

        new_content = '\n'.join(lines)

        write_response = await client.post(
            f"{CONTAINER_URL}/tools/file/write",
            json={"path": path, "content": new_content}
        )
        write_response.raise_for_status()
        return {"output": f"Inserted text at line {insert_line}"}

    elif command == "undo_edit":
        return {"output": "Undo is not supported. Please manually revert changes."}

    else:
        return {"error": f"Unknown editor command: {command}"}


# ===================
# MCP Protocol Handler
# ===================

async def handle_tool_call(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming tool call from MCP."""
    logger.info(f"Tool call: {tool_name}")
    logger.info(f"Input: {json.dumps(tool_input)[:200]}")

    try:
        if tool_name == "computer":
            action = tool_input.get("action", "screenshot")
            return await execute_computer(action, **tool_input)

        elif tool_name == "bash":
            command = tool_input.get("command", "")
            return await execute_bash(command, tool_input.get("timeout", 120), tool_input.get("restart", False))

        elif tool_name == "browser":
            action = tool_input.get("action", "")
            params = tool_input.get("params", {})
            return await execute_browser(action, params)

        elif tool_name == "str_replace_editor":
            command = tool_input.get("command", "view")
            path = tool_input.get("path", "")
            return await execute_editor(command, path, **tool_input)

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except httpx.RequestError as e:
        logger.error(f"Container communication error: {e}")
        return {"error": f"Container communication error: {str(e)}"}
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return {"error": f"Tool execution error: {str(e)}"}


async def main():
    """
    Main MCP server loop.

    Reads JSON-RPC messages from stdin, processes tool calls,
    and writes responses to stdout.
    """
    logger.info(f"MCP Tool Server starting. Container URL: {CONTAINER_URL}")

    # Simple stdin/stdout JSON-RPC handler
    loop = asyncio.get_event_loop()

    while True:
        try:
            # Read line from stdin
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            # Parse JSON-RPC request
            request = json.loads(line.strip())
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "tools/call":
                tool_name = params.get("name", "")
                tool_input = params.get("arguments", {})
                result = await handle_tool_call(tool_name, tool_input)

                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }

            elif method == "tools/list":
                # Return available tools
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {"name": "computer", "description": "Computer control (screenshot, mouse, keyboard)"},
                            {"name": "bash", "description": "Execute bash commands"},
                            {"name": "browser", "description": "Web browser automation"},
                            {"name": "str_replace_editor", "description": "File operations"},
                        ]
                    }
                }

            elif method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "computer-use-mcp", "version": "1.0.0"}
                    }
                }

            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            # Write response to stdout
            print(json.dumps(response), flush=True)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")
            if request_id:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
