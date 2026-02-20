"""Common validation schemas for OMNI."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ValidatedResult(BaseModel):
    """Result of a validation operation.

    This is the standard return type for all validation operations,
    containing the validation status, data (if valid), errors, and
    any auto-corrections made.
    """

    valid: bool = Field(description="Whether the data passed validation")
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Validated and potentially corrected data"
    )
    errors: List[str] = Field(
        default_factory=list, description="List of validation errors if invalid"
    )
    corrections: Optional[Dict[str, Any]] = Field(
        default=None, description="Auto-corrections made by LLM during validation"
    )
    schema_name: str = Field(description="Name of the schema used for validation")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class StepRecord(BaseModel):
    """Record of an individual step in the execution history.

    Used for audit trails and debugging.
    """

    step_type: str = Field(
        description="Type of step (e.g., 'query_analyzer', 'crew_execution')"
    )
    input: Dict[str, Any] = Field(
        default_factory=dict, description="Input data to the step"
    )
    output: Optional[Dict[str, Any]] = Field(
        default=None, description="Output data from the step"
    )
    timestamp: str = Field(description="ISO timestamp when step was executed")
    duration_ms: Optional[int] = Field(
        default=None, description="Duration of step execution in milliseconds"
    )
    success: bool = Field(
        default=True, description="Whether the step completed successfully"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if step failed"
    )
