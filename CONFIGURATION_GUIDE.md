# Configuration Guide - MCP Servers vs S3 Skills

**Important**: MCP servers and S3 skills are configured **differently**!

---

## 🔧 Two Configuration Systems

### 1. MCP Servers → settings.json ✅

**File**: `.claude/settings.json`

```json
{
  "mcpServers": {
    "computer-use": {
      "httpUrl": "http://localhost:8080",
      "enabled": true,
      "description": "Computer use tools (screenshot, bash, browser, editor)"
    },
    "retail-data": {
      "httpUrl": "http://localhost:8081",
      "enabled": true,
      "description": "Retail data access (7 tools)"
    },
    "skills": {
      "httpUrl": "http://localhost:8082",
      "enabled": true,
      "description": "Legacy skills (query_database, etc)"
    }
  }
}
```

**What this configures**:
- MCP server endpoints (HTTP URLs)
- Tool discovery endpoints
- Enable/disable servers
- Server descriptions

**Loaded by**: `MCPClient` class in `orchestrator/agent_runner.py`

### 2. S3 Skills → Code Parameters ✅

**NOT in settings.json** - configured via constructor:

```python
from orchestrator.agent_runner import DynamicAgent

agent = DynamicAgent(
    anthropic_api_key="sk-ant-...",
    settings_path=".claude/settings.json",  # MCP servers config

    # S3 Skills configuration (separate)
    load_s3_skills=True,
    s3_skills_bucket="cerebricks-studio-agent-skills",
    s3_skills_prefix="skills_phase3/"
)
```

**What this configures**:
- S3 bucket location
- S3 prefix/path
- Enable/disable S3 skills
- Cache directory (optional)

**Loaded by**: `S3SkillLoader` class in `orchestrator/skill_loader.py`

---

## 📊 Comparison Table

| Aspect | MCP Servers | S3 Skills |
|--------|-------------|-----------|
| **Config Location** | `.claude/settings.json` | Code parameters |
| **Type** | HTTP endpoints | S3 objects |
| **Discovery** | Runtime (tools/list API) | Startup (S3 list) |
| **Format** | JSON-RPC 2.0 protocol | Skill files (md, json, py) |
| **Caching** | No caching | Local + memory cache |
| **Updates** | Restart servers | Re-run or force refresh |
| **Tools** | MCP tools via protocol | Context in system prompt |
| **Purpose** | Dynamic tool execution | Skill documentation/context |

---

## ✅ Correct Configuration Pattern

### Your settings.json (MCP Servers Only)

```json
{
  "mcpServers": {
    "computer-use": {
      "httpUrl": "http://localhost:8080",
      "enabled": true,
      "description": "Official Anthropic computer use tools"
    },
    "retail-data": {
      "httpUrl": "http://localhost:8081",
      "enabled": true,
      "description": "Retail database access"
    },
    "skills": {
      "httpUrl": "http://localhost:8082",
      "enabled": true,
      "description": "Legacy local skills"
    }
  }
}
```

### Your Python Code (S3 Skills Configuration)

```python
# main.py or wherever you create the agent

from orchestrator.agent_runner import DynamicAgent

agent = DynamicAgent(
    anthropic_api_key="sk-ant-...",

    # MCP servers from settings.json
    settings_path=".claude/settings.json",

    # S3 skills (separate configuration)
    load_s3_skills=True,
    s3_skills_bucket="cerebricks-studio-agent-skills",
    s3_skills_prefix="skills_phase3/"
)
```

---

## 🏗️ How They Work Together

```
DynamicAgent.__init__()
    │
    ├─► MCPClient.load_settings()
    │       │
    │       └─► Reads .claude/settings.json
    │           └─► Discovers tools from MCP servers
    │               (computer-use, retail-data, skills)
    │
    └─► S3SkillLoader.preload_skills()
            │
            └─► Downloads from S3 bucket
                └─► Loads skills into memory
                    (pdf_report_generator, etc)

System Prompt:
    ├─► S3 Skills section (full documentation)
    └─► MCP Tools section (tool names + descriptions)

Claude sees BOTH:
    - Skills from S3 (context/documentation)
    - Tools from MCP servers (executable actions)
```

---

## 📝 Complete Example

### 1. Create settings.json for MCP servers

**File**: `.claude/settings.json`

```json
{
  "mcpServers": {
    "computer-use": {
      "httpUrl": "http://localhost:8080",
      "enabled": true,
      "description": "Computer use tools"
    },
    "retail-data": {
      "httpUrl": "http://localhost:8081",
      "enabled": true,
      "description": "Retail data tools"
    }
  }
}
```

### 2. Create agent with S3 skills in code

**File**: `main.py`

```python
#!/usr/bin/env python3
import os
from orchestrator.agent_runner import DynamicAgent

def main():
    # Create agent with BOTH:
    # - MCP servers from settings.json
    # - S3 skills from constructor

    agent = DynamicAgent(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),

        # MCP servers configuration
        settings_path=".claude/settings.json",

        # S3 skills configuration
        load_s3_skills=True,
        s3_skills_bucket="cerebricks-studio-agent-skills",
        s3_skills_prefix="skills_phase3/"
    )

    print(f"MCP servers: {len(agent.mcp_client.servers)}")
    print(f"MCP tools: {len(agent.tools)}")
    print(f"S3 skills loaded: {agent.skills_loaded}")

    if agent.skill_loader:
        skills = agent.skill_loader.get_skills()
        print(f"S3 skills: {list(skills.keys())}")

if __name__ == "__main__":
    main()
```

### 3. Run

```bash
python main.py
```

**Output**:
```
MCP servers: 2
MCP tools: 11
S3 skills loaded: True
S3 skills: ['pdf_report_generator']
```

---

## 🎯 Quick Decision Guide

### Use settings.json for:
- ✅ MCP server endpoints
- ✅ HTTP-based tools
- ✅ Local server configurations
- ✅ Enable/disable servers

### Use code parameters for:
- ✅ S3 bucket configuration
- ✅ S3 skills loading
- ✅ Cache directory
- ✅ Force refresh options

---

## ❌ Common Mistakes

### ❌ DON'T: Put S3 skills in settings.json

```json
{
  "mcpServers": {
    "s3-skills": {
      "s3Bucket": "cerebricks-studio-agent-skills",
      "s3Prefix": "skills_phase3/"
    }
  }
}
```

This won't work - settings.json is for MCP servers only!

### ✅ DO: Configure S3 skills in code

```python
agent = DynamicAgent(
    anthropic_api_key="...",
    settings_path=".claude/settings.json",  # MCP servers
    load_s3_skills=True,  # S3 skills
    s3_skills_bucket="...",
    s3_skills_prefix="..."
)
```

---

## 🔄 Alternative: Environment Variables

If you want S3 skills configurable without code changes:

### .env file

```bash
# MCP Servers (settings.json path)
CLAUDE_SETTINGS_PATH=.claude/settings.json

# S3 Skills
LOAD_S3_SKILLS=true
S3_SKILLS_BUCKET=cerebricks-studio-agent-skills
S3_SKILLS_PREFIX=skills_phase3/
```

### Python code

```python
import os
from dotenv import load_dotenv
from orchestrator.agent_runner import DynamicAgent

load_dotenv()

agent = DynamicAgent(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    settings_path=os.getenv("CLAUDE_SETTINGS_PATH", ".claude/settings.json"),
    load_s3_skills=os.getenv("LOAD_S3_SKILLS", "true") == "true",
    s3_skills_bucket=os.getenv("S3_SKILLS_BUCKET", "cerebricks-studio-agent-skills"),
    s3_skills_prefix=os.getenv("S3_SKILLS_PREFIX", "skills_phase3/")
)
```

---

## 📚 Summary

### settings.json Structure

```json
{
  "mcpServers": {
    "<server-name>": {
      "httpUrl": "<endpoint>",
      "enabled": true|false,
      "description": "<description>"
    }
  }
}
```

**Purpose**: Configure MCP server endpoints

### S3 Skills Configuration

```python
DynamicAgent(
    anthropic_api_key="...",
    settings_path=".claude/settings.json",  # MCP servers
    load_s3_skills=True,  # S3 skills enabled
    s3_skills_bucket="bucket-name",
    s3_skills_prefix="path/to/skills/"
)
```

**Purpose**: Configure S3 skills loading

### Both Work Together

```
Agent = MCP Servers (settings.json) + S3 Skills (code params)
        └─► HTTP tools                └─► Skill documentation
```

---

## ✅ Your Configuration

Based on your setup:

### .claude/settings.json (MCP Servers)

```json
{
  "mcpServers": {
    "computer-use": {
      "httpUrl": "http://localhost:8080",
      "enabled": true,
      "description": "Computer use tools"
    },
    "retail-data": {
      "httpUrl": "http://localhost:8081",
      "enabled": true,
      "description": "Retail data access"
    },
    "skills": {
      "httpUrl": "http://localhost:8082",
      "enabled": true,
      "description": "Legacy skills"
    }
  }
}
```

### Your Code (S3 Skills)

```python
agent = DynamicAgent(
    anthropic_api_key="sk-ant-...",
    settings_path=".claude/settings.json",
    load_s3_skills=True,  # This loads S3 skills
    s3_skills_bucket="cerebricks-studio-agent-skills",
    s3_skills_prefix="skills_phase3/"
)
```

**That's it!** ✅

- MCP servers: configured in JSON file
- S3 skills: configured in code
- Both work together seamlessly

