"""
Screenshot Tool.

Takes screenshots of the virtual display (Xvfb) using scrot or pillow.
This captures what's currently visible on the desktop, including
browser windows and any GUI applications.
"""

import subprocess
import base64
import asyncio
import os
from typing import Dict
from PIL import Image
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Screenshot storage location (temp for processing)
SCREENSHOT_DIR = "/tmp/screenshots"

# Persistent storage location (mounted to local machine)
PERSISTENT_SCREENSHOT_DIR = "/screenshots"


async def take_screenshot(
    display: str = ":99",
    filename: str = "screenshot.png"
) -> Dict:
    """
    Take a screenshot of the current display.

    Uses scrot command-line tool to capture the Xvfb display.

    Args:
        display: X display to capture (default: :99)
        filename: Output filename (saved in /tmp/screenshots)

    Returns:
        Dict with:
        - image_base64: Base64 encoded PNG image
        - width: Image width in pixels
        - height: Image height in pixels
        - error: Error message if failed
    """
    # Ensure screenshot directory exists
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    output_path = os.path.join(SCREENSHOT_DIR, filename)

    logger.info(f"Taking screenshot of display {display}")

    try:
        # Method 1: Use scrot (preferred)
        result = await _take_screenshot_scrot(display, output_path)
        if result:
            return result

        # Method 2: Fallback to import (ImageMagick)
        result = await _take_screenshot_import(display, output_path)
        if result:
            return result

        return {"error": "No screenshot method available"}

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return {"error": str(e)}


async def _take_screenshot_scrot(display: str, output_path: str) -> Dict:
    """Take screenshot using scrot."""
    try:
        process = await asyncio.create_subprocess_exec(
            'scrot', '-o', output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, 'DISPLAY': display}
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=10
        )

        if process.returncode != 0:
            logger.warning(f"scrot failed: {stderr.decode()}")
            return None

        return await _read_screenshot(output_path)

    except FileNotFoundError:
        logger.debug("scrot not found")
        return None
    except asyncio.TimeoutError:
        logger.warning("scrot timed out")
        return None
    except Exception as e:
        logger.debug(f"scrot error: {e}")
        return None


async def _take_screenshot_import(display: str, output_path: str) -> Dict:
    """Take screenshot using ImageMagick import."""
    try:
        process = await asyncio.create_subprocess_exec(
            'import', '-window', 'root', output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, 'DISPLAY': display}
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=10
        )

        if process.returncode != 0:
            logger.warning(f"import failed: {stderr.decode()}")
            return None

        return await _read_screenshot(output_path)

    except FileNotFoundError:
        logger.debug("import (ImageMagick) not found")
        return None
    except asyncio.TimeoutError:
        logger.warning("import timed out")
        return None
    except Exception as e:
        logger.debug(f"import error: {e}")
        return None


async def _read_screenshot(filepath: str) -> Dict:
    """Read screenshot file and return as base64."""
    if not os.path.exists(filepath):
        return {"error": f"Screenshot file not created: {filepath}"}

    with open(filepath, 'rb') as f:
        image_data = f.read()

    # Get dimensions using PIL
    img = Image.open(io.BytesIO(image_data))
    width, height = img.size

    logger.info(f"Screenshot captured: {width}x{height}")

    # Save a copy to persistent storage with timestamp
    saved_path = await _save_screenshot_persistent(image_data)
    if saved_path:
        logger.info(f"Screenshot saved to: {saved_path}")

    return {
        "image_base64": base64.b64encode(image_data).decode('utf-8'),
        "width": width,
        "height": height,
        "saved_path": saved_path
    }


async def _save_screenshot_persistent(image_data: bytes) -> str:
    """Save screenshot to persistent storage with timestamp."""
    try:
        # Ensure persistent directory exists
        os.makedirs(PERSISTENT_SCREENSHOT_DIR, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(PERSISTENT_SCREENSHOT_DIR, filename)

        # Save the file
        with open(filepath, 'wb') as f:
            f.write(image_data)

        return filepath
    except Exception as e:
        logger.warning(f"Failed to save persistent screenshot: {e}")
        return None


async def take_region_screenshot(
    x: int,
    y: int,
    width: int,
    height: int,
    display: str = ":99"
) -> Dict:
    """
    Take a screenshot of a specific region.

    Args:
        x: Left coordinate
        y: Top coordinate
        width: Width of region
        height: Height of region
        display: X display

    Returns:
        Dict with image_base64, width, height
    """
    output_path = os.path.join(SCREENSHOT_DIR, "region_screenshot.png")

    try:
        # Use scrot with geometry
        process = await asyncio.create_subprocess_exec(
            'scrot', '-a', f'{x},{y},{width},{height}', '-o', output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, 'DISPLAY': display}
        )

        await asyncio.wait_for(process.communicate(), timeout=10)

        if process.returncode == 0:
            return await _read_screenshot(output_path)

        # Fallback: take full screenshot and crop
        full_result = await take_screenshot(display)
        if "error" in full_result:
            return full_result

        # Decode and crop
        image_data = base64.b64decode(full_result["image_base64"])
        img = Image.open(io.BytesIO(image_data))
        cropped = img.crop((x, y, x + width, y + height))

        # Encode cropped image
        buffer = io.BytesIO()
        cropped.save(buffer, format='PNG')
        cropped_data = buffer.getvalue()

        return {
            "image_base64": base64.b64encode(cropped_data).decode('utf-8'),
            "width": width,
            "height": height
        }

    except Exception as e:
        return {"error": str(e)}
