"""Generic schema validator for OMNI.

Provides type-safe validation against Pydantic schemas with optional LLM auto-correction.
"""

from typing import Any

from pydantic import BaseModel

from omni.core.logging import get_logger
from omni.validators.base import BaseValidator
from omni.validators.schemas.common import ValidatedResult

logger = get_logger(__name__)


class SchemaValidator:
    """Generic validator for crew input/output/response data.

    Validates data against any Pydantic schema with optional LLM
    auto-correction on validation failure.
    """

    def __init__(self):
        """Initialize the schema validator."""
        self._base = BaseValidator()

    def validate(
        self,
        data: Any,
        schema: type[BaseModel],
        context: str = "unknown",
    ) -> ValidatedResult:
        """Validate data against a Pydantic schema.

        Args:
            data: Data to validate
            schema: Pydantic schema class
            context: Descriptive context for logging (e.g., "crew_input", "crew_output")

        Returns:
            ValidatedResult with validation status and any corrections
        """
        logger.debug(
            "Validating data",
            context=context,
            schema=schema.__name__,
        )

        result = self._base.validate(data, schema, schema_name=schema.__name__)

        if result.valid:
            logger.debug("Validation passed", context=context, schema=schema.__name__)
        else:
            logger.warning(
                "Validation failed",
                context=context,
                schema=schema.__name__,
                errors=result.errors,
            )

        return result

    def validate_or_raise(
        self,
        data: Any,
        schema: type[BaseModel],
        context: str = "unknown",
    ) -> dict[str, Any]:
        """Validate data and raise on failure.

        Args:
            data: Data to validate
            schema: Pydantic schema class
            context: Descriptive context for error messages

        Returns:
            Validated data dict

        Raises:
            ValidationError: If validation fails
        """
        result = self.validate(data, schema, context)
        if not result.valid:
            from pydantic_core import ValidationError

            raise ValidationError.from_exception_data(
                title=context,
                line_errors=[
                    {
                        "type": "value_error",
                        "loc": (),
                        "input": data,
                        "msg": f"{context} validation failed: "
                        + "; ".join(result.errors),
                    }
                ],
            )
        return result.data


_input_validator: SchemaValidator | None = None
_output_validator: SchemaValidator | None = None
_response_validator: SchemaValidator | None = None


def get_input_validator() -> SchemaValidator:
    """Get the global input validator instance."""
    global _input_validator
    if _input_validator is None:
        _input_validator = SchemaValidator()
    return _input_validator


def get_output_validator() -> SchemaValidator:
    """Get the global output validator instance."""
    global _output_validator
    if _output_validator is None:
        _output_validator = SchemaValidator()
    return _output_validator


def get_response_validator() -> SchemaValidator:
    """Get the global response validator instance."""
    global _response_validator
    if _response_validator is None:
        _response_validator = SchemaValidator()
    return _response_validator
