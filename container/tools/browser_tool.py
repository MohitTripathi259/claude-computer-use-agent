"""
Browser Automation Tool using Playwright.

Provides browser control capabilities for the computer-use agent:
- Navigation
- Clicking elements
- Typing text
- Screenshots
- Scrolling
- Content extraction
"""

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Dict, Any, Optional, List
import base64
import asyncio
import logging
import os

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Manages a Playwright browser instance for automation.

    Provides methods for common browser operations that the agent
    can use to interact with web pages.
    """

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Playwright and launch browser."""
        if self._initialized:
            return

        logger.info("Initializing Playwright browser...")

        try:
            self.playwright = await async_playwright().start()

            # Launch Chromium in headed mode (for Xvfb screenshots)
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Headed mode required for Xvfb screenshots
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    # Removed '--disable-gpu' and '--disable-software-rasterizer'
                    # These flags prevented rendering to Xvfb display
                    '--window-size=1920,1080',
                    '--window-position=0,0'
                ]
            )

            # Create context with viewport
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # Create initial page
            self.page = await self.context.new_page()

            self._initialized = True
            logger.info("Browser initialized successfully")

        except Exception as e:
            logger.error(f"Browser initialization failed: {e}")
            raise

    async def cleanup(self):
        """Clean up browser resources."""
        logger.info("Cleaning up browser resources...")

        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self._initialized = False
            logger.info("Browser cleanup complete")

        except Exception as e:
            logger.error(f"Browser cleanup error: {e}")

    async def ensure_initialized(self):
        """Ensure browser is initialized before operations."""
        if not self._initialized:
            await self.initialize()

    async def execute_action(self, action: str, params: Dict[str, Any]) -> Dict:
        """
        Execute a browser action.

        Args:
            action: Action name (navigate, click, type, screenshot, etc.)
            params: Parameters for the action

        Returns:
            Dict with action result or error
        """
        await self.ensure_initialized()

        if not self.page:
            return {"error": "Browser not initialized"}

        try:
            if action == "navigate":
                return await self._navigate(params)

            elif action == "click":
                return await self._click(params)

            elif action == "type":
                return await self._type(params)

            elif action == "screenshot":
                return await self._screenshot(params)

            elif action == "scroll":
                return await self._scroll(params)

            elif action == "get_content":
                return await self._get_content(params)

            elif action == "wait":
                return await self._wait(params)

            elif action == "go_back":
                return await self._go_back()

            elif action == "go_forward":
                return await self._go_forward()

            elif action == "refresh":
                return await self._refresh()

            elif action == "get_url":
                return {"url": self.page.url}

            elif action == "get_title":
                return {"title": await self.page.title()}

            elif action == "evaluate":
                return await self._evaluate(params)

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Browser action '{action}' failed: {e}")
            return {"error": str(e)}

    async def _navigate(self, params: Dict) -> Dict:
        """Navigate to a URL."""
        url = params.get("url")
        if not url:
            return {"error": "URL is required"}

        logger.info(f"Navigating to: {url}")

        try:
            response = await self.page.goto(
                url,
                wait_until=params.get("wait_until", "domcontentloaded"),
                timeout=params.get("timeout", 30000)
            )

            return {
                "url": self.page.url,
                "title": await self.page.title(),
                "status": response.status if response else None
            }
        except Exception as e:
            return {"error": f"Navigation failed: {str(e)}"}

    async def _click(self, params: Dict) -> Dict:
        """Click an element by selector or coordinates."""
        logger.info(f"Click action with params: {params}")

        try:
            if "selector" in params:
                selector = params["selector"]
                await self.page.click(
                    selector,
                    timeout=params.get("timeout", 10000),
                    button=params.get("button", "left")
                )
                return {"clicked": selector}

            elif "x" in params and "y" in params:
                x, y = params["x"], params["y"]
                await self.page.mouse.click(x, y, button=params.get("button", "left"))
                return {"clicked_at": [x, y]}

            elif "text" in params:
                # Click by visible text
                text = params["text"]
                await self.page.get_by_text(text, exact=params.get("exact", False)).click(
                    timeout=params.get("timeout", 10000)
                )
                return {"clicked_text": text}

            else:
                return {"error": "Either 'selector', 'text', or 'x'/'y' coordinates required"}

        except Exception as e:
            return {"error": f"Click failed: {str(e)}"}

    async def _type(self, params: Dict) -> Dict:
        """Type text into an element or the active element."""
        text = params.get("text", "")

        try:
            if "selector" in params:
                selector = params["selector"]
                if params.get("clear", False):
                    await self.page.fill(selector, text)
                else:
                    await self.page.type(selector, text, delay=params.get("delay", 50))
                return {"typed": text, "selector": selector}
            else:
                # Type into currently focused element
                await self.page.keyboard.type(text, delay=params.get("delay", 50))
                return {"typed": text}

        except Exception as e:
            return {"error": f"Type failed: {str(e)}"}

    async def _screenshot(self, params: Dict) -> Dict:
        """Take a screenshot of the page."""
        try:
            screenshot_bytes = await self.page.screenshot(
                full_page=params.get("full_page", False),
                type="png"
            )

            return {
                "image_base64": base64.b64encode(screenshot_bytes).decode("utf-8"),
                "width": 1920,
                "height": 1080
            }

        except Exception as e:
            return {"error": f"Screenshot failed: {str(e)}"}

    async def _scroll(self, params: Dict) -> Dict:
        """Scroll the page."""
        direction = params.get("direction", "down")
        amount = params.get("amount", 500)

        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "left":
                await self.page.evaluate(f"window.scrollBy(-{amount}, 0)")
            elif direction == "right":
                await self.page.evaluate(f"window.scrollBy({amount}, 0)")
            elif direction == "top":
                await self.page.evaluate("window.scrollTo(0, 0)")
            elif direction == "bottom":
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            else:
                return {"error": f"Unknown scroll direction: {direction}"}

            return {"scrolled": direction, "amount": amount}

        except Exception as e:
            return {"error": f"Scroll failed: {str(e)}"}

    async def _get_content(self, params: Dict) -> Dict:
        """Get page content and text."""
        try:
            content = {
                "url": self.page.url,
                "title": await self.page.title(),
            }

            # Get visible text
            if params.get("text", True):
                text = await self.page.inner_text("body")
                # Limit text size
                max_size = params.get("max_text_size", 10000)
                if len(text) > max_size:
                    text = text[:max_size] + f"\n...[truncated at {max_size} chars]"
                content["text_content"] = text

            # Get HTML if requested
            if params.get("html", False):
                html = await self.page.content()
                max_size = params.get("max_html_size", 50000)
                if len(html) > max_size:
                    html = html[:max_size] + f"\n...[truncated at {max_size} chars]"
                content["html"] = html

            # Get links if requested
            if params.get("links", False):
                links = await self.page.eval_on_selector_all(
                    "a[href]",
                    "elements => elements.slice(0, 50).map(e => ({href: e.href, text: e.innerText.trim().slice(0, 100)}))"
                )
                content["links"] = links

            return content

        except Exception as e:
            return {"error": f"Get content failed: {str(e)}"}

    async def _wait(self, params: Dict) -> Dict:
        """Wait for element or time."""
        try:
            if "selector" in params:
                await self.page.wait_for_selector(
                    params["selector"],
                    timeout=params.get("timeout", 10000),
                    state=params.get("state", "visible")
                )
                return {"waited_for": params["selector"]}

            elif "seconds" in params:
                await asyncio.sleep(params["seconds"])
                return {"waited_seconds": params["seconds"]}

            elif "navigation" in params:
                await self.page.wait_for_load_state(params.get("state", "domcontentloaded"))
                return {"waited_for_navigation": True}

            else:
                await asyncio.sleep(1)
                return {"waited_seconds": 1}

        except Exception as e:
            return {"error": f"Wait failed: {str(e)}"}

    async def _go_back(self) -> Dict:
        """Navigate back."""
        await self.page.go_back()
        return {"url": self.page.url, "title": await self.page.title()}

    async def _go_forward(self) -> Dict:
        """Navigate forward."""
        await self.page.go_forward()
        return {"url": self.page.url, "title": await self.page.title()}

    async def _refresh(self) -> Dict:
        """Refresh the page."""
        await self.page.reload()
        return {"url": self.page.url, "title": await self.page.title()}

    async def _evaluate(self, params: Dict) -> Dict:
        """Evaluate JavaScript in the page."""
        script = params.get("script", "")
        if not script:
            return {"error": "Script is required"}

        result = await self.page.evaluate(script)
        return {"result": result}
