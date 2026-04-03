"""Input validator agent.

Validates crew input data against input schemas.

.. deprecated::
    Use :class:`omni.validators.agents.schema_validator.SchemaValidator` instead.
    This module is kept for backward compatibility.
"""

from typing import Any

from pydantic import BaseModel

from omni.validators.agents.schema_validator import get_input_validator
from omni.validators.schemas.common import ValidatedResult

InputValidator = get_input_validator()


def validate_input(
    data: dict[str, Any],
    schema: type[BaseModel],
    crew_name: str,
) -> ValidatedResult:
    """Validate input data for a crew.

    Args:
        data: Input data to validate
        schema: Pydantic schema class
        crew_name: Name of the crew (for logging)

    Returns:
        ValidatedResult with validation status
    """
    return InputValidator.validate(data, schema, context=f"input:{crew_name}")


def validate_input_or_raise(
    data: dict[str, Any],
    schema: type[BaseModel],
    crew_name: str,
) -> dict[str, Any]:
    """Validate and raise on failure.

    Args:
        data: Input data to validate
        schema: Pydantic schema class
        crew_name: Name of the crew

    Returns:
        Validated data dict

    Raises:
        ValidationError: If validation fails
    """
    return InputValidator.validate_or_raise(data, schema, context=f"input:{crew_name}")
