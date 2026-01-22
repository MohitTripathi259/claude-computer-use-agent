"""
Tool Executor - Bridge between Claude and Container.

This module handles the execution of tool calls by forwarding them
to the container's API and formatting the responses for Claude.
"""

import httpx
import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime

from .config import config


def log(message: str, level: str = "INFO"):
    """Print formatted log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [EXECUTOR] [{level}] {message}")


class ToolExecutor:
    """
    Executes tool calls by forwarding them to the container.
    """

    def __init__(self, container_url: Optional[str] = None):
        """Initialize the tool executor."""
        self.container_url = container_url or config.container_url
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0))
        log(f"ToolExecutor initialized")
        log(f"  Container URL: {self.container_url}")

    async def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict:
        """Execute a tool call and return the result."""
        log("")
        log(f"╔══════════════════════════════════════════════════")
        log(f"║ TOOL EXECUTION REQUEST")
        log(f"║ Tool: {tool_name}")
        log(f"║ Input: {json.dumps(tool_input)[:200]}")
        log(f"╚══════════════════════════════════════════════════")

        try:
            if tool_name == "bash":
                log("→ Routing to: _execute_bash()")
                return await self._execute_bash(tool_input)

            elif tool_name == "computer":
                log("→ Routing to: _execute_computer()")
                return await self._execute_computer(tool_input)

            elif tool_name == "str_replace_editor":
                log("→ Routing to: _execute_editor()")
                return await self._execute_editor(tool_input)

            elif tool_name == "browser":
                log("→ Routing to: _execute_browser()")
                return await self._execute_browser(tool_input)

            else:
                log(f"ERROR: Unknown tool: {tool_name}", "ERROR")
                return {"error": f"Unknown tool: {tool_name}"}

        except httpx.RequestError as e:
            log(f"CONTAINER ERROR: {e}", "ERROR")
            return {"error": f"Container communication error: {str(e)}"}
        except Exception as e:
            log(f"EXECUTION ERROR: {e}", "ERROR")
            return {"error": f"Tool execution error: {str(e)}"}

    async def _execute_bash(self, input: Dict) -> Dict:
        """Execute bash command via container."""
        command = input.get("command", "")
        restart = input.get("restart", False)

        if restart:
            log("Bash restart requested (no-op)")
            return {"output": "Shell session restarted"}

        log(f"Executing bash command: {command[:100]}{'...' if len(command) > 100 else ''}")
        log(f"  POST {self.container_url}/tools/bash")

        response = await self.client.post(
            f"{self.container_url}/tools/bash",
            json={
                "command": command,
                "timeout": input.get("timeout", 120)
            }
        )
        log(f"  Response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()

        log(f"  Return code: {result.get('return_code')}")
        log(f"  Stdout length: {len(result.get('stdout', ''))} chars")
        log(f"  Stderr length: {len(result.get('stderr', ''))} chars")

        # Format output for Claude
        output_parts = []
        if result.get("stdout"):
            output_parts.append(result["stdout"])
        if result.get("stderr"):
            output_parts.append(f"STDERR:\n{result['stderr']}")

        return_code = result.get("return_code", 0)
        if return_code != 0:
            output_parts.append(f"\nExit code: {return_code}")

        output = "\n".join(output_parts) if output_parts else "(no output)"
        log(f"  Formatted output: {output[:100]}...")
        return {"output": output}

    async def _execute_computer(self, input: Dict) -> Dict:
        """Execute computer actions (screenshot, mouse, keyboard)."""
        action = input.get("action")
        log(f"Computer action: {action}")

        if action == "screenshot":
            log(f"  GET {self.container_url}/tools/screenshot")
            response = await self.client.get(f"{self.container_url}/tools/screenshot")
            log(f"  Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                log(f"  Screenshot error: {data['error']}", "ERROR")
                return {"error": data["error"]}

            log(f"  Screenshot captured: {data.get('width')}x{data.get('height')}")
            log(f"  Image data size: {len(data.get('image_base64', ''))} chars (base64)")

            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": data["image_base64"]
                }
            }

        elif action == "mouse_move":
            coordinate = input.get("coordinate", [0, 0])
            log(f"  Mouse move to: ({coordinate[0]}, {coordinate[1]})")
            return {"output": f"Moved mouse to ({coordinate[0]}, {coordinate[1]})"}

        elif action == "left_click":
            coordinate = input.get("coordinate", [0, 0])
            log(f"  Left click at: ({coordinate[0]}, {coordinate[1]})")
            log(f"  POST {self.container_url}/tools/browser (click)")
            response = await self.client.post(
                f"{self.container_url}/tools/browser",
                json={"action": "click", "params": {"x": coordinate[0], "y": coordinate[1]}}
            )
            response.raise_for_status()
            log(f"  Click executed")
            return {"output": f"Left clicked at ({coordinate[0]}, {coordinate[1]})"}

        elif action == "right_click":
            coordinate = input.get("coordinate", [0, 0])
            log(f"  Right click at: ({coordinate[0]}, {coordinate[1]})")
            response = await self.client.post(
                f"{self.container_url}/tools/browser",
                json={"action": "click", "params": {"x": coordinate[0], "y": coordinate[1], "button": "right"}}
            )
            response.raise_for_status()
            return {"output": f"Right clicked at ({coordinate[0]}, {coordinate[1]})"}

        elif action == "double_click":
            coordinate = input.get("coordinate", [0, 0])
            log(f"  Double click at: ({coordinate[0]}, {coordinate[1]})")
            for _ in range(2):
                await self.client.post(
                    f"{self.container_url}/tools/browser",
                    json={"action": "click", "params": {"x": coordinate[0], "y": coordinate[1]}}
                )
            return {"output": f"Double clicked at ({coordinate[0]}, {coordinate[1]})"}

        elif action == "left_click_drag":
            start = input.get("start_coordinate", [0, 0])
            end = input.get("coordinate", [0, 0])
            log(f"  Drag from ({start[0]}, {start[1]}) to ({end[0]}, {end[1]})")
            return {"output": f"Dragged from ({start[0]}, {start[1]}) to ({end[0]}, {end[1]})"}

        elif action == "type":
            text = input.get("text", "")
            log(f"  Typing text: {text[:50]}{'...' if len(text) > 50 else ''}")
            log(f"  POST {self.container_url}/tools/browser (type)")
            response = await self.client.post(
                f"{self.container_url}/tools/browser",
                json={"action": "type", "params": {"text": text}}
            )
            response.raise_for_status()
            return {"output": f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}"}

        elif action == "key":
            key = input.get("key", "")
            log(f"  Pressing key: {key}")
            key_mapping = {
                "Return": "Enter",
                "BackSpace": "Backspace",
                "space": " ",
            }
            mapped_key = key_mapping.get(key, key)
            response = await self.client.post(
                f"{self.container_url}/tools/browser",
                json={"action": "type", "params": {"text": mapped_key if len(mapped_key) == 1 else f"[{mapped_key}]"}}
            )
            return {"output": f"Pressed key: {key}"}

        elif action == "scroll":
            coordinate = input.get("coordinate", [960, 540])
            direction = input.get("direction", "down")
            amount = input.get("amount", 3)
            log(f"  Scroll {direction} by {amount} at ({coordinate[0]}, {coordinate[1]})")

            scroll_amount = amount * 100
            response = await self.client.post(
                f"{self.container_url}/tools/browser",
                json={"action": "scroll", "params": {"direction": direction, "amount": scroll_amount}}
            )
            response.raise_for_status()
            return {"output": f"Scrolled {direction} at ({coordinate[0]}, {coordinate[1]})"}

        elif action == "wait":
            log(f"  Waiting 1 second...")
            import asyncio
            await asyncio.sleep(1)
            return {"output": "Waited 1 second"}

        else:
            log(f"  Unknown action: {action}", "ERROR")
            return {"error": f"Unknown computer action: {action}"}

    async def _execute_editor(self, input: Dict) -> Dict:
        """Execute text editor operations."""
        command = input.get("command")
        path = input.get("path", "")

        if not path.startswith("/workspace"):
            path = f"/workspace/{path.lstrip('/')}"

        log(f"Editor command: {command}")
        log(f"  Path: {path}")

        if command == "view":
            log(f"  POST {self.container_url}/tools/file/read")
            response = await self.client.post(
                f"{self.container_url}/tools/file/read",
                json={"path": path}
            )

            if response.status_code == 404:
                log(f"  File not found: {path}", "WARN")
                return {"output": f"Error: File not found: {path}"}

            response.raise_for_status()
            data = response.json()
            content = data.get("content", "")
            log(f"  File read: {len(content)} chars")

            lines = content.split('\n')
            numbered = '\n'.join(f"{i+1:4d}\t{line}" for i, line in enumerate(lines))
            return {"output": numbered}

        elif command == "create":
            file_text = input.get("file_text", "")
            log(f"  Creating file with {len(file_text)} chars")
            log(f"  POST {self.container_url}/tools/file/write")
            response = await self.client.post(
                f"{self.container_url}/tools/file/write",
                json={"path": path, "content": file_text}
            )
            response.raise_for_status()
            log(f"  File created: {path}")
            return {"output": f"Created file: {path}"}

        elif command == "str_replace":
            log(f"  String replace in file")
            read_response = await self.client.post(
                f"{self.container_url}/tools/file/read",
                json={"path": path}
            )

            if read_response.status_code == 404:
                return {"output": f"Error: File not found: {path}"}

            read_response.raise_for_status()
            content = read_response.json().get("content", "")

            old_str = input.get("old_str", "")
            new_str = input.get("new_str", "")

            if old_str not in content:
                log(f"  String not found in file", "WARN")
                return {"output": f"Error: String not found in file:\n{old_str}"}

            count = content.count(old_str)
            if count > 1:
                log(f"  String appears {count} times", "WARN")
                return {"output": f"Error: String appears {count} times. Please provide more context to make it unique."}

            new_content = content.replace(old_str, new_str, 1)

            write_response = await self.client.post(
                f"{self.container_url}/tools/file/write",
                json={"path": path, "content": new_content}
            )
            write_response.raise_for_status()
            log(f"  Replacement done")
            return {"output": f"Successfully replaced text in {path}"}

        elif command == "insert":
            log(f"  Insert text into file")
            read_response = await self.client.post(
                f"{self.container_url}/tools/file/read",
                json={"path": path}
            )

            if read_response.status_code == 404:
                return {"output": f"Error: File not found: {path}"}

            read_response.raise_for_status()
            content = read_response.json().get("content", "")

            insert_line = input.get("insert_line", 0)
            new_str = input.get("new_str", "")

            lines = content.split('\n')

            if insert_line <= 0:
                lines.insert(0, new_str)
            elif insert_line >= len(lines):
                lines.append(new_str)
            else:
                lines.insert(insert_line, new_str)

            new_content = '\n'.join(lines)

            write_response = await self.client.post(
                f"{self.container_url}/tools/file/write",
                json={"path": path, "content": new_content}
            )
            write_response.raise_for_status()
            log(f"  Insert done at line {insert_line}")
            return {"output": f"Inserted text at line {insert_line} in {path}"}

        elif command == "undo_edit":
            log(f"  Undo not supported")
            return {"output": "Undo is not supported. Please manually revert changes."}

        else:
            log(f"  Unknown command: {command}", "ERROR")
            return {"error": f"Unknown editor command: {command}"}

    async def _execute_browser(self, input: Dict) -> Dict:
        """Execute browser-specific actions."""
        action = input.get("action")
        params = input.get("params", {})

        log(f"Browser action: {action}")
        log(f"  Params: {json.dumps(params)[:200]}")
        log(f"  POST {self.container_url}/tools/browser")

        response = await self.client.post(
            f"{self.container_url}/tools/browser",
            json={"action": action, "params": params}
        )
        log(f"  Response status: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            log(f"  Browser error: {data.get('error')}", "ERROR")
            return {"error": data.get("error", "Unknown error")}

        result_data = data.get("data", {})
        log(f"  Result keys: {list(result_data.keys())}")

        if "image_base64" in result_data:
            log(f"  Screenshot in response: {len(result_data['image_base64'])} chars")
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result_data["image_base64"]
                }
            }

        return {"output": json.dumps(result_data, indent=2)}

    async def health_check(self) -> bool:
        """Check if the container is healthy."""
        try:
            log(f"Health check: GET {self.container_url}/health")
            response = await self.client.get(f"{self.container_url}/health")
            healthy = response.status_code == 200
            log(f"  Result: {'healthy' if healthy else 'unhealthy'}")
            return healthy
        except Exception as e:
            log(f"  Health check failed: {e}", "ERROR")
            return False

    async def close(self):
        """Close the HTTP client."""
        log("Closing HTTP client...")
        await self.client.aclose()
        log("✓ ToolExecutor closed")
