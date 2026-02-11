#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for ClaudeAgentOptions wrapper.

Demonstrates how to use the ClaudeAgentOptions interface
which matches the official claude-agent-sdk API.

Run: python test_claude_options.py
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

from orchestrator.claude_options import (
    ClaudeAgentOptions,
    query,
    ClaudeAgentClient,
    McpServerConfig
)


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_create_options():
    """Test 1: Create ClaudeAgentOptions."""
    print_section("TEST 1: Create ClaudeAgentOptions")

    api_key = os.getenv("ANTHROPIC_API_KEY", "dummy-key")

    # Test 1a: Create with minimal config (loads from settings.json)
    print("\n[1a] Creating with minimal config (auto-load from settings.json):")
    options = ClaudeAgentOptions(
        api_key=api_key,
        settings_path=".claude/settings.json",
        verbose=True
    )

    print(f"✓ Options created")
    print(f"  - Model: {options.model}")
    print(f"  - MCP Servers: {len(options.mcp_servers or {})}")
    print(f"  - Max Turns: {options.max_turns}")
    print(f"  - Permission Mode: {options.permission_mode}")

    if options.mcp_servers:
        print(f"\n  MCP Servers loaded:")
        for name, server in options.mcp_servers.items():
            status = "ENABLED" if server.enabled else "DISABLED"
            print(f"    • {name}: {server.httpUrl[:50]}... [{status}]")

    # Test 1b: Create with explicit MCP servers
    print("\n[1b] Creating with explicit MCP server configuration:")
    options_explicit = ClaudeAgentOptions(
        api_key=api_key,
        settings_path=".claude/settings.json",
        mcp_servers={
            "custom-server": McpServerConfig(
                httpUrl="http://localhost:9999/mcp",
                description="Custom MCP server",
                enabled=True
            )
        },
        allowed_tools=["tool1", "tool2"],
        max_turns=10,
        verbose=False
    )

    print(f"✓ Options with explicit config created")
    print(f"  - MCP Servers: {list(options_explicit.mcp_servers.keys())}")
    print(f"  - Allowed Tools: {options_explicit.allowed_tools}")
    print(f"  - Max Turns: {options_explicit.max_turns}")

    # Test 1c: Serialize and deserialize
    print("\n[1c] Serializing to dict and back:")
    options_dict = options.to_dict()
    print(f"✓ Serialized to dict ({len(options_dict)} keys)")

    options_restored = ClaudeAgentOptions.from_dict(options_dict, api_key=api_key)
    print(f"✓ Restored from dict")
    print(f"  - Model: {options_restored.model}")
    print(f"  - MCP Servers: {len(options_restored.mcp_servers or {})}")

    return True


async def test_query_function():
    """Test 2: Test query() function."""
    print_section("TEST 2: query() Function")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set")
        print("   Skipping query function test")
        return None

    print("\nCreating ClaudeAgentOptions...")
    options = ClaudeAgentOptions(
        api_key=api_key,
        settings_path=".claude/settings.json",
        max_turns=5,
        verbose=True
    )

    print(f"✓ Options created with {len(options.mcp_servers or {})} MCP servers")

    print("\nExecuting simple task with query()...")
    print("Task: 'List all available tools from MCP servers'")

    try:
        result = await query(
            task="List all available tools from MCP servers",
            options=options
        )

        print(f"\n✓ Query completed successfully")
        print(f"  - Status: {result.get('status')}")
        print(f"  - Tool calls: {result.get('tool_calls', 0)}")
        print(f"  - Turns: {result.get('turns', 0)}")
        print(f"  - Result preview: {result.get('result', '')[:200]}...")

        return True

    except Exception as e:
        print(f"\n✗ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_client_conversation():
    """Test 3: Test ClaudeAgentClient for continuous conversation."""
    print_section("TEST 3: ClaudeAgentClient (Continuous Conversation)")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set")
        print("   Skipping client conversation test")
        return None

    print("\nCreating ClaudeAgentClient...")
    options = ClaudeAgentOptions(
        api_key=api_key,
        settings_path=".claude/settings.json",
        max_turns=3,
        verbose=True
    )

    client = ClaudeAgentClient(options=options)
    print(f"✓ Client created")

    try:
        # First interaction
        print("\n[Interaction 1] Asking about MCP servers...")
        result1 = await client.query("What MCP servers are available?")
        print(f"✓ Response received ({result1.get('status')})")

        # Second interaction (maintains context)
        print("\n[Interaction 2] Following up...")
        result2 = await client.query("How many tools do they provide in total?")
        print(f"✓ Response received ({result2.get('status')})")

        # Get conversation summary
        summary = client.get_conversation_summary()
        print(f"\n✓ Conversation Summary:")
        print(f"  - Total interactions: {summary['total_interactions']}")
        print(f"  - Total tool calls: {summary['total_tool_calls']}")
        print(f"  - Total turns: {summary['total_turns']}")

        return True

    except Exception as e:
        print(f"\n✗ Client conversation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compatibility_check():
    """Test 4: Verify compatibility with official SDK structure."""
    print_section("TEST 4: SDK Compatibility Check")

    print("\nChecking ClaudeAgentOptions attributes match official SDK:")

    # Expected attributes from official SDK
    expected_attrs = [
        "api_key", "settings_path", "mcp_servers", "allowed_tools",
        "enable_mcp_servers", "system_prompt", "system_prompt_preset",
        "permission_mode", "model", "max_turns", "max_tokens",
        "temperature", "cwd", "verbose", "log_tool_calls"
    ]

    api_key = "dummy-key"
    options = ClaudeAgentOptions(api_key=api_key)

    missing = []
    for attr in expected_attrs:
        if not hasattr(options, attr):
            missing.append(attr)
        else:
            print(f"  ✓ {attr}")

    if missing:
        print(f"\n✗ Missing attributes: {missing}")
        return False
    else:
        print(f"\n✓ All expected attributes present")
        return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("   CLAUDE AGENT OPTIONS TEST SUITE")
    print("=" * 70)
    print(f"Working directory: {Path.cwd()}")

    results = {}

    # Test 1: Create options
    results["create_options"] = test_create_options()

    # Test 2: query() function (async)
    results["query_function"] = asyncio.run(test_query_function())

    # Test 3: Client conversation (async)
    results["client_conversation"] = asyncio.run(test_client_conversation())

    # Test 4: Compatibility check
    results["compatibility"] = test_compatibility_check()

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

    all_passed = all(r in [True, None] for r in results.values())
    any_failed = any(r is False for r in results.values())

    print("\n" + "=" * 70)
    if all_passed and not any_failed:
        print("  ✅ ALL TESTS PASSED")
    else:
        print("  ❌ SOME TESTS FAILED")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
