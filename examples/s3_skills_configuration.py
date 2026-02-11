#!/usr/bin/env python3
"""
S3 Skills Configuration Examples
Shows how to configure S3 skills (NOT via settings.json)
"""

from orchestrator.agent_runner import DynamicAgent
from orchestrator.claude_options import ClaudeAgentOptions, create_agent_with_options

# ============================================================
# Method 1: Direct DynamicAgent Parameters (RECOMMENDED)
# ============================================================

# Option A: Use defaults
agent = DynamicAgent(
    anthropic_api_key="sk-ant-...",
    settings_path=".claude/settings.json",  # For MCP servers
    load_s3_skills=True,  # Default: cerebricks-studio-agent-skills/skills_phase3/
)

# Option B: Custom S3 location
agent = DynamicAgent(
    anthropic_api_key="sk-ant-...",
    settings_path=".claude/settings.json",
    load_s3_skills=True,
    s3_skills_bucket="my-company-skills",
    s3_skills_prefix="production/v2/"
)

# Option C: Disable S3 skills
agent = DynamicAgent(
    anthropic_api_key="sk-ant-...",
    settings_path=".claude/settings.json",
    load_s3_skills=False  # Only use MCP servers from settings.json
)


# ============================================================
# Method 2: Using ClaudeAgentOptions (SDK Compatible)
# ============================================================

options = ClaudeAgentOptions(
    api_key="sk-ant-...",
    settings_path=".claude/settings.json",
    model="claude-sonnet-4-20250514",

    # S3 Skills configuration
    load_s3_skills=True,
    s3_skills_bucket="cerebricks-studio-agent-skills",
    s3_skills_prefix="skills_phase3/"
)

agent = create_agent_with_options(options)


# ============================================================
# Method 3: Environment Variables (Optional)
# ============================================================

import os

# Set environment variables
os.environ["LOAD_S3_SKILLS"] = "true"
os.environ["S3_SKILLS_BUCKET"] = "cerebricks-studio-agent-skills"
os.environ["S3_SKILLS_PREFIX"] = "skills_phase3/"

# Then create agent (reads from environment)
agent = DynamicAgent(
    anthropic_api_key="sk-ant-...",
    load_s3_skills=os.getenv("LOAD_S3_SKILLS", "true") == "true",
    s3_skills_bucket=os.getenv("S3_SKILLS_BUCKET", "cerebricks-studio-agent-skills"),
    s3_skills_prefix=os.getenv("S3_SKILLS_PREFIX", "skills_phase3/")
)


# ============================================================
# What settings.json IS used for (MCP Servers)
# ============================================================

# settings.json configures MCP servers ONLY:
settings_json_example = """
{
  "mcpServers": {
    "computer-use": {
      "httpUrl": "http://localhost:8080",
      "enabled": true,
      "description": "Computer use tools (screenshot, bash, browser)"
    },
    "retail-data": {
      "httpUrl": "http://localhost:8081",
      "enabled": true,
      "description": "Retail data access"
    },
    "skills": {
      "httpUrl": "http://localhost:8082",
      "enabled": true,
      "description": "Legacy skills (query_database, etc)"
    }
  }
}
"""

# S3 skills are separate - loaded via constructor parameters
# They work ALONGSIDE MCP servers configured in settings.json

print("Configuration Examples Created!")
print("\nKey Points:")
print("1. S3 skills = Constructor parameters")
print("2. MCP servers = settings.json")
print("3. Both work together in DynamicAgent")
