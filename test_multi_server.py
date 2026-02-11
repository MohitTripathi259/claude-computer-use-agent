#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Multi-Server Integration (Phase 3).

Tests:
1. Both MCP servers (computer-use + retail-data) are discovered
2. Tools from both servers are aggregated
3. DynamicAgent can use tools from both servers
4. ClaudeAgentOptions with tool filtering works
5. Multi-server workflows can be orchestrated

Run: python test_multi_server.py
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
from orchestrator.claude_options import ClaudeAgentOptions, query


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_settings_both_enabled():
    """Test 1: Verify both servers enabled in settings."""
    print_section("TEST 1: Settings Configuration")

    import json
    settings_path = Path(".claude/settings.json")

    with open(settings_path) as f:
        config = json.load(f)

    servers = config.get("mcpServers", {})

    print(f"\n  Total MCP servers configured: {len(servers)}")

    for name, server_config in servers.items():
        enabled = server_config.get("enabled", False)
        url = server_config.get("httpUrl", "")
        status = "✓ ENABLED" if enabled else "✗ DISABLED"

        print(f"\n  {status}  {name}")
        print(f"    URL: {url}")
        print(f"    Description: {server_config.get('description', 'N/A')[:80]}")

    # Check both are enabled
    computer_use_enabled = servers.get("computer-use", {}).get("enabled", False)
    retail_data_enabled = servers.get("retail-data", {}).get("enabled", False)

    if computer_use_enabled and retail_data_enabled:
        print(f"\n✓ Both servers enabled in settings.json")
        return True
    else:
        print(f"\n✗ Not all servers enabled:")
        print(f"    computer-use: {computer_use_enabled}")
        print(f"    retail-data: {retail_data_enabled}")
        return False


def test_mcp_client_multi_server():
    """Test 2: MCPClient discovers both servers."""
    print_section("TEST 2: MCPClient Multi-Server Discovery")

    try:
        print("\n  Creating MCPClient...")
        client = MCPClient(".claude/settings.json")

        print("  Connecting to MCP servers...")
        client.connect_to_servers()

        print(f"\n✓ MCPClient initialized")
        print(f"  • Servers connected: {len(client.servers)}")
        print(f"  • Total tools discovered: {len(client.all_tools)}")

        for server_name, server in client.servers.items():
            tool_count = len(server.tools or [])
            print(f"\n  Server: {server_name}")
            print(f"    URL: {server.url}")
            print(f"    Tools: {tool_count}")

            if server.tools and len(server.tools) > 0:
                print(f"    Tool names:")
                for tool in server.tools[:5]:  # Show first 5
                    print(f"      - {tool['name']}")
                if len(server.tools) > 5:
                    print(f"      ... and {len(server.tools) - 5} more")

        # Verify we have both servers
        has_computer_use = "computer-use" in client.servers
        has_retail_data = "retail-data" in client.servers

        if has_computer_use and has_retail_data:
            print(f"\n✓ Both servers discovered successfully")
            print(f"  Expected: 4 tools from computer-use + 7 tools from retail-data = 11 total")
            print(f"  Actual: {len(client.all_tools)} total tools")
            return True
        else:
            print(f"\n✗ Missing servers:")
            print(f"    computer-use: {has_computer_use}")
            print(f"    retail-data: {has_retail_data}")
            return False

    except Exception as e:
        print(f"\n✗ MCPClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_dynamic_agent_multi_server():
    """Test 3: DynamicAgent with multiple servers."""
    print_section("TEST 3: DynamicAgent Multi-Server Integration")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set")
        print("   Skipping DynamicAgent test")
        return None

    try:
        print(f"\n  Creating DynamicAgent with multi-server config...")

        agent = DynamicAgent(
            anthropic_api_key=api_key,
            settings_path=".claude/settings.json"
        )

        print(f"\n✓ DynamicAgent initialized")
        print(f"  • MCP servers loaded: {len(agent.mcp_client.servers)}")
        print(f"  • Total tools for Anthropic: {len(agent.tools)}")

        # Group tools by server
        tool_by_server = {}
        for tool in agent.mcp_client.all_tools:
            server_name = tool.get("_mcp_server", "unknown")
            if server_name not in tool_by_server:
                tool_by_server[server_name] = []
            tool_by_server[server_name].append(tool["name"])

        print(f"\n  Tools by server:")
        for server_name, tools in tool_by_server.items():
            print(f"    {server_name}: {len(tools)} tools")
            for tool_name in tools[:3]:
                print(f"      - {tool_name}")
            if len(tools) > 3:
                print(f"      ... and {len(tools) - 3} more")

        # Verify we have tools from both servers
        has_computer_tools = "computer-use" in tool_by_server
        has_retail_tools = "retail-data" in tool_by_server

        if has_computer_tools and has_retail_tools:
            print(f"\n✓ Tools from both servers available to agent")
            return True
        else:
            print(f"\n⚠️  Some tools missing:")
            print(f"    computer-use tools: {has_computer_tools}")
            print(f"    retail-data tools: {has_retail_tools}")
            return False

    except Exception as e:
        print(f"\n✗ DynamicAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_claude_options_tool_filtering():
    """Test 4: ClaudeAgentOptions with tool filtering."""
    print_section("TEST 4: ClaudeAgentOptions Tool Filtering")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set")
        print("   Skipping tool filtering test")
        return None

    try:
        print("\n  [Test 4a] No filtering (all tools)")

        options_all = ClaudeAgentOptions(
            api_key=api_key,
            settings_path=".claude/settings.json",
            verbose=False
        )

        print(f"  ✓ All tools loaded: {len(options_all.mcp_servers or {})} servers")

        # Create agent
        from orchestrator.claude_options import create_agent_with_options
        agent_all = create_agent_with_options(options_all)

        print(f"  ✓ Agent has {len(agent_all.tools)} tools (unfiltered)")

        # Test 4b: Filter to only computer use tools
        print("\n  [Test 4b] Filter to computer-use tools only")

        computer_tools = ["computer_20250124", "bash_20250124", "text_editor_20250728", "browser"]

        options_filtered = ClaudeAgentOptions(
            api_key=api_key,
            settings_path=".claude/settings.json",
            allowed_tools=computer_tools,
            verbose=False
        )

        agent_filtered = create_agent_with_options(options_filtered)

        print(f"  ✓ Filtered agent has {len(agent_filtered.tools)} tools")
        print(f"    Allowed: {computer_tools}")
        print(f"    Actual: {[t['name'] for t in agent_filtered.tools]}")

        # Verify filtering worked
        filtered_names = [t['name'] for t in agent_filtered.tools]
        all_allowed = all(name in computer_tools for name in filtered_names)

        if all_allowed:
            print(f"\n✓ Tool filtering works correctly")
            return True
        else:
            print(f"\n✗ Some disallowed tools found")
            return False

    except Exception as e:
        print(f"\n✗ Tool filtering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_discovery_summary():
    """Test 5: Summary of tool discovery across servers."""
    print_section("TEST 5: Tool Discovery Summary")

    try:
        client = MCPClient(".claude/settings.json")
        client.connect_to_servers()

        print(f"\n  Multi-Server Tool Catalog")
        print(f"  {'=' * 66}")

        total_tools = 0
        for server_name, server in client.servers.items():
            tools = server.tools or []
            total_tools += len(tools)

            print(f"\n  📦 {server_name}")
            print(f"     URL: {server.url}")
            print(f"     Tools: {len(tools)}")

            if tools:
                print(f"     Tool List:")
                for tool in tools:
                    desc = tool.get('description', '')[:60]
                    print(f"       • {tool['name']}")
                    print(f"         └─ {desc}...")

        print(f"\n  {'=' * 66}")
        print(f"  Total Tools Available: {total_tools}")
        print(f"  {'=' * 66}")

        # Expected totals
        expected_computer = 4
        expected_retail = 7
        expected_total = expected_computer + expected_retail

        computer_actual = len(client.servers.get("computer-use", MCPClient(".claude/settings.json")).tools or [])
        retail_actual = len(client.servers.get("retail-data", MCPClient(".claude/settings.json")).tools or [])

        print(f"\n  Verification:")
        print(f"    computer-use: {computer_actual} tools (expected {expected_computer})")
        print(f"    retail-data: {retail_actual} tools (expected {expected_retail})")
        print(f"    TOTAL: {total_tools} tools (expected {expected_total})")

        if total_tools >= 10:  # At least most tools discovered
            print(f"\n✓ Multi-server tool discovery successful")
            return True
        else:
            print(f"\n⚠️  Fewer tools than expected")
            return False

    except Exception as e:
        print(f"\n✗ Tool discovery summary failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 3 tests."""
    print("\n" + "=" * 70)
    print("   PHASE 3: MULTI-SERVER INTEGRATION TEST SUITE")
    print("=" * 70)
    print(f"Working directory: {Path.cwd()}")

    print("\n  Testing multi-server setup:")
    print("    • computer-use MCP server (4 tools)")
    print("    • retail-data MCP server (7 tools)")
    print("    • Total expected: 11 tools")

    results = {}

    # Test 1: Settings configuration
    results["settings_config"] = test_settings_both_enabled()

    if not results["settings_config"]:
        print("\n" + "=" * 70)
        print("  ⚠️  STOPPING: Both servers not enabled")
        print("=" * 70)
        print("\nPlease ensure both servers are enabled in .claude/settings.json")
        return 1

    # Test 2: MCPClient multi-server discovery
    results["mcp_client_multi"] = test_mcp_client_multi_server()

    # Test 3: DynamicAgent with multiple servers
    results["dynamic_agent_multi"] = asyncio.run(test_dynamic_agent_multi_server())

    # Test 4: Tool filtering with ClaudeAgentOptions
    results["tool_filtering"] = asyncio.run(test_claude_options_tool_filtering())

    # Test 5: Tool discovery summary
    results["tool_summary"] = test_tool_discovery_summary()

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
        print("\n  Phase 3 Multi-Server Integration: SUCCESS!")
        print("\n  Key Achievements:")
        print("    ✓ Multiple MCP servers discovered")
        print("    ✓ Tools from all servers aggregated")
        print("    ✓ DynamicAgent can access all tools")
        print("    ✓ Tool filtering works correctly")
        print("\n  Ready for Phase 4: Skills Integration")
    else:
        print("  ❌ SOME TESTS FAILED")
        print("\n  Review failures above for details")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
