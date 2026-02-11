"""
FastAPI server for computer use operations
Provides REST endpoints for screenshot, mouse, keyboard control
Compatible with native_tool_handlers.py expectations
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64
import logging
from io import BytesIO
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Computer Use Server", version="1.0.0")

# Lazy import for display-dependent modules
def _get_pyautogui():
    """Lazy import pyautogui to avoid X display connection at module import time"""
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.1
    return pyautogui

def _get_mss():
    """Lazy import mss"""
    import mss
    return mss

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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Computer Use Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "screenshot": "/screenshot",
            "mouse_move": "/mouse/move",
            "mouse_click": "/mouse/click",
            "mouse_position": "/mouse/position",
            "keyboard_type": "/keyboard/type",
            "keyboard_key": "/keyboard/key"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "display": ":99",
        "service": "computer-use"
    }

@app.get("/screenshot")
async def screenshot():
    """
    Capture screenshot and return as base64

    Returns:
        {
            "base64_image": "...",
            "width": 1920,
            "height": 1080,
            "success": true
        }
    """
    try:
        logger.info("Capturing screenshot...")
        mss = _get_mss()

        with mss.mss() as sct:
            # Capture the primary monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            logger.info(f"Screenshot captured: {img.width}x{img.height}")

            return {
                "base64_image": img_base64,
                "width": img.width,
                "height": img.height,
                "success": True
            }
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mouse/move")
async def mouse_move(data: MouseMove):
    """
    Move mouse to coordinates

    Args:
        data: {"x": 100, "y": 200}

    Returns:
        {"success": true, "message": "Moved to (100, 200)"}
    """
    try:
        pyautogui = _get_pyautogui()
        logger.info(f"Moving mouse to ({data.x}, {data.y})")
        pyautogui.moveTo(data.x, data.y, duration=0.2)
        return {
            "success": True,
            "message": f"Moved to ({data.x}, {data.y})"
        }
    except Exception as e:
        logger.error(f"Mouse move failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mouse/click")
async def mouse_click(data: MouseClick):
    """
    Click mouse button at current or specified position

    Args:
        data: {"button": "left", "x": 100, "y": 200}

    Returns:
        {"success": true, "message": "left click at (100, 200)"}
    """
    try:
        pyautogui = _get_pyautogui()
        button_map = {
            "left": "left",
            "right": "right",
            "middle": "middle",
            "double": "left"
        }

        button = button_map.get(data.button, "left")
        clicks = 2 if data.button == "double" else 1

        if data.x is not None and data.y is not None:
            logger.info(f"{data.button} click at ({data.x}, {data.y})")
            pyautogui.click(data.x, data.y, button=button, clicks=clicks)
            message = f"{data.button} click at ({data.x}, {data.y})"
        else:
            logger.info(f"{data.button} click at current position")
            pyautogui.click(button=button, clicks=clicks)
            message = f"{data.button} click"

        return {
            "success": True,
            "message": message
        }
    except Exception as e:
        logger.error(f"Click failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mouse/position")
async def mouse_position():
    """
    Get current mouse position

    Returns:
        {"x": 100, "y": 200, "success": true}
    """
    try:
        pyautogui = _get_pyautogui()
        x, y = pyautogui.position()
        logger.info(f"Current mouse position: ({x}, {y})")
        return {
            "x": x,
            "y": y,
            "success": True
        }
    except Exception as e:
        logger.error(f"Get position failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/keyboard/type")
async def keyboard_type(data: KeyboardType):
    """
    Type text string

    Args:
        data: {"text": "Hello World"}

    Returns:
        {"success": true, "message": "Typed: Hello World"}
    """
    try:
        pyautogui = _get_pyautogui()
        logger.info(f"Typing text: {data.text[:50]}...")
        pyautogui.write(data.text, interval=0.05)
        return {
            "success": True,
            "message": f"Typed: {data.text[:50]}{'...' if len(data.text) > 50 else ''}"
        }
    except Exception as e:
        logger.error(f"Type failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/keyboard/key")
async def keyboard_key(data: KeyboardKey):
    """
    Press keyboard key

    Args:
        data: {"key": "enter"}

    Returns:
        {"success": true, "message": "Pressed: enter"}
    """
    try:
        pyautogui = _get_pyautogui()
        # Map common key names
        key_map = {
            "Return": "enter",
            "return": "enter",
            "Enter": "enter",
            "BackSpace": "backspace",
            "Tab": "tab",
            "Escape": "esc",
            "Delete": "delete",
            "Space": "space",
            "space": "space"
        }

        key = key_map.get(data.key, data.key.lower())
        logger.info(f"Pressing key: {key}")
        pyautogui.press(key)

        return {
            "success": True,
            "message": f"Pressed: {data.key}"
        }
    except Exception as e:
        logger.error(f"Key press failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
