"""Output schemas for all department crews.

These schemas define the expected output format from each crew/department.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    """Source information for research or analysis."""

    title: str = Field(description="Source title")
    url: str = Field(description="Source URL")
    snippet: Optional[str] = Field(default=None, description="Relevant excerpt")


class GitHubOutput(BaseModel):
    """Output schema for GitHub department crew."""

    success: bool = Field(description="Whether the operation succeeded")
    operation: str = Field(description="Operation performed")
    result: Any = Field(description="Result data from the operation")
    repository: Optional[str] = Field(default=None, description="Repository used")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ResearchReport(BaseModel):
    """Output schema for Research department crew."""

    summary: str = Field(description="Summary of findings")
    findings: List[str] = Field(description="Key findings")
    sources: List[Source] = Field(description="Sources cited")
    depth: str = Field(description="Research depth achieved")
    gaps: List[str] = Field(
        default_factory=list, description="Areas needing more research"
    )


class SocialContentOutput(BaseModel):
    """Output schema for Social department crew."""

    contents: Dict[str, str] = Field(
        description="Content for each platform (platform -> content)"
    )
    hashtags: List[str] = Field(default_factory=list, description="Hashtags used")
    tone: str = Field(description="Tone used in content")


class AnalysisReport(BaseModel):
    """Output schema for Analysis department crew."""

    summary: str = Field(description="Summary of analysis")
    findings: List[str] = Field(description="Key findings")
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Quantitative metrics"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations"
    )
    visualizations: List[str] = Field(
        default_factory=list, description="Suggested visualizations"
    )


class WritingOutput(BaseModel):
    """Output schema for Writing department crew."""

    title: str = Field(description="Content title")
    content: str = Field(description="Written content")
    content_type: str = Field(description="Type of content created")
    word_count: int = Field(description="Approximate word count")
    style: str = Field(description="Writing style used")


class CodingOutput(BaseModel):
    """Output schema for Coding department crew."""

    success: bool = Field(description="Whether the task was completed")
    code: Optional[str] = Field(default=None, description="Generated code")
    language: str = Field(description="Programming language used")
    explanation: Optional[str] = Field(default=None, description="Code explanation")
    tests: Optional[str] = Field(default=None, description="Generated tests")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    files_created: List[str] = Field(default_factory=list, description="Files created")
