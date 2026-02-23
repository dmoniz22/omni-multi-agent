"""Browser skill for OMNI.

Provides web browsing capabilities with Playwright for full browser automation.
Supports navigation, scraping, clicking, form filling, and screenshots.
"""

import base64
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from omni.skills.base import BaseSkill, SkillAction
from omni.core.logging import get_logger

logger = get_logger(__name__)


class NavigateInput(BaseModel):
    """Input for navigate action."""

    url: str = Field(..., description="URL to navigate to")
    wait_for: Optional[str] = Field(
        default=None, description="Selector or text to wait for"
    )
    timeout: int = Field(default=30000, description="Timeout in milliseconds")


class ClickInput(BaseModel):
    """Input for click action."""

    selector: str = Field(..., description="CSS selector to click")
    timeout: int = Field(default=30000, description="Timeout in milliseconds")


class TypeInput(BaseModel):
    """Input for type action."""

    selector: str = Field(..., description="CSS selector to type into")
    text: str = Field(..., description="Text to type")
    clear_first: bool = Field(default=True, description="Clear field before typing")


class PressInput(BaseModel):
    """Input for press action."""

    key: str = Field(..., description="Key to press (enter, escape, etc)")
    selector: Optional[str] = Field(
        default=None, description="Optional selector to focus first"
    )


class ScreenshotInput(BaseModel):
    """Input for screenshot action."""

    path: Optional[str] = Field(
        default=None, description="Path to save screenshot (optional)"
    )
    full_page: bool = Field(
        default=False, description="Capture full page or just viewport"
    )


class ScrapeInput(BaseModel):
    """Input for scrape action."""

    url: str = Field(..., description="URL to scrape")
    selectors: Optional[Dict[str, str]] = Field(
        default=None, description="CSS selectors to extract"
    )


class EvaluateInput(BaseModel):
    """Input for evaluate action."""

    script: str = Field(..., description="JavaScript to execute")
    selector: Optional[str] = Field(
        default=None, description="Optional selector to pass as argument"
    )


class GetHTMLInput(BaseModel):
    """Input for get_html action."""

    selector: Optional[str] = Field(
        default=None, description="Optional selector (default: whole page)"
    )


class BrowserSkill(BaseSkill):
    """Browser skill with Playwright for full browser automation.

    Provides powerful browser control including:
    - Navigation with JavaScript rendering
    - Clicking elements
    - Typing in forms
    - Taking screenshots
    - Executing JavaScript

    Actions:
        - navigate: Load a URL (supports JS)
        - click: Click an element
        - type: Type text into an input
        - press: Press a keyboard key
        - screenshot: Take a screenshot
        - scrape: Extract structured data (supports JS)
        - evaluate: Execute JavaScript
        - get_html: Get page HTML

    Usage:
        skill = BrowserSkill()
        skill.execute("navigate", {"url": "https://example.com"})
        skill.execute("click", {"selector": "#submit-button"})
        skill.execute("type", {"selector": "#search", "text": "hello"})
        skill.execute("screenshot", {"path": "screenshot.png"})
    """

    name = "browser"
    description = "Full browser automation with Playwright"
    version = "2.0.0"

    def __init__(self):
        """Initialize browser skill."""
        super().__init__()
        self._playwright = None
        self._browser = None
        self._page = None
        self._context = None

    def _get_playwright(self):
        """Get or initialize Playwright."""
        if self._playwright is None:
            try:
                from playwright.sync_api import sync_playwright

                self._playwright = sync_playwright().start()
            except ImportError:
                logger.warning(
                    "Playwright not installed. Install with: pip install playwright"
                )
                return None
        return self._playwright

    def _get_page(self):
        """Get or create a browser page."""
        if self._page is None:
            pw = self._get_playwright()
            if pw is None:
                raise RuntimeError(
                    "Playwright not available. Run: pip install playwright"
                )

            try:
                self._browser = pw.chromium.launch(headless=True)
                self._context = self._browser.new_context(
                    viewport={"width": 1280, "height": 720}
                )
                self._page = self._context.new_page()
            except Exception as e:
                logger.error(f"Failed to launch browser: {e}")
                raise RuntimeError(f"Failed to launch browser: {e}")

        return self._page

    def close(self):
        """Close the browser."""
        if self._page:
            self._page.close()
            self._page = None
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def get_actions(self) -> Dict[str, SkillAction]:
        """Get available browser actions."""
        return {
            "navigate": SkillAction(
                name="navigate",
                description="Navigate to URL (supports JavaScript)",
                input_schema=NavigateInput,
            ),
            "click": SkillAction(
                name="click",
                description="Click an element by CSS selector",
                input_schema=ClickInput,
            ),
            "type": SkillAction(
                name="type",
                description="Type text into an input field",
                input_schema=TypeInput,
            ),
            "press": SkillAction(
                name="press",
                description="Press a keyboard key",
                input_schema=PressInput,
            ),
            "screenshot": SkillAction(
                name="screenshot",
                description="Take a screenshot",
                input_schema=ScreenshotInput,
            ),
            "scrape": SkillAction(
                name="scrape",
                description="Extract structured data from page (supports JavaScript)",
                input_schema=ScrapeInput,
            ),
            "evaluate": SkillAction(
                name="evaluate",
                description="Execute JavaScript on the page",
                input_schema=EvaluateInput,
            ),
            "get_html": SkillAction(
                name="get_html",
                description="Get page HTML",
                input_schema=GetHTMLInput,
            ),
        }

    def execute(self, action: str, params: dict) -> dict:
        """Execute a browser action.

        Args:
            action: Action name
            params: Action parameters

        Returns:
            Dict with action results
        """
        try:
            if action == "navigate":
                return self._navigate(params)
            elif action == "click":
                return self._click(params)
            elif action == "type":
                return self._type(params)
            elif action == "press":
                return self._press(params)
            elif action == "screenshot":
                return self._screenshot(params)
            elif action == "scrape":
                return self._scrape(params)
            elif action == "evaluate":
                return self._evaluate(params)
            elif action == "get_html":
                return self._get_html(params)
            else:
                raise ValueError(f"Unknown action: {action}")
        except RuntimeError as e:
            if "Playwright not available" in str(e):
                return self._fallback_navigate(params)
            raise

    def _navigate(self, params: dict) -> dict:
        """Navigate to URL."""
        validated = NavigateInput.model_validate(params)
        page = self._get_page()

        try:
            if validated.wait_for:
                response = page.goto(
                    validated.url,
                    wait_until="domcontentloaded",
                    timeout=validated.timeout,
                )
                page.wait_for_selector(validated.wait_for, timeout=validated.timeout)
            else:
                response = page.goto(
                    validated.url,
                    wait_until="networkidle",
                    timeout=validated.timeout,
                )

            title = page.title()
            url = page.url

            return {
                "success": True,
                "url": url,
                "title": title,
                "status": response.status if response else 200,
                "message": f"Navigated to {url}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": validated.url,
            }

    def _click(self, params: dict) -> dict:
        """Click an element."""
        validated = ClickInput.model_validate(params)
        page = self._get_page()

        try:
            page.click(validated.selector, timeout=validated.timeout)
            return {
                "success": True,
                "selector": validated.selector,
                "message": f"Clicked {validated.selector}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "selector": validated.selector,
            }

    def _type(self, params: dict) -> dict:
        """Type text into input."""
        validated = TypeInput.model_validate(params)
        page = self._get_page()

        try:
            if validated.clear_first:
                page.fill(validated.selector, validated.text)
            else:
                page.type(validated.selector, validated.text)
            return {
                "success": True,
                "selector": validated.selector,
                "text": validated.text,
                "message": f"Typed into {validated.selector}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "selector": validated.selector,
            }

    def _press(self, params: dict) -> dict:
        """Press a key."""
        validated = PressInput.model_validate(params)
        page = self._get_page()

        try:
            if validated.selector:
                page.focus(validated.selector)
            page.keyboard.press(validated.key)
            return {
                "success": True,
                "key": validated.key,
                "message": f"Pressed {validated.key}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _screenshot(self, params: dict) -> dict:
        """Take a screenshot."""
        validated = ScreenshotInput.model_validate(params)
        page = self._get_page()

        try:
            if validated.path:
                page.screenshot(path=validated.path, full_page=validated.full_page)
                return {
                    "success": True,
                    "path": validated.path,
                    "message": f"Screenshot saved to {validated.path}",
                }
            else:
                screenshot_bytes = page.screenshot(
                    full_page=validated.full_page, type="png"
                )
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
                return {
                    "success": True,
                    "screenshot": screenshot_b64,
                    "message": "Screenshot captured (base64)",
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _scrape(self, params: dict) -> dict:
        """Scrape structured data."""
        validated = ScrapeInput.model_validate(params)

        if not hasattr(self, "_page") or self._page is None:
            nav_result = self._navigate({"url": validated.url})
            if not nav_result.get("success"):
                return nav_result

        page = self._get_page()

        try:
            data = {}
            if validated.selectors:
                for name, selector in validated.selectors.items():
                    elements = page.query_selector_all(selector)
                    data[name] = [el.inner_text() for el in elements if el.is_visible()]
            else:
                data["text"] = page.content()

            return {
                "success": True,
                "data": data,
                "url": page.url,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _evaluate(self, params: dict) -> dict:
        """Execute JavaScript."""
        validated = EvaluateInput.model_validate(params)
        page = self._get_page()

        try:
            if validated.selector:
                element = page.query_selector(validated.selector)
                if element:
                    result = page.evaluate(
                        validated.script,
                        element,
                    )
                else:
                    return {
                        "success": False,
                        "error": f"Selector not found: {validated.selector}",
                    }
            else:
                result = page.evaluate(validated.script)

            return {
                "success": True,
                "result": str(result),
                "message": "Script executed",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _get_html(self, params: dict) -> dict:
        """Get page HTML."""
        validated = GetHTMLInput.model_validate(params)
        page = self._get_page()

        try:
            if validated.selector:
                element = page.query_selector(validated.selector)
                html = element.inner_html() if element else ""
            else:
                html = page.content()

            return {
                "success": True,
                "html": html,
                "url": page.url,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _fallback_navigate(self, params: dict) -> dict:
        """Fallback to httpx if Playwright not available."""
        try:
            import httpx
            from bs4 import BeautifulSoup

            url = params.get("url", "")
            with httpx.Client(timeout=30) as client:
                response = client.get(url, follow_redirects=True)
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.string if soup.title else ""

                return {
                    "success": True,
                    "url": str(response.url),
                    "title": title,
                    "status": response.status_code,
                    "content": response.text[:10000],
                    "message": "Note: Using fallback httpx (no JavaScript support)",
                }
        except ImportError:
            return {
                "success": False,
                "error": "Neither Playwright nor httpx available. Install one of them.",
            }

    def health_check(self) -> bool:
        """Verify browser is operational."""
        try:
            pw = self._get_playwright()
            if pw:
                pw.chromium.launch(headless=True)
                return True
            return False
        except Exception:
            return False
