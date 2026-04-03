"""Response validator agent.

Validates final response before returning to user.

.. deprecated::
    Use :class:`omni.validators.agents.schema_validator.SchemaValidator` instead.
    This module is kept for backward compatibility.
"""

from typing import Any

from omni.validators.agents.schema_validator import get_response_validator
from omni.validators.schemas.common import ValidatedResult

ResponseValidator = get_response_validator()


def validate_response(data: dict[str, Any]) -> ValidatedResult:
    """Validate final response data.

    Args:
        data: Response data to validate

    Returns:
        ValidatedResult with validation status
    """
    from omni.validators.schemas.responses import FinalResponse

    return ResponseValidator.validate(data, FinalResponse, context="final_response")


def validate_response_or_raise(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and raise on failure.

    Args:
        data: Response data to validate

    Returns:
        Validated data dict

    Raises:
        ValidationError: If validation fails
    """
    from omni.validators.schemas.responses import FinalResponse

    return ResponseValidator.validate_or_raise(
        data, FinalResponse, context="final_response"
    )
