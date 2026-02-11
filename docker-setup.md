# Docker Setup for Anthropic Computer Use

## Option 1: Use Anthropic's Official Container (Recommended for Production)

### Step 1: Pull and Run Anthropic's Container

**Note**: Anthropic's official container image name may vary. Check their GitHub for the latest.

```bash
# If Anthropic provides an official image:
docker pull anthropic/computer-use:latest

# Run the container
docker run -d \
  --name computer-use \
  -p 8080:8080 \
  -p 5900:5900 \
  -e DISPLAY_WIDTH=1920 \
  -e DISPLAY_HEIGHT=1080 \
  anthropic/computer-use:latest
```

### Step 2: Verify Container is Running

```bash
# Check container status
docker ps | grep computer-use

# Test screenshot endpoint
curl http://localhost:8080/screenshot

# Expected response:
# {"base64_image": "iVBORw0KGgoAAAANS...", "success": true}
```

### Step 3: Test from Your API

```bash
# Your API will automatically use the container
# native_tool_handlers.py already has fallback to container URL

# Test via your API
curl -X POST http://localhost:8003/execute \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Take a screenshot",
    "max_turns": 3,
    "use_computer_tools": true
  }'
```

---

## Option 2: Build Your Own Computer Use Container

If Anthropic doesn't provide a public image, build one:

### Dockerfile for Computer Use Server

```dockerfile
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    xvfb \
    x11vnc \
    fluxbox \
    chromium-browser \
    scrot \
    xdotool \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install fastapi uvicorn pillow pyautogui mss

# Create app directory
WORKDIR /app

# Copy server code
COPY computer_use_server.py .

# Expose ports
EXPOSE 8080 5900

# Start X server and API
CMD Xvfb :99 -screen 0 1920x1080x24 & \
    x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -xkb & \
    DISPLAY=:99 fluxbox & \
    DISPLAY=:99 uvicorn computer_use_server:app --host 0.0.0.0 --port 8080
```

### computer_use_server.py

```python
"""
FastAPI server for computer use operations
Provides REST endpoints for screenshot, mouse, keyboard
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pyautogui
import mss
import base64
from io import BytesIO
from PIL import Image

app = FastAPI()

# Configure pyautogui
pyautogui.FAILSAFE = False

class MouseMove(BaseModel):
    x: int
    y: int

class MouseClick(BaseModel):
    button: str = "left"
    x: Optional[int] = None
    y: Optional[int] = None

class KeyboardType(BaseModel):
    text: str

class KeyboardKey(BaseModel):
    key: str

@app.get("/screenshot")
async def screenshot():
    """Capture screenshot and return as base64"""
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            return {
                "base64_image": img_base64,
                "width": img.width,
                "height": img.height,
                "success": True
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mouse/move")
async def mouse_move(data: MouseMove):
    """Move mouse to coordinates"""
    try:
        pyautogui.moveTo(data.x, data.y, duration=0.2)
        return {"success": True, "message": f"Moved to ({data.x}, {data.y})"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mouse/click")
async def mouse_click(data: MouseClick):
    """Click mouse button"""
    try:
        if data.x is not None and data.y is not None:
            pyautogui.click(data.x, data.y, button=data.button)
        else:
            pyautogui.click(button=data.button)
        return {"success": True, "message": f"{data.button} click"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/keyboard/type")
async def keyboard_type(data: KeyboardType):
    """Type text"""
    try:
        pyautogui.write(data.text, interval=0.05)
        return {"success": True, "message": f"Typed: {data.text[:50]}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/keyboard/key")
async def keyboard_key(data: KeyboardKey):
    """Press key"""
    try:
        pyautogui.press(data.key.lower())
        return {"success": True, "message": f"Pressed: {data.key}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mouse/position")
async def mouse_position():
    """Get current mouse position"""
    try:
        x, y = pyautogui.position()
        return {"x": x, "y": y, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "display": ":99"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### Build and Run

```bash
# Build the image
docker build -t computer-use-server .

# Run the container
docker run -d \
  --name computer-use \
  -p 8080:8080 \
  -p 5900:5900 \
  -e DISPLAY=:99 \
  computer-use-server

# Test
curl http://localhost:8080/health
curl http://localhost:8080/screenshot
```

---

## VNC Access (Optional)

Connect to VNC for visual monitoring:

```bash
# Port 5900 is exposed
# Use VNC client:
# - TigerVNC
# - RealVNC
# - TightVNC

# Connect to: localhost:5900
# No password required (for dev)
```

---

## Integration with Your API

Your `native_tool_handlers.py` already supports this! It tries local first, then falls back to container:

```python
# Line 307-347 in native_tool_handlers.py
def _computer_screenshot(self, container_url: str):
    # Try local first
    if COMPUTER_CONTROL_AVAILABLE:
        try:
            # Use pyautogui/mss locally
            ...
        except:
            pass

    # Fallback to container (THIS PART WILL BE USED)
    try:
        response = requests.get(f"{container_url}/screenshot")
        return response.json()
    except Exception as e:
        return {"error": str(e)}
```

**When pyautogui is NOT installed** (production container), it automatically uses the Docker container!

---

## Environment Variable

Already configured in `.env`:

```bash
COMPUTER_USE_CONTAINER_URL=http://localhost:8080
```

For ECS deployment:
```bash
# If running in same ECS task (sidecar)
COMPUTER_USE_CONTAINER_URL=http://localhost:8080

# If running as separate ECS service
COMPUTER_USE_CONTAINER_URL=http://computer-use-service:8080
```

---

## Next Steps

1. **Local Testing**:
   ```bash
   # Start computer-use container
   docker run -d -p 8080:8080 -p 5900:5900 --name computer-use computer-use-server

   # Start your API (it will detect and use the container)
   python api_server.py

   # Test
   curl -X POST http://localhost:8003/execute \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Take a screenshot", "use_computer_tools": true}'
   ```

2. **Verify Fallback**:
   ```bash
   # Check logs - should show:
   # "Local screenshot failed, trying container"
   # "Screenshot captured from container"
   ```

3. **Ready for ECS deployment**!
