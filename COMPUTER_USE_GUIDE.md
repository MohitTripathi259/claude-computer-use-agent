# 🖥️ Computer Use Tools - Complete Implementation Guide

## ✅ What's Implemented

All three Anthropic Computer Use tools are now available:

| Tool | Type ID | Capabilities | Handler |
|------|---------|--------------|---------|
| **computer** | `computer_20241022` | Screen capture, mouse control, keyboard input, browser automation | `handle_computer()` |
| **bash** | `bash_20250124` | Shell command execution, file system operations | `handle_bash()` |
| **text_editor** | `text_editor_20250728` | File view/create/edit with str_replace and insert | `handle_text_editor()` |

---

## 🏗️ Architecture

```
User Request (via Postman)
    ↓
API Server (api_server.py)
    ↓
DynamicAgent.enable_computer_tools()
    ↓ registers tools
    ├─ computer_20241022 (screen/mouse/keyboard)
    ├─ bash_20250124 (shell commands)
    └─ text_editor_20250728 (file operations)
    ↓
Claude analyzes task and calls tools
    ↓
Tool Routing (native_tools list)
    ↓
NativeToolHandler (native_tool_handlers.py)
    ├─ handle_computer() → Docker container (localhost:8080)
    ├─ handle_bash() → subprocess.run()
    └─ handle_text_editor() → pathlib file operations
    ↓
Results returned to Claude
    ↓
Final response to user
```

---

## 📋 Prerequisites

### 1. Computer Use Docker Container (Required for `computer` tool)

The `computer` tool requires a Docker container with:
- VNC display server
- Desktop environment (X11)
- Browser (Chromium/Firefox)
- REST API endpoints for mouse/keyboard/screen

**Start the container:**
```bash
docker run -d -p 8080:8080 \
  -e DISPLAY_WIDTH=1024 \
  -e DISPLAY_HEIGHT=768 \
  --name computer-use \
  anthropic/computer-use:latest
```

**Verify it's running:**
```bash
curl http://localhost:8080/screenshot
```

Expected response:
```json
{
  "base64_image": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

### 2. Environment Variables

Add to `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
COMPUTER_USE_CONTAINER_URL=http://localhost:8080
```

### 3. Start API Server

```bash
python api_server.py
```

---

## 🧪 Testing All Tools

### Test 1: Computer Tool - Screenshot

**Postman Request:**
```json
POST http://localhost:8003/execute

{
  "prompt": "Take a screenshot and describe what you see on the screen",
  "max_turns": 5,
  "use_computer_tools": true
}
```

**Expected:**
- Claude calls `computer(action="screenshot")`
- Returns base64 image
- Claude describes screen contents

### Test 2: Computer Tool - Mouse + Click

**Postman Request:**
```json
{
  "prompt": "Take a screenshot, find any clickable button, move the mouse to it, and click it",
  "max_turns": 10,
  "use_computer_tools": true
}
```

**Expected:**
- `computer(action="screenshot")`
- Claude identifies button coordinates [x, y]
- `computer(action="mouse_move", coordinate=[x, y])`
- `computer(action="left_click")`
- Another screenshot to verify

### Test 3: Computer Tool - Browser Automation

**Postman Request:**
```json
{
  "prompt": "Open a browser, navigate to example.com, and take a screenshot",
  "max_turns": 15,
  "use_computer_tools": true
}
```

**Expected workflow:**
1. Screenshot (see desktop)
2. Find browser icon coordinates
3. Click browser icon
4. Type URL in address bar
5. Press Enter
6. Wait and screenshot result

### Test 4: Bash Tool - File Operations

**Postman Request:**
```json
{
  "prompt": "List all Python files and count total lines of code",
  "max_turns": 5,
  "use_computer_tools": true
}
```

**Expected:**
- Single PowerShell command aggregating results
- Fast execution (1-3 turns)

### Test 5: Text Editor Tool - File Editing

**Postman Request:**
```json
{
  "prompt": "Create a new file called test.txt with 'Hello World' and then view it",
  "max_turns": 5,
  "use_computer_tools": true
}
```

**Expected:**
- `str_replace_based_edit_tool(command="create", path="test.txt", file_text="Hello World")`
- `str_replace_based_edit_tool(command="view", path="test.txt")`

### Test 6: Combined Tools - Full Workflow

**Postman Request:**
```json
{
  "prompt": "Take a screenshot of the desktop, create a text file with a description of what you see, and then show me the file contents",
  "max_turns": 10,
  "use_computer_tools": true
}
```

**Expected workflow:**
1. `computer(action="screenshot")` → get image
2. Claude analyzes image
3. `str_replace_based_edit_tool(command="create", ...)` → save description
4. `str_replace_based_edit_tool(command="view", ...)` → show file

---

## 🔧 Computer Tool Actions Reference

### Screenshot
```json
{
  "action": "screenshot"
}
```
Returns: `{"base64_image": "...", "success": true}`

### Mouse Move
```json
{
  "action": "mouse_move",
  "coordinate": [512, 384]
}
```

### Click (with optional coordinates)
```json
{
  "action": "left_click",
  "coordinate": [100, 200]
}
```

Variations: `right_click`, `double_click`, `middle_click`

### Type Text
```json
{
  "action": "type",
  "text": "https://example.com"
}
```

### Press Key
```json
{
  "action": "key",
  "text": "Return"
}
```

Common keys: `Return`, `Tab`, `Escape`, `BackSpace`, `Delete`, `space`

### Cursor Position
```json
{
  "action": "cursor_position"
}
```
Returns: `{"x": 123, "y": 456, "success": true}`

---

## 📊 Performance Expectations

| Tool | Typical Latency | Notes |
|------|----------------|-------|
| **computer** | 500-2000ms | Depends on Docker container response |
| **bash** | 50-500ms | Fast for simple commands, slower for complex |
| **text_editor** | 10-100ms | Very fast, local file I/O |

---

## 🐛 Troubleshooting

### Issue: "Computer tool failed: Connection refused"

**Cause:** Docker container not running

**Fix:**
```bash
docker ps | grep computer-use
# If not running:
docker start computer-use
# Or create new:
docker run -d -p 8080:8080 --name computer-use anthropic/computer-use:latest
```

### Issue: "Screenshot returns empty image"

**Cause:** VNC display not initialized

**Fix:**
```bash
docker exec -it computer-use bash
export DISPLAY=:1
```

### Issue: "Bash tool working but computer tool not available"

**Cause:** `use_computer_tools` flag not set

**Fix:**
Ensure request includes:
```json
{
  "use_computer_tools": true
}
```

### Issue: "Tools registered but Claude not using computer tool"

**Cause:** Docker container might be down, or Claude prefers bash for the task

**Fix:**
- Verify container: `curl http://localhost:8080/screenshot`
- Be explicit in prompt: "Use the computer tool to take a screenshot"

---

## 🎯 Use Cases

### 1. Web Scraping with Visual Verification
- Screenshot page
- Identify elements visually
- Extract data
- Verify with screenshots

### 2. Automated Testing
- Navigate UI
- Click buttons
- Fill forms
- Screenshot results

### 3. File System Automation
- Bash for file operations
- Text editor for content manipulation
- Computer tool for GUI applications

### 4. Research & Documentation
- Browse websites
- Screenshot interesting findings
- Save to files
- Generate reports

---

## 📝 System Prompt Guidance

When `use_computer_tools: true`, Claude receives this guidance:

**Computer Tool:**
- Take screenshot first to understand state
- Identify coordinates visually
- Chain actions efficiently
- Always verify with screenshots

**Bash Tool:**
- Prefer single aggregated commands
- Use PowerShell for complex Windows operations
- Avoid iterating files individually

**Text Editor:**
- Use for targeted file operations
- Not for data aggregation (use bash instead)

---

## 🚀 Production Deployment

### Docker Compose (Recommended)

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8003:8003"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - COMPUTER_USE_CONTAINER_URL=http://computer-use:8080
    depends_on:
      - computer-use

  computer-use:
    image: anthropic/computer-use:latest
    ports:
      - "8080:8080"
    environment:
      - DISPLAY_WIDTH=1024
      - DISPLAY_HEIGHT=768
```

**Start:**
```bash
docker-compose up -d
```

---

## 📈 Monitoring

### View Container Logs
```bash
docker logs -f computer-use
```

### API Server Logs
Terminal shows:
```
🖥️  Executing native tool...
Computer tool: screenshot
✅ Native tool executed
```

### Test All Endpoints
```bash
# Screenshot
curl http://localhost:8080/screenshot

# Mouse
curl -X POST http://localhost:8080/mouse/move -H "Content-Type: application/json" -d '{"x":100,"y":100}'

# Click
curl -X POST http://localhost:8080/mouse/click -H "Content-Type: application/json" -d '{"button":"left"}'

# Keyboard
curl -X POST http://localhost:8080/keyboard/type -H "Content-Type: application/json" -d '{"text":"hello"}'
```

---

## ✅ Summary

You now have a **complete computer use implementation** with:

- ✅ **computer_20241022** - Browser automation, screenshot, mouse, keyboard
- ✅ **bash_20250124** - Shell command execution with optimized prompts
- ✅ **text_editor_20250728** - File operations (view/create/edit)
- ✅ **Docker integration** - Computer tool communicates with VNC container
- ✅ **Intelligent routing** - All tools route to correct native handlers
- ✅ **System prompt optimization** - Guides Claude to use tools efficiently

**Ready to test!** Start with the screenshot test, then move to more complex browser automation.
