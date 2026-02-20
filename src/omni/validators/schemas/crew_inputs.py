"""Input schemas for all department crews.

These schemas define the expected input format for each crew/department.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GitHubTaskInput(BaseModel):
    """Input schema for GitHub department crew."""

    query: str = Field(description="The GitHub-related task or question")
    repository: Optional[str] = Field(
        default=None, description="Specific repository to query (owner/repo format)"
    )
    operation: Optional[str] = Field(
        default=None,
        description="Specific operation: search_repos, get_repo, get_file, create_gist, list_issues",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Additional parameters for the operation"
    )


class ResearchTaskInput(BaseModel):
    """Input schema for Research department crew."""

    query: str = Field(description="Research topic or question")
    depth: str = Field(
        default="medium", description="Research depth: quick, medium, or comprehensive"
    )
    sources_required: int = Field(
        default=3, description="Minimum number of sources to retrieve", ge=1, le=20
    )
    focus_areas: List[str] = Field(
        default_factory=list, description="Specific aspects to focus on"
    )


class SocialTaskInput(BaseModel):
    """Input schema for Social department crew."""

    topic: str = Field(description="Topic to create social content about")
    platforms: List[str] = Field(
        description="Target platforms: twitter, linkedin, blog, etc."
    )
    tone: str = Field(
        default="professional",
        description="Content tone: professional, casual, humorous, etc.",
    )
    target_audience: Optional[str] = Field(
        default=None, description="Target audience description"
    )
    include_hashtags: bool = Field(
        default=True, description="Whether to include hashtags"
    )


class AnalysisTaskInput(BaseModel):
    """Input schema for Analysis department crew."""

    subject: str = Field(description="Subject to analyze")
    analysis_type: str = Field(
        description="Type of analysis: data, code, document, market, etc."
    )
    focus: List[str] = Field(
        default_factory=list, description="Specific aspects to analyze"
    )
    data_source: Optional[str] = Field(
        default=None, description="Source of data to analyze"
    )


class WritingTaskInput(BaseModel):
    """Input schema for Writing department crew."""

    topic: str = Field(description="Topic to write about")
    content_type: str = Field(
        description="Type of content: blog_post, article, documentation, email, etc."
    )
    style: str = Field(
        default="professional",
        description="Writing style: professional, creative, technical, etc.",
    )
    length: str = Field(
        default="medium", description="Approximate length: short, medium, long"
    )
    audience: Optional[str] = Field(default=None, description="Target audience")


class CodingTaskInput(BaseModel):
    """Input schema for Coding department crew."""

    task: str = Field(description="Coding task description")
    language: Optional[str] = Field(default=None, description="Programming language")
    framework: Optional[str] = Field(default=None, description="Framework to use")
    requirements: List[str] = Field(
        default_factory=list, description="Specific requirements or constraints"
    )
    test_code: bool = Field(default=False, description="Whether to include tests")
