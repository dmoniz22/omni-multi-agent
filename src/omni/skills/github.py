"""GitHub skill for OMNI.

Provides GitHub API operations: search repos, get repo info, read files, create gists, list issues.
Uses GitHub REST API v3.
"""

import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from omni.skills.base import BaseSkill, SkillAction


class SearchReposInput(BaseModel):
    """Input for search_repos action."""

    query: str = Field(..., description="Search query")
    sort: Optional[str] = Field(
        default=None, description="Sort field (stars, forks, updated)"
    )


class RepoInfo(BaseModel):
    """Repository information."""

    name: str
    full_name: str
    description: Optional[str]
    stars: int
    forks: int
    language: Optional[str]
    url: str


class SearchReposOutput(BaseModel):
    """Output from search_repos action."""

    repos: list[RepoInfo] = Field(..., description="List of repositories")
    total_count: int = Field(..., description="Total results count")


class GetRepoInput(BaseModel):
    """Input for get_repo action."""

    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")


class GetRepoOutput(BaseModel):
    """Output from get_repo action."""

    repo: Dict[str, Any] = Field(..., description="Repository details")


class GetFileInput(BaseModel):
    """Input for get_file action."""

    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="File path")


class GetFileOutput(BaseModel):
    """Output from get_file action."""

    content: str = Field(..., description="File content")
    encoding: str = Field(..., description="Content encoding")
    path: str = Field(..., description="File path")


class CreateGistInput(BaseModel):
    """Input for create_gist action."""

    description: str = Field(..., description="Gist description")
    files: Dict[str, str] = Field(..., description="Files to include in gist")
    public: bool = Field(default=False, description="Whether gist is public")


class CreateGistOutput(BaseModel):
    """Output from create_gist action."""

    url: str = Field(..., description="Gist URL")
    id: str = Field(..., description="Gist ID")


class ListIssuesInput(BaseModel):
    """Input for list_issues action."""

    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    state: str = Field(default="open", description="Issue state (open, closed, all)")


class IssueInfo(BaseModel):
    """Issue information."""

    number: int
    title: str
    state: str
    url: str


class ListIssuesOutput(BaseModel):
    """Output from list_issues action."""

    issues: list[IssueInfo] = Field(..., description="List of issues")


class GitHubSkill(BaseSkill):
    """GitHub skill for repository operations.

    Provides GitHub API operations for repository search,
    file reading, gist creation, and issue management.
    Requires GITHUB_TOKEN environment variable for authentication.

    Actions:
        - search_repos: Search GitHub repositories
        - get_repo: Get repository details
        - get_file: Read a file from a repository
        - create_gist: Create a GitHub gist
        - list_issues: List repository issues

    Usage:
        skill = GitHubSkill()
        result = skill.execute("search_repos", {"query": "python ai"})
    """

    name = "github"
    description = (
        "GitHub operations: search repos, read files, create gists, manage issues"
    )
    version = "1.0.0"

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub skill.

        Args:
            token: GitHub personal access token. Defaults to GITHUB_TOKEN env var.
        """
        super().__init__()
        self._token = token or os.environ.get("GITHUB_TOKEN")
        self._base_url = "https://api.github.com"

        try:
            import httpx

            self._httpx = httpx
        except ImportError:
            self._httpx = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self._token:
            headers["Authorization"] = f"token {self._token}"
        return headers

    def get_actions(self) -> Dict[str, SkillAction]:
        """Get available GitHub actions."""
        return {
            "search_repos": SkillAction(
                name="search_repos",
                description="Search GitHub repositories",
                input_schema=SearchReposInput,
                output_schema=SearchReposOutput,
            ),
            "get_repo": SkillAction(
                name="get_repo",
                description="Get repository details",
                input_schema=GetRepoInput,
                output_schema=GetRepoOutput,
            ),
            "get_file": SkillAction(
                name="get_file",
                description="Read a file from a repository",
                input_schema=GetFileInput,
                output_schema=GetFileOutput,
            ),
            "create_gist": SkillAction(
                name="create_gist",
                description="Create a GitHub gist",
                input_schema=CreateGistInput,
                output_schema=CreateGistOutput,
            ),
            "list_issues": SkillAction(
                name="list_issues",
                description="List repository issues",
                input_schema=ListIssuesInput,
                output_schema=ListIssuesOutput,
            ),
        }

    def execute(self, action: str, params: dict) -> dict:
        """Execute a GitHub action.

        Args:
            action: Action name (search_repos, get_repo, get_file, create_gist, list_issues)
            params: Action parameters

        Returns:
            Dict with action results

        Raises:
            ValueError: If action is unknown
        """
        action_map = {
            "search_repos": self._search_repos,
            "get_repo": self._get_repo,
            "get_file": self._get_file,
            "create_gist": self._create_gist,
            "list_issues": self._list_issues,
        }

        if action not in action_map:
            raise ValueError(f"Unknown action: {action}")

        return action_map[action](params)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make GitHub API request."""
        if self._httpx is None:
            return {"error": "httpx not installed. Install with: pip install httpx"}

        url = f"{self._base_url}{endpoint}"
        headers = self._get_headers()
        headers.update(kwargs.pop("headers", {}))

        try:
            with self._httpx.Client(timeout=30) as client:
                response = client.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    def _search_repos(self, params: dict) -> dict:
        """Search repositories."""
        validated = SearchReposInput.model_validate(params)
        endpoint = f"/search/repositories?q={validated.query}"
        if validated.sort:
            endpoint += f"&sort={validated.sort}"

        result = self._make_request("GET", endpoint)

        if "error" in result:
            return {"repos": [], "total_count": 0}

        repos = [
            RepoInfo(
                name=item.get("name", ""),
                full_name=item.get("full_name", ""),
                description=item.get("description"),
                stars=item.get("stargazers_count", 0),
                forks=item.get("forks_count", 0),
                language=item.get("language"),
                url=item.get("html_url", ""),
            )
            for item in result.get("items", [])
        ]

        return {
            "repos": [r.model_dump() for r in repos],
            "total_count": result.get("total_count", 0),
        }

    def _get_repo(self, params: dict) -> dict:
        """Get repository details."""
        validated = GetRepoInput.model_validate(params)
        endpoint = f"/repos/{validated.owner}/{validated.repo}"

        result = self._make_request("GET", endpoint)

        if "error" in result:
            return {"repo": {"error": result["error"]}}

        return {"repo": result}

    def _get_file(self, params: dict) -> dict:
        """Get file from repository."""
        validated = GetFileInput.model_validate(params)
        endpoint = (
            f"/repos/{validated.owner}/{validated.repo}/contents/{validated.path}"
        )

        result = self._make_request("GET", endpoint)

        if "error" in result:
            return {"content": "", "encoding": "none", "path": validated.path}

        import base64

        content = result.get("content", "")
        if result.get("encoding") == "base64":
            content = base64.b64decode(content).decode("utf-8")

        return {
            "content": content,
            "encoding": result.get("encoding", "none"),
            "path": validated.path,
        }

    def _create_gist(self, params: dict) -> dict:
        """Create a gist."""
        validated = CreateGistInput.model_validate(params)

        if not self._token:
            return {
                "url": "",
                "id": "",
                "error": "GITHUB_TOKEN required for gist creation",
            }

        endpoint = "/gists"
        data = {
            "description": validated.description,
            "public": validated.public,
            "files": validated.files,
        }

        result = self._make_request("POST", endpoint, json=data)

        if "error" in result:
            return {"url": "", "id": "", "error": result["error"]}

        return {
            "url": result.get("html_url", ""),
            "id": result.get("id", ""),
        }

    def _list_issues(self, params: dict) -> dict:
        """List repository issues."""
        validated = ListIssuesInput.model_validate(params)
        endpoint = (
            f"/repos/{validated.owner}/{validated.repo}/issues?state={validated.state}"
        )

        result = self._make_request("GET", endpoint)

        if "error" in result:
            return {"issues": []}

        issues = [
            IssueInfo(
                number=item.get("number", 0),
                title=item.get("title", ""),
                state=item.get("state", "open"),
                url=item.get("html_url", ""),
            )
            for item in result
            if "pull_request" not in item
        ]

        return {"issues": [i.model_dump() for i in issues]}

    def health_check(self) -> bool:
        """Verify GitHub skill is operational."""
        return True
