"""
Claude Computer-Use Agent.

Agent implementation using Claude Agent SDK (ClaudeSDKClient + ClaudeAgentOptions)
for computer-use capabilities in a containerized environment.

This follows the same pattern as the reference agent.py with:
1. ClaudeAgentOptions for configuration
2. Async streaming with receive_response()
3. MCP server for tool execution
4. ThinkingBlock support for approach/planning
"""

import os
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime

from .config import config
from .tools import (
    COMPUTER_USE_MCP_SERVER,
    ALLOWED_TOOLS,
    set_reasoning_callback,
    set_reasoning_enabled,
)

# Claude Agent SDK imports
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
    ThinkingBlock,
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger("COMPUTER_USE_AGENT")


def log(message: str, level: str = "INFO"):
    """Print formatted log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [AGENT] [{level}] {message}")


# ---------- UTILITY FUNCTIONS ----------

def extract_last_json_object(text: str) -> Optional[str]:
    """Extract the main response JSON object from output text."""
    json_objects = []
    i = 0
    while i < len(text):
        if text[i] == '{':
            depth = 0
            start = i
            for idx in range(i, len(text)):
                char = text[idx]
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        json_str = text[start:idx + 1]
                        json_objects.append(json_str)
                        i = idx
                        break
            else:
                break
        i += 1

    if not json_objects:
        return None

    # Priority 1: Find JSON with type field
    for json_str in reversed(json_objects):
        try:
            obj = json.loads(json_str)
            if isinstance(obj, dict):
                obj_type = obj.get("type")
                if obj_type in ("response", "result", "error"):
                    return json_str
        except json.JSONDecodeError:
            continue

    # Priority 2: Return largest valid JSON object
    valid_objects = []
    for json_str in json_objects:
        try:
            obj = json.loads(json_str)
            if isinstance(obj, dict):
                valid_objects.append((len(json_str), json_str))
        except json.JSONDecodeError:
            continue

    if valid_objects:
        valid_objects.sort(key=lambda x: x[0], reverse=True)
        return valid_objects[0][1]

    return json_objects[-1] if json_objects else None


class ComputerUseAgent:
    """
    Claude agent with computer-use capabilities using Claude Agent SDK.

    This agent can:
    - Execute bash commands
    - Control a browser (navigate, click, type)
    - Take screenshots
    - Read/write files
    - Interact with the desktop
    """

    def __init__(
        self,
        container_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize the computer-use agent."""
        log("=" * 60)
        log("INITIALIZING COMPUTER-USE AGENT (SDK VERSION)")
        log("=" * 60)

        self.api_key = api_key or config.anthropic_api_key
        if not self.api_key:
            log("ERROR: ANTHROPIC_API_KEY is required", "ERROR")
            raise ValueError("ANTHROPIC_API_KEY is required")

        log(f"API Key: {self.api_key[:20]}...{self.api_key[-10:]}")

        self.container_url = container_url or config.container_url
        log(f"Container URL: {self.container_url}")

        self.model = model or config.model
        log(f"Model: {self.model}")

        # Project root for SDK options
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Track conversation (for compatibility with orchestrator)
        self.conversation_history: List[Dict] = []

        log(f"✓ Tools configured: {ALLOWED_TOOLS}")
        log("=" * 60)
        log("AGENT INITIALIZATION COMPLETE")
        log("=" * 60)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        container_url = self.container_url
        return f"""You are a computer-use agent with access to a Linux computer with a desktop environment and browser.

## THINKING BLOCK (Your approach - shown to user)

In your thinking block, describe your approach:
- What you're about to do
- The steps you'll take
- What tools you'll use

## CAPABILITIES

- Execute bash commands (files are in /workspace)
- Control a web browser (navigate, click, type, scroll)
- Take screenshots to see what's on screen
- Read and write files
- Interact with the desktop via mouse/keyboard

## CONTAINER API (Use via curl in bash)

The computer container is available at: {container_url}

### SCREENSHOT - Take a screenshot of the desktop
```bash
curl -s {container_url}/tools/screenshot | jq -r '.image_base64' | base64 -d > /workspace/screenshot.png
```
This saves a PNG screenshot to /workspace/screenshot.png

### BROWSER NAVIGATE - Open a URL in the browser
```bash
curl -s -X POST {container_url}/tools/browser -H "Content-Type: application/json" -d '{{"action": "navigate", "params": {{"url": "https://example.com"}}}}'
```
**IMPORTANT**: After navigation, ALWAYS wait 3-5 seconds for the page to load before taking a screenshot:
```bash
sleep 5
```

### BROWSER SCREENSHOT - Take a screenshot of the browser
```bash
curl -s -X POST {container_url}/tools/browser -H "Content-Type: application/json" -d '{{"action": "screenshot"}}' | jq -r '.data.image_base64' | base64 -d > /workspace/browser_screenshot.png
```

### BROWSER GET CONTENT - Get page text content
```bash
curl -s -X POST {container_url}/tools/browser -H "Content-Type: application/json" -d '{{"action": "get_content", "params": {{"text": true}}}}'
```

## WORKFLOW

1. Take a screenshot using the container API to see the current state
2. Plan your actions step by step
3. Execute actions one at a time
4. After each action, take a screenshot to verify the result
5. If something doesn't work, try an alternative approach

## TOOLS AVAILABLE

1. **Bash** - Execute shell commands including curl to container API
2. **Read** - Read file contents
3. **Write** - Create/write files to /workspace

## IMPORTANT GUIDELINES

- ALWAYS take screenshots using the container API (curl to {container_url}/tools/screenshot)
- Save all files to /workspace directory (you have write access there)
- Use the browser API for web navigation (navigate, then screenshot)
- **CRITICAL**: After browser navigation, ALWAYS run `sleep 5` before taking a screenshot to allow the page to fully load
- Be methodical and verify each step with screenshots
- If you encounter an error, explain and try to fix it
- If a screenshot appears blank or incomplete, wait longer and retry

Always explain what you're doing and why."""

    def _get_mcp_server_config(self) -> Dict[str, Any]:
        """Get MCP server configuration for tool execution."""
        return {
            "computer_use": {
                "command": "python",
                "args": ["-m", "agent.mcp_tool_server"],
                "env": {
                    "CONTAINER_URL": self.container_url,
                    "PYTHONPATH": self.project_root,
                    "ANTHROPIC_API_KEY": self.api_key,
                },
            }
        }

    async def run(
        self,
        task: str,
        on_iteration: Optional[Callable[[int, str], None]] = None,
        send_approach_callback: Optional[Callable[[Dict], None]] = None
    ) -> str:
        """
        Run the agent on a task using Claude Agent SDK.

        The SDK handles the agentic loop internally - no max_iterations needed.

        Args:
            task: The task to execute
            on_iteration: Optional callback for tool execution updates
            send_approach_callback: Optional callback for approach/thinking output

        Returns:
            Final response string from the agent
        """
        start_time = time.time()
        correlation_id = f"AGENT-{uuid.uuid4().hex[:8].upper()}-{int(time.time())}"

        print("=" * 60)
        print(f"[AGENT] Correlation ID: {correlation_id}")
        logger.info(f"[{correlation_id}] New task received")

        # Enable reasoning for approach generation
        set_reasoning_enabled(True)
        print(f"[AGENT] Processing task: {task[:100]}...")
        logger.info(f"[{correlation_id}] Task: {task[:100]}...")

        # Add user message to history (for compatibility)
        self.conversation_history.append({
            "role": "user",
            "content": task
        })

        # Initialize Claude Agent SDK options
        print("[AGENT] Initializing Claude SDK Client...")
        logger.info(f"[{correlation_id}] Initializing SDK")

        options = ClaudeAgentOptions(
            cwd=self.project_root,
            setting_sources=["project"],
            allowed_tools=ALLOWED_TOOLS,
            mcp_servers=self._get_mcp_server_config(),
            permission_mode="bypassPermissions",  # Now works with non-root user in Docker
            system_prompt=self._get_system_prompt(),
            max_thinking_tokens=2048,  # Enable thinking for approach generation
        )

        client = ClaudeSDKClient(options=options)

        # Tracking variables
        accumulated_text = ""
        thinking_text = ""
        approach_sent = False
        chunk_count = 0
        message_count = 0
        tool_count = 0

        # Connect the client
        print("[AGENT] Connecting to Claude SDK...")
        await client.__aenter__()
        print("[AGENT] Connected successfully")
        logger.info(f"[{correlation_id}] Claude SDK connected")

        try:
            # Send the query
            print(f"[AGENT] Sending task to Claude...")
            await client.query(task)
            print("[AGENT] Task sent, receiving response stream...")

            # Receive the response stream (SDK handles agentic loop internally)
            async for message in client.receive_response():
                message_count += 1

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        # Handle thinking blocks - capture as approach
                        if isinstance(block, ThinkingBlock):
                            thinking_text += block.thinking
                            print(f"[THINKING] Captured thinking block (len={len(block.thinking)})")

                            # Send thinking as approach via callback (once)
                            if send_approach_callback and not approach_sent:
                                approach_sent = True
                                send_approach_callback({
                                    "type": "approach",
                                    "response": {
                                        "markdown": block.thinking
                                    }
                                })
                                print("[AGENT] Approach (from thinking) sent via callback")

                        # Handle text blocks
                        elif isinstance(block, TextBlock):
                            chunk_count += 1
                            text = block.text
                            accumulated_text += text

                            # Log text chunks
                            preview = text[:150].replace('\n', ' ')
                            if len(text) > 150:
                                preview += "..."
                            print(f"[AGENT CHUNK #{chunk_count}] Length={len(text)}, Preview: {preview}")

                        # Handle tool use blocks
                        elif hasattr(block, 'name'):
                            tool_count += 1
                            tool_name = block.name.replace('mcp__computer_use__', '')
                            print(f"[TOOL #{tool_count}] Executing: {tool_name}")
                            logger.info(f"[{correlation_id}] Tool invoked: {tool_name}")

                            if on_iteration:
                                on_iteration(tool_count, f"executing_{tool_name}")

                elif isinstance(message, ResultMessage):
                    print(f"[AGENT] Tool execution complete")
                    logger.info(f"[{correlation_id}] ResultMessage received")
                else:
                    msg_type = type(message).__name__
                    if msg_type != "SystemMessage":
                        print(f"[AGENT DEBUG] Message type: {msg_type}")

            print(f"[AGENT] Stream complete. Total messages: {message_count}, chunks: {chunk_count}")
            logger.info(f"[{correlation_id}] Response stream complete")

        except Exception as e:
            print(f"[AGENT ERROR] Task failed: {str(e)}")
            logger.exception(f"[{correlation_id}] Agent task failed")
            return f"Error: {str(e)}"

        finally:
            # Always close the client
            print("[AGENT] Closing Claude SDK connection...")
            try:
                await client.__aexit__(None, None, None)
                print("[AGENT] Connection closed")
            except:
                pass

        # Store response in conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": accumulated_text
        })

        # Parse response if JSON format expected
        print(f"[AGENT] Raw output length: {len(accumulated_text)}")
        logger.info(f"[{correlation_id}] Raw output length: {len(accumulated_text)}")

        # Try to extract structured response
        result_json = None
        json_str = extract_last_json_object(accumulated_text)
        if json_str:
            try:
                result_json = json.loads(json_str)
                print("[AGENT] Parsed JSON from output")
            except:
                pass

        elapsed = time.time() - start_time
        print(f"[AGENT] Completed in {elapsed:.2f}s")
        print(f"[AGENT] Tool calls: {tool_count}")
        print("=" * 60)
        logger.info(f"[{correlation_id}] Completed in {elapsed:.2f}s")

        # Return text response (or JSON markdown if structured)
        if result_json and "response" in result_json:
            return result_json.get("response", {}).get("markdown", accumulated_text)

        return accumulated_text or thinking_text or "Task completed."

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        log("Conversation history reset")

    def get_conversation_history(self) -> List[Dict]:
        """Get the current conversation history."""
        return self.conversation_history.copy()

    async def cleanup(self):
        """Clean up resources."""
        log("Cleaning up agent resources...")
        log("✓ ComputerUseAgent cleaned up")


# Re-export for compatibility
__all__ = [
    'ComputerUseAgent',
    'set_reasoning_callback',
    'set_reasoning_enabled',
]


async def main():
    """Run the agent with a sample task (for testing)."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is required")
        return

    agent = ComputerUseAgent()

    try:
        task = """
        Please do the following:
        1. Take a screenshot to see the current state
        2. Open a browser and navigate to https://example.com
        3. Take a screenshot of the page
        4. Tell me what you see on the page
        5. Create a file called /workspace/test.txt with a summary
        """

        print(f"Task: {task}\n")
        print("=" * 50)

        def on_iteration(num, status):
            print(f"  [Tool #{num}] {status}")

        result = await agent.run(task, on_iteration=on_iteration)

        print("=" * 50)
        print(f"\nFinal Result:\n{result}")

    finally:
        await agent.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
