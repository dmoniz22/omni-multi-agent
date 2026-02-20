"""Final response schema for user-facing output.

This schema defines the structure of the final response returned to the user
after all processing is complete.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    """Source citation for the response."""

    title: str = Field(description="Source title")
    url: Optional[str] = Field(default=None, description="Source URL")
    department: str = Field(description="Department that provided this source")


class FinalResponse(BaseModel):
    """Final response schema for user-facing output.

    This is the schema that gets validated before returning the final
    response to the user.
    """

    content: str = Field(description="The main response content")
    sources: List[Source] = Field(
        default_factory=list, description="Sources cited in the response"
    )
    departments_used: List[str] = Field(
        default_factory=list,
        description="List of departments that contributed to this response",
    )
    execution_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Summary of execution (steps, timing, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the response"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
