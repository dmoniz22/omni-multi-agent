"""Search skill for OMNI.

Provides web search capabilities using DuckDuckGo (local-first, no API key required).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from omni.skills.base import BaseSkill, SkillAction


class WebSearchInput(BaseModel):
    """Input for web search action."""

    query: str = Field(..., description="Search query")
    num_results: int = Field(default=5, description="Number of results to return")


class SearchResult(BaseModel):
    """A single search result."""

    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    snippet: str = Field(..., description="Result snippet")


class WebSearchOutput(BaseModel):
    """Output from web search action."""

    results: List[SearchResult] = Field(..., description="Search results")
    query: str = Field(..., description="Original query")


class NewsSearchInput(BaseModel):
    """Input for news search action."""

    query: str = Field(..., description="Search query")
    recency: Optional[str] = Field(
        default=None, description="Recency filter (day, week, month)"
    )


class NewsResult(BaseModel):
    """A single news article."""

    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="News source")
    published: Optional[str] = Field(default=None, description="Publication date")


class NewsSearchOutput(BaseModel):
    """Output from news search action."""

    articles: List[NewsResult] = Field(..., description="News articles")
    query: str = Field(..., description="Original query")


class SearchSkill(BaseSkill):
    """Search skill for web and news searches.

    Uses DuckDuckGo for privacy-respecting local-first search.
    No API keys required.

    Actions:
        - web_search: Perform a web search
        - news_search: Search news articles

    Usage:
        skill = SearchSkill()
        result = skill.execute("web_search", {"query": "latest AI news"})
    """

    name = "search"
    description = "Web and news search capabilities"
    version = "1.0.0"

    def __init__(self):
        """Initialize search skill."""
        super().__init__()
        self._ddg_available = self._check_ddg()

    def _check_ddg(self) -> bool:
        """Check if DuckDuckGo is available."""
        try:
            from duckduckgo_search import DDGS

            return True
        except ImportError:
            return False

    def get_actions(self) -> Dict[str, SkillAction]:
        """Get available search actions."""
        return {
            "web_search": SkillAction(
                name="web_search",
                description="Perform a web search",
                input_schema=WebSearchInput,
                output_schema=WebSearchOutput,
            ),
            "news_search": SkillAction(
                name="news_search",
                description="Search for news articles",
                input_schema=NewsSearchInput,
                output_schema=NewsSearchOutput,
            ),
        }

    def execute(self, action: str, params: dict) -> dict:
        """Execute a search action.

        Args:
            action: Action name (web_search, news_search)
            params: Action parameters

        Returns:
            Dict with action results

        Raises:
            ValueError: If action is unknown or service unavailable
        """
        if action == "web_search":
            return self._web_search(params)
        elif action == "news_search":
            return self._news_search(params)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _web_search(self, params: dict) -> dict:
        """Perform web search."""
        validated = WebSearchInput.model_validate(params)

        if not self._ddg_available:
            return {
                "results": [
                    {
                        "title": "DuckDuckGo not installed",
                        "url": "https://duckduckgo.com",
                        "snippet": "Install duckduckgo-search package to enable web search: pip install duckduckgo-search",
                    }
                ],
                "query": validated.query,
            }

        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddg:
                results = list(
                    ddg.text(validated.query, max_results=validated.num_results)
                )

            search_results = [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                )
                for r in results
            ]

            return {
                "results": [r.model_dump() for r in search_results],
                "query": validated.query,
            }
        except Exception as e:
            return {
                "results": [
                    {
                        "title": "Search error",
                        "url": "",
                        "snippet": f"Error performing search: {str(e)}",
                    }
                ],
                "query": validated.query,
            }

    def _news_search(self, params: dict) -> dict:
        """Search news articles."""
        validated = NewsSearchInput.model_validate(params)

        if not self._ddg_available:
            return {
                "articles": [
                    {
                        "title": "DuckDuckGo not installed",
                        "url": "https://duckduckgo.com",
                        "source": "System",
                        "published": None,
                    }
                ],
                "query": validated.query,
            }

        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddg:
                kwargs = {"max_results": 5}
                if validated.recency:
                    kwargs["timing"] = validated.recency

                results = list(ddg.news(validated.query, **kwargs))

            articles = [
                NewsResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    source=r.get("source", ""),
                    published=r.get("date", None),
                )
                for r in results
            ]

            return {
                "articles": [a.model_dump() for a in articles],
                "query": validated.query,
            }
        except Exception as e:
            return {
                "articles": [
                    {
                        "title": "News search error",
                        "url": "",
                        "source": "System",
                        "published": None,
                    }
                ],
                "query": validated.query,
            }

    def health_check(self) -> bool:
        """Verify search is operational."""
        return True
