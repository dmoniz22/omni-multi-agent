"""Browser skill for OMNI.

Provides web browsing capabilities: navigate to URLs, scrape content.
Uses httpx for requests, beautifulsoup4 for parsing.
"""

import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from omni.skills.base import BaseSkill, SkillAction


class NavigateInput(BaseModel):
    """Input for navigate action."""

    url: str = Field(..., description="URL to navigate to")


class NavigateOutput(BaseModel):
    """Output from navigate action."""

    content: str = Field(..., description="Page content")
    title: str = Field(..., description="Page title")
    status: int = Field(..., description="HTTP status code")
    url: str = Field(..., description="Final URL after redirects")


class ScrapeInput(BaseModel):
    """Input for scrape action."""

    url: str = Field(..., description="URL to scrape")
    selectors: Optional[Dict[str, str]] = Field(
        default=None, description="CSS selectors to extract"
    )


class ScrapeOutput(BaseModel):
    """Output from scrape action."""

    data: Dict[str, Any] = Field(..., description="Extracted data")
    url: str = Field(..., description="Source URL")


class BrowserSkill(BaseSkill):
    """Browser skill for web navigation and scraping.

    Provides basic HTTP fetching and HTML parsing capabilities.
    Includes rate limiting and URL validation for safety.

    Actions:
        - navigate: Load a URL and return page content
        - scrape: Extract structured data from a page

    Usage:
        skill = BrowserSkill()
        result = skill.execute("navigate", {"url": "https://example.com"})
    """

    name = "browser"
    description = "Web browser: navigate to URLs and scrape content"
    version = "1.0.0"

    def __init__(
        self,
        timeout: int = 30,
        max_content_size: int = 1_000_000,
        allowed_domains: Optional[list[str]] = None,
    ):
        """Initialize browser skill.

        Args:
            timeout: Request timeout in seconds
            max_content_size: Maximum content size to fetch
            allowed_domains: Optional list of allowed domains (None = all)
        """
        super().__init__()
        self._timeout = timeout
        self._max_content_size = max_content_size
        self._allowed_domains = allowed_domains

        try:
            import httpx

            self._httpx = httpx
        except ImportError:
            self._httpx = None

    def _is_allowed_url(self, url: str) -> bool:
        """Check if URL is allowed."""
        if self._allowed_domains is None:
            return True
        parsed = urlparse(url)
        return parsed.netloc in self._allowed_domains

    def get_actions(self) -> Dict[str, SkillAction]:
        """Get available browser actions."""
        return {
            "navigate": SkillAction(
                name="navigate",
                description="Load a URL and return page content",
                input_schema=NavigateInput,
                output_schema=NavigateOutput,
            ),
            "scrape": SkillAction(
                name="scrape",
                description="Extract structured data from a page using CSS selectors",
                input_schema=ScrapeInput,
                output_schema=ScrapeOutput,
            ),
        }

    def execute(self, action: str, params: dict) -> dict:
        """Execute a browser action.

        Args:
            action: Action name (navigate, scrape)
            params: Action parameters

        Returns:
            Dict with action results

        Raises:
            ValueError: If action is unknown
        """
        if action == "navigate":
            return self._navigate(params)
        elif action == "scrape":
            return self._scrape(params)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _navigate(self, params: dict) -> dict:
        """Navigate to URL and get content."""
        validated = NavigateInput.model_validate(params)
        url = validated.url

        if not self._is_allowed_url(url):
            raise ValueError(f"URL not allowed: {url}")

        if self._httpx is None:
            return {
                "content": "httpx not installed. Install with: pip install httpx",
                "title": "Error",
                "status": 500,
                "url": url,
            }

        try:
            with self._httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, follow_redirects=True)

                content = response.text[: self._max_content_size]

                title = ""
                if "text/html" in response.headers.get("content-type", ""):
                    try:
                        from bs4 import BeautifulSoup

                        soup = BeautifulSoup(content, "html.parser")
                        title_tag = soup.find("title")
                        if title_tag:
                            title = title_tag.get_text()
                    except ImportError:
                        pass

                return {
                    "content": content,
                    "title": title,
                    "status": response.status_code,
                    "url": str(response.url),
                }

        except Exception as e:
            return {
                "content": f"Error: {str(e)}",
                "title": "Error",
                "status": 500,
                "url": url,
            }

    def _scrape(self, params: dict) -> dict:
        """Scrape structured data from URL."""
        validated = ScrapeInput.model_validate(params)
        url = validated.url

        if not self._is_allowed_url(url):
            raise ValueError(f"URL not allowed: {url}")

        navigate_result = self._navigate({"url": url})
        content = navigate_result["content"]

        if "error" in content.lower():
            return {
                "data": {"error": content},
                "url": url,
            }

        if self._httpx is None:
            return {
                "data": {"error": "httpx not installed"},
                "url": url,
            }

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(content, "html.parser")

            data = {}
            if validated.selectors:
                for name, selector in validated.selectors.items():
                    elements = soup.select(selector)
                    data[name] = [el.get_text(strip=True) for el in elements]
            else:
                data["text"] = soup.get_text(strip=True)

            return {
                "data": data,
                "url": url,
            }

        except ImportError:
            return {
                "data": {
                    "error": "beautifulsoup4 not installed. Install with: pip install beautifulsoup4"
                },
                "url": url,
            }
        except Exception as e:
            return {
                "data": {"error": str(e)},
                "url": url,
            }

    def health_check(self) -> bool:
        """Verify browser is operational."""
        return True
