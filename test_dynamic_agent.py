#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Dynamic Agent with MCP support.

Tests:
1. Settings.json loads correctly
2. MCP client connects to servers
3. Tools are discovered
4. Agent can be initialized

Run: python test_dynamic_agent.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.agent_runner import DynamicAgent, MCPClient


def test_settings_file():
    """Test 1: Settings file exists and is valid."""
    print("\n" + "=" * 60)
    print("TEST 1: Settings File")
    print("=" * 60)

    settings_path = Path(".claude/settings.json")

    if not settings_path.exists():
        print(f"❌ FAIL: {settings_path} not found")
        return False

    print(f"✓ Settings file exists: {settings_path}")

    try:
        import json
        with open(settings_path) as f:
            config = json.load(f)

        mcp_servers = config.get("mcpServers", {})
        print(f"✓ Valid JSON")
        print(f"✓ MCP servers configured: {len(mcp_servers)}")

        for name, server_config in mcp_servers.items():
            enabled = server_config.get("enabled", True)
            url = server_config.get("httpUrl", "N/A")
            status = "ENABLED" if enabled else "DISABLED"
            print(f"  • {name}: {url[:50]}... [{status}]")

        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_mcp_client():
    """Test 2: MCP client can load settings and connect."""
    print("\n" + "=" * 60)
    print("TEST 2: MCP Client")
    print("=" * 60)

    try:
        client = MCPClient(".claude/settings.json")
        print(f"✓ MCPClient initialized")

        print(f"\nConnecting to MCP servers...")
        client.connect_to_servers()

        print(f"\n✓ Connection complete")
        print(f"  • Servers connected: {len(client.servers)}")
        print(f"  • Total tools discovered: {len(client.all_tools)}")

        for server_name, server in client.servers.items():
            tool_count = len(server.tools or [])
            print(f"\n  Server: {server_name}")
            print(f"    URL: {server.url}")
            print(f"    Tools: {tool_count}")
            if server.tools and len(server.tools) > 0:
                print(f"    Sample tools:")
                for tool in server.tools[:3]:
                    print(f"      - {tool['name']}")

        return len(client.servers) > 0

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_dynamic_agent():
    """Test 3: Dynamic agent initialization."""
    print("\n" + "=" * 60)
    print("TEST 3: Dynamic Agent Initialization")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set")
        print("   Skipping agent initialization test")
        return None

    try:
        print(f"✓ ANTHROPIC_API_KEY found")

        print(f"\nInitializing DynamicAgent...")
        agent = DynamicAgent(
            anthropic_api_key=api_key,
            settings_path=".claude/settings.json"
        )

        print(f"\n✓ DynamicAgent initialized successfully")
        print(f"  • MCP servers: {len(agent.mcp_client.servers)}")
        print(f"  • Tools for Anthropic: {len(agent.tools)}")

        print(f"\n✓ System prompt generated ({len(agent._build_system_prompt())} chars)")

        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("   DYNAMIC AGENT TEST SUITE")
    print("=" * 60)
    print(f"Working directory: {Path.cwd()}")

    results = {}

    # Test 1: Settings file
    results["settings"] = test_settings_file()

    # Test 2: MCP client
    results["mcp_client"] = test_mcp_client()

    # Test 3: Dynamic agent (async)
    results["dynamic_agent"] = asyncio.run(test_dynamic_agent())

    # Summary
    print("\n" + "=" * 60)
    print("   TEST RESULTS")
    print("=" * 60)

    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIPPED"

        print(f"{status}  {test_name}")

    all_passed = all(r in [True, None] for r in results.values())
    any_failed = any(r is False for r in results.values())

    print("\n" + "=" * 60)
    if all_passed and not any_failed:
        print("  ✅ ALL TESTS PASSED")
    else:
        print("  ❌ SOME TESTS FAILED")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
