"""
Bash Command Execution Tool.

Executes shell commands in the container environment and returns
stdout, stderr, and return code.
"""

import asyncio
import os
import shlex
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Maximum output size to prevent memory issues
MAX_OUTPUT_SIZE = 100000  # 100KB


async def execute_bash(
    command: str,
    timeout: int = 120,
    working_dir: Optional[str] = "/workspace"
) -> Dict:
    """
    Execute a bash command and return the result.

    Args:
        command: The bash command to execute
        timeout: Maximum execution time in seconds (default: 120)
        working_dir: Working directory for command execution (default: /workspace)

    Returns:
        Dict with keys:
        - stdout: Standard output (string)
        - stderr: Standard error (string)
        - return_code: Process return code (int)
    """
    logger.info(f"Executing: {command[:200]}{'...' if len(command) > 200 else ''}")

    # Validate working directory
    if working_dir and not os.path.isdir(working_dir):
        os.makedirs(working_dir, exist_ok=True)

    try:
        # Create subprocess
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
            env={
                **os.environ,
                "HOME": "/root",
                "USER": "root",
                "TERM": "xterm-256color"
            }
        )

        try:
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # Kill the process if it times out
            process.kill()
            await process.wait()

            logger.warning(f"Command timed out after {timeout}s: {command[:100]}")
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "return_code": -1
            }

        # Decode output
        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")

        # Truncate if too large
        if len(stdout_str) > MAX_OUTPUT_SIZE:
            stdout_str = stdout_str[:MAX_OUTPUT_SIZE] + f"\n\n[Output truncated at {MAX_OUTPUT_SIZE} bytes]"
        if len(stderr_str) > MAX_OUTPUT_SIZE:
            stderr_str = stderr_str[:MAX_OUTPUT_SIZE] + f"\n\n[Output truncated at {MAX_OUTPUT_SIZE} bytes]"

        return_code = process.returncode or 0

        logger.info(f"Command completed with return code: {return_code}")

        return {
            "stdout": stdout_str,
            "stderr": stderr_str,
            "return_code": return_code
        }

    except Exception as e:
        logger.error(f"Bash execution error: {e}")
        return {
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "return_code": -1
        }


async def execute_bash_interactive(
    command: str,
    input_text: Optional[str] = None,
    timeout: int = 120,
    working_dir: Optional[str] = "/workspace"
) -> Dict:
    """
    Execute a bash command with optional stdin input.

    Useful for commands that expect user input.

    Args:
        command: The bash command to execute
        input_text: Optional text to send to stdin
        timeout: Maximum execution time in seconds
        working_dir: Working directory for command execution

    Returns:
        Dict with stdout, stderr, and return_code
    """
    logger.info(f"Executing interactive: {command[:200]}")

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE if input_text else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )

        try:
            stdin_bytes = input_text.encode() if input_text else None
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin_bytes),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "return_code": -1
            }

        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "return_code": process.returncode or 0
        }

    except Exception as e:
        logger.error(f"Interactive bash error: {e}")
        return {
            "stdout": "",
            "stderr": str(e),
            "return_code": -1
        }
