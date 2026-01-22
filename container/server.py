"""
Tool Execution Server - Runs inside the container.

This server receives tool calls from the Claude agent and executes them
in the containerized environment. It provides endpoints for:
- Bash command execution
- Browser automation (Playwright)
- File operations
- Screenshots
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import base64
import os
import logging

from tools.bash_tool import execute_bash
from tools.browser_tool import BrowserManager
from tools.file_tool import read_file, write_file, list_directory
from tools.screenshot_tool import take_screenshot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Computer-Use Tool Server",
    description="Executes tool calls from Claude computer-use agent",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize browser manager (singleton)
browser_manager = BrowserManager()


# ===================
# Request/Response Models
# ===================

class BashRequest(BaseModel):
    """Request to execute a bash command."""
    command: str
    timeout: int = 120
    working_dir: Optional[str] = "/workspace"


class BashResponse(BaseModel):
    """Response from bash execution."""
    stdout: str
    stderr: str
    return_code: int


class BrowserRequest(BaseModel):
    """Request for browser actions."""
    action: str  # navigate, click, type, screenshot, scroll, get_content, wait, go_back
    params: Dict[str, Any] = {}


class BrowserResponse(BaseModel):
    """Response from browser action."""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FileReadRequest(BaseModel):
    """Request to read a file."""
    path: str


class FileWriteRequest(BaseModel):
    """Request to write a file."""
    path: str
    content: str


class ScreenshotResponse(BaseModel):
    """Response with screenshot data."""
    image_base64: str
    width: int
    height: int


# ===================
# Endpoints
# ===================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "display": os.environ.get("DISPLAY", "not set"),
        "workspace": "/workspace",
        "browser_initialized": browser_manager.page is not None
    }


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Computer-Use Tool Server",
        "version": "1.0.0",
        "endpoints": {
            "bash": "POST /tools/bash",
            "browser": "POST /tools/browser",
            "file_read": "POST /tools/file/read",
            "file_write": "POST /tools/file/write",
            "file_list": "GET /tools/file/list",
            "screenshot": "GET /tools/screenshot"
        }
    }


# --- Bash Tool ---

@app.post("/tools/bash", response_model=BashResponse)
async def bash_endpoint(request: BashRequest):
    """
    Execute a bash command and return the result.

    The command runs in the workspace directory by default.
    Output is captured and returned.
    """
    logger.info(f"Executing bash command: {request.command[:100]}...")

    try:
        result = await execute_bash(
            request.command,
            timeout=request.timeout,
            working_dir=request.working_dir
        )
        return BashResponse(**result)
    except Exception as e:
        logger.error(f"Bash execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Browser Tool ---

@app.post("/tools/browser")
async def browser_endpoint(request: BrowserRequest):
    """
    Execute browser actions.

    Supported actions:
    - navigate: Go to a URL (params: url)
    - click: Click element (params: selector OR x, y)
    - type: Type text (params: text, selector?)
    - screenshot: Take screenshot (params: full_page?)
    - scroll: Scroll page (params: direction, amount)
    - get_content: Get page content
    - wait: Wait for element/time (params: selector?, seconds?)
    - go_back: Navigate back
    - go_forward: Navigate forward
    """
    logger.info(f"Browser action: {request.action}")

    try:
        result = await browser_manager.execute_action(request.action, request.params)

        if "error" in result:
            return {"status": "error", "error": result["error"]}

        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Browser action error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- File Tools ---

@app.post("/tools/file/read")
async def file_read_endpoint(request: FileReadRequest):
    """Read a file from the workspace."""
    logger.info(f"Reading file: {request.path}")

    try:
        content = await read_file(request.path)
        return {"content": content, "path": request.path}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {request.path}")
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Access denied: {request.path}")
    except Exception as e:
        logger.error(f"File read error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/file/write")
async def file_write_endpoint(request: FileWriteRequest):
    """Write content to a file in the workspace."""
    logger.info(f"Writing file: {request.path}")

    try:
        await write_file(request.path, request.content)
        return {"status": "success", "path": request.path, "size": len(request.content)}
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Access denied: {request.path}")
    except Exception as e:
        logger.error(f"File write error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools/file/list")
async def file_list_endpoint(path: str = "/workspace"):
    """List directory contents."""
    logger.info(f"Listing directory: {path}")

    try:
        files = await list_directory(path)
        return {"path": path, "files": files}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
    except Exception as e:
        logger.error(f"Directory list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Screenshot Tool ---

@app.get("/tools/screenshot")
async def screenshot_endpoint():
    """Take a screenshot of the current display."""
    logger.info("Taking screenshot of display")

    try:
        screenshot_data = await take_screenshot()

        if "error" in screenshot_data:
            raise HTTPException(status_code=500, detail=screenshot_data["error"])

        return ScreenshotResponse(**screenshot_data)
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================
# Lifecycle Events
# ===================

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Starting Computer-Use Tool Server...")

    # Initialize browser
    try:
        await browser_manager.initialize()
        logger.info("Browser initialized successfully")
    except Exception as e:
        logger.warning(f"Browser initialization deferred: {e}")

    logger.info("Tool Server ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Tool Server...")

    try:
        await browser_manager.cleanup()
        logger.info("Browser cleaned up")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
