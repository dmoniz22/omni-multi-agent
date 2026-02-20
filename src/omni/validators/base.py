"""Base validator for OMNI.

Provides Pydantic-first validation with LLM auto-correction fallback.
"""

import json
from typing import Any, Dict, Type

from pydantic import BaseModel
from pydantic_core import ValidationError

from omni.core.logging import get_logger
from omni.validators.schemas.common import ValidatedResult

logger = get_logger(__name__)


class BaseValidator:
    """Base validator with Pydantic-first, LLM-fallback pattern.

    This validator attempts to validate data against a Pydantic schema.
    If validation fails and corrections are enabled, it uses an LLM to
    attempt auto-correction.
    """

    def __init__(
        self,
        model_name: str = "phi3.5:3.8b",
        max_correction_attempts: int = 2,
        corrections_enabled: bool = True,
    ):
        """Initialize the validator.

        Args:
            model_name: Ollama model to use for corrections
            max_correction_attempts: Maximum number of LLM correction attempts
            corrections_enabled: Whether to enable LLM auto-correction
        """
        self.model_name = model_name
        self.max_correction_attempts = max_correction_attempts
        self.corrections_enabled = corrections_enabled

    def validate(
        self,
        data: Dict[str, Any],
        schema: Type[BaseModel],
        schema_name: str = "unknown",
    ) -> ValidatedResult:
        """Validate data against a Pydantic schema.

        Args:
            data: Data to validate
            schema: Pydantic schema class
            schema_name: Name of the schema for reporting

        Returns:
            ValidatedResult with validation status and any corrections
        """
        try:
            validated = schema.model_validate(data)
            return ValidatedResult(
                valid=True,
                data=validated.model_dump(),
                schema_name=schema_name,
            )
        except ValidationError as e:
            if not self.corrections_enabled:
                errors = [err["msg"] for err in e.errors()]
                return ValidatedResult(
                    valid=False,
                    data=None,
                    errors=errors,
                    schema_name=schema_name,
                )

            correction_result = self._attempt_correction(data, schema, schema_name, e)
            return correction_result

    def _attempt_correction(
        self,
        data: Dict[str, Any],
        schema: Type[BaseModel],
        schema_name: str,
        original_error: ValidationError,
    ) -> ValidatedResult:
        """Attempt to correct invalid data using LLM.

        Args:
            data: Original invalid data
            schema: Target schema
            schema_name: Name of the schema
            original_error: Original validation error

        Returns:
            ValidatedResult with correction attempts
        """
        errors = [err["msg"] for err in original_error.errors()]

        try:
            schema_json = json.dumps(schema.model_json_schema())
            correction_prompt = self._build_correction_prompt(data, schema_json, errors)

            from omni.core.models import ModelFactory

            model_factory = ModelFactory()
            model = model_factory.get(self.model_name)

            response = model.invoke(correction_prompt)

            try:
                corrected_data = json.loads(response.content)
                validated = schema.model_validate(corrected_data)

                return ValidatedResult(
                    valid=True,
                    data=validated.model_dump(),
                    corrections=corrected_data,
                    schema_name=schema_name,
                )
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(
                    "LLM correction failed",
                    schema=schema_name,
                    error=str(e),
                )
                return ValidatedResult(
                    valid=False,
                    data=None,
                    errors=errors + [f"Correction failed: {str(e)}"],
                    schema_name=schema_name,
                )

        except Exception as e:
            logger.error(
                "LLM correction attempt failed",
                schema=schema_name,
                error=str(e),
            )
            return ValidatedResult(
                valid=False,
                data=None,
                errors=errors + [f"Correction error: {str(e)}"],
                schema_name=schema_name,
            )

    def _build_correction_prompt(
        self,
        data: Dict[str, Any],
        schema_json: str,
        errors: list[str],
    ) -> str:
        """Build prompt for LLM to correct invalid data.

        Args:
            data: Original invalid data
            schema_json: JSON schema description
            errors: List of validation errors

        Returns:
            Prompt string for LLM
        """
        return f"""You are a data correction assistant. The following data failed validation.

Original data:
{json.dumps(data, indent=2)}

Validation errors:
{json.dumps(errors, indent=2)}

Target schema (JSON Schema):
{schema_json}

Please correct the data to match the schema. Return ONLY valid JSON with no additional text.
Your response must be a valid JSON object that conforms to the schema above."""

    def validate_or_raise(
        self,
        data: Dict[str, Any],
        schema: Type[BaseModel],
        schema_name: str = "unknown",
    ) -> Dict[str, Any]:
        """Validate and raise on failure.

        Args:
            data: Data to validate
            schema: Pydantic schema class
            schema_name: Name of the schema

        Returns:
            Validated data dict

        Raises:
            ValidationError: If validation fails
        """
        result = self.validate(data, schema, schema_name)

        if not result.valid:
            raise ValidationError.from_exception_data(
                title=schema_name,
                line_errors=[
                    {
                        "type": "value_error",
                        "loc": (),
                        "input": data,
                        "msg": "; ".join(result.errors),
                    }
                ],
            )

        return result.data
