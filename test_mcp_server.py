#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Computer Use MCP Server.

Tests:
1. MCP server health check
2. tools/list - List available tools
3. tools/call - Execute bash tool
4. Verify tool schemas

Run this AFTER starting the MCP server:
    cd container
    python mcp_server.py

Then in another terminal:
    python test_mcp_server.py
"""

import asyncio
import sys
from pathlib import Path
import httpx
import json

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def test_health_check():
    """Test 1: MCP server health check."""
    print_section("TEST 1: Health Check")

    url = "http://localhost:8081/health"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                print(f"✓ MCP server is healthy")
                print(f"  - Status: {data.get('status')}")
                print(f"  - Tools available: {data.get('tools_available')}")
                print(f"  - Browser initialized: {data.get('browser_initialized')}")
                return True
            else:
                print(f"✗ Health check failed: HTTP {response.status_code}")
                return False

    except httpx.ConnectError:
        print(f"✗ Cannot connect to MCP server at {url}")
        print(f"  Make sure the server is running:")
        print(f"    cd container")
        print(f"    python mcp_server.py")
        return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False


async def test_tools_list():
    """Test 2: tools/list - List available tools."""
    print_section("TEST 2: tools/list - List Available Tools")

    url = "http://localhost:8081/"

    # JSON-RPC 2.0 request for tools/list
    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()

                if "result" in data:
                    tools = data["result"].get("tools", [])
                    print(f"✓ tools/list successful")
                    print(f"  - Total tools: {len(tools)}")

                    for i, tool in enumerate(tools, 1):
                        print(f"\n  Tool {i}: {tool['name']}")
                        print(f"    Description: {tool['description'][:80]}...")
                        print(f"    Input schema: {tool['inputSchema']['type']}")

                        # Count required params
                        required = tool['inputSchema'].get('required', [])
                        print(f"    Required params: {', '.join(required) if required else 'none'}")

                    return True
                else:
                    print(f"✗ No result in response: {data}")
                    return False

            else:
                print(f"✗ tools/list failed: HTTP {response.status_code}")
                print(f"  Response: {response.text}")
                return False

    except Exception as e:
        print(f"✗ tools/list error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tools_call_bash():
    """Test 3: tools/call - Execute bash tool."""
    print_section("TEST 3: tools/call - Execute bash_20250124 Tool")

    url = "http://localhost:8081/"

    # JSON-RPC 2.0 request to call bash tool
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "bash_20250124",
            "arguments": {
                "command": "echo 'Hello from MCP bash tool!' && pwd",
                "timeout": 30
            }
        },
        "id": 2
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()

                if "result" in data:
                    content = data["result"].get("content", [])
                    print(f"✓ tools/call successful")
                    print(f"  - Content blocks: {len(content)}")

                    for block in content:
                        print(f"\n  Block type: {block.get('type')}")
                        if block.get('type') == 'text':
                            print(f"  Text output:")
                            print("  " + "\n  ".join(block.get('text', '').split('\n')))

                    return True
                elif "error" in data:
                    print(f"✗ tools/call returned error:")
                    print(f"  Code: {data['error'].get('code')}")
                    print(f"  Message: {data['error'].get('message')}")
                    return False
                else:
                    print(f"✗ Unexpected response: {data}")
                    return False

            else:
                print(f"✗ tools/call failed: HTTP {response.status_code}")
                print(f"  Response: {response.text}")
                return False

    except Exception as e:
        print(f"✗ tools/call error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tools_call_text_editor():
    """Test 4: tools/call - Execute text_editor tool."""
    print_section("TEST 4: tools/call - Execute text_editor_20250728 Tool")

    url = "http://localhost:8081/"

    # First, create a test file
    print("\n[Step 1] Creating test file...")
    create_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "text_editor_20250728",
            "arguments": {
                "command": "create",
                "path": "/workspace/mcp_test.txt",
                "file_text": "Hello from MCP text editor!\nThis is a test file.\n"
            }
        },
        "id": 3
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create file
            response = await client.post(url, json=create_request)

            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    print("✓ File created successfully")
                else:
                    print(f"✗ File creation failed: {data}")
                    return False
            else:
                print(f"✗ File creation failed: HTTP {response.status_code}")
                return False

            # Read file back
            print("\n[Step 2] Reading file back...")
            read_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "text_editor_20250728",
                    "arguments": {
                        "command": "view",
                        "path": "/workspace/mcp_test.txt"
                    }
                },
                "id": 4
            }

            response = await client.post(url, json=read_request)

            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    content = data["result"].get("content", [])
                    print("✓ File read successfully")

                    for block in content:
                        if block.get('type') == 'text':
                            print(f"\n  File contents:")
                            print("  " + "\n  ".join(block.get('text', '').split('\n')))

                    return True
                else:
                    print(f"✗ File read failed: {data}")
                    return False
            else:
                print(f"✗ File read failed: HTTP {response.status_code}")
                return False

    except Exception as e:
        print(f"✗ text_editor test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_with_mcp_client():
    """Test 5: Integration with MCPClient from agent_runner."""
    print_section("TEST 5: Integration with MCPClient")

    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent))

    try:
        from orchestrator.agent_runner import MCPClient

        print("\n[Step 1] Creating MCPClient...")
        client = MCPClient(".claude/settings.json")

        print("[Step 2] Connecting to MCP servers...")
        client.connect_to_servers()

        print(f"✓ MCPClient connected")
        print(f"  - Servers: {len(client.servers)}")
        print(f"  - Total tools: {len(client.all_tools)}")

        for server_name, server in client.servers.items():
            print(f"\n  Server: {server_name}")
            print(f"    URL: {server.url}")
            print(f"    Tools: {len(server.tools or [])}")

            if server.tools:
                print(f"    Tool names:")
                for tool in server.tools:
                    print(f"      - {tool['name']}")

        return len(client.all_tools) > 0

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("   COMPUTER USE MCP SERVER TEST SUITE")
    print("=" * 70)
    print(f"Working directory: {Path.cwd()}")
    print(f"\nMCP Server URL: http://localhost:8081")
    print(f"Make sure the server is running first:")
    print(f"  cd container")
    print(f"  python mcp_server.py")

    results = {}

    # Test 1: Health check
    results["health_check"] = asyncio.run(test_health_check())

    if not results["health_check"]:
        print("\n" + "=" * 70)
        print("  ⚠️  STOPPING: MCP Server not running")
        print("=" * 70)
        print("\nPlease start the MCP server first:")
        print("  cd container")
        print("  python mcp_server.py")
        return 1

    # Test 2: tools/list
    results["tools_list"] = asyncio.run(test_tools_list())

    # Test 3: tools/call (bash)
    results["tools_call_bash"] = asyncio.run(test_tools_call_bash())

    # Test 4: tools/call (text_editor)
    results["tools_call_text_editor"] = asyncio.run(test_tools_call_text_editor())

    # Test 5: Integration
    results["integration"] = asyncio.run(test_integration_with_mcp_client())

    # Summary
    print("\n" + "=" * 70)
    print("   TEST RESULTS")
    print("=" * 70)

    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIPPED"

        print(f"{status}  {test_name}")

    all_passed = all(r is True for r in results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ ALL TESTS PASSED")
        print("\n  Next steps:")
        print("    1. MCP server is working correctly")
        print("    2. Tools are discoverable via MCP protocol")
        print("    3. Ready to test with DynamicAgent")
        print("\n  Try running:")
        print("    python test_dynamic_agent.py")
    else:
        print("  ❌ SOME TESTS FAILED")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
