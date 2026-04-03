"""Output validator agent.

Validates crew output data against output schemas.

.. deprecated::
    Use :class:`omni.validators.agents.schema_validator.SchemaValidator` instead.
    This module is kept for backward compatibility.
"""

from typing import Any

from pydantic import BaseModel

from omni.validators.agents.schema_validator import get_output_validator
from omni.validators.schemas.common import ValidatedResult

OutputValidator = get_output_validator()


def validate_output(
    data: dict[str, Any],
    schema: type[BaseModel],
    crew_name: str,
) -> ValidatedResult:
    """Validate output data from a crew.

    Args:
        data: Output data to validate
        schema: Pydantic schema class
        crew_name: Name of the crew (for logging)

    Returns:
        ValidatedResult with validation status
    """
    return OutputValidator.validate(data, schema, context=f"output:{crew_name}")


def validate_output_or_raise(
    data: dict[str, Any],
    schema: type[BaseModel],
    crew_name: str,
) -> dict[str, Any]:
    """Validate and raise on failure.

    Args:
        data: Output data to validate
        schema: Pydantic schema class
        crew_name: Name of the crew

    Returns:
        Validated data dict

    Raises:
        ValidationError: If validation fails
    """
    return OutputValidator.validate_or_raise(
        data, schema, context=f"output:{crew_name}"
    )
