"""Validator registry for OMNI.

Manages validation schemas and provides validation services.
"""

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from omni.core.logging import get_logger
from omni.validators.agents.input_validator import InputValidator
from omni.validators.agents.output_validator import OutputValidator
from omni.validators.agents.response_validator import ResponseValidator
from omni.validators.base import BaseValidator
from omni.validators.schemas.common import ValidatedResult

logger = get_logger(__name__)


class ValidatorRegistry:
    """Registry for validation schemas and validators.

    Provides centralized access to validation schemas and
    validation operations.
    """

    def __init__(self):
        """Initialize the validator registry."""
        self._schemas: Dict[str, Type[BaseModel]] = {}
        self._input_validator = InputValidator()
        self._output_validator = OutputValidator()
        self._response_validator = ResponseValidator()
        self._base_validator = BaseValidator()

        self._register_default_schemas()

    def _register_default_schemas(self) -> None:
        """Register default schemas."""
        from omni.validators.schemas import (
            AnalysisTaskInput,
            CodingTaskInput,
            FinalResponse,
            GitHubTaskInput,
            GitHubOutput,
            ResearchTaskInput,
            ResearchReport,
            SocialContentOutput,
            SocialTaskInput,
            WritingOutput,
            WritingTaskInput,
        )

        schemas = [
            ("GitHubTaskInput", GitHubTaskInput),
            ("ResearchTaskInput", ResearchTaskInput),
            ("SocialTaskInput", SocialTaskInput),
            ("AnalysisTaskInput", AnalysisTaskInput),
            ("WritingTaskInput", WritingTaskInput),
            ("CodingTaskInput", CodingTaskInput),
            ("GitHubOutput", GitHubOutput),
            ("ResearchReport", ResearchReport),
            ("SocialContentOutput", SocialContentOutput),
            ("WritingOutput", WritingOutput),
            ("FinalResponse", FinalResponse),
        ]

        for name, schema in schemas:
            self.register(name, schema)

    def register(self, schema_name: str, schema_class: Type[BaseModel]) -> None:
        """Register a validation schema.

        Args:
            schema_name: Name of the schema
            schema_class: Pydantic model class
        """
        self._schemas[schema_name] = schema_class
        logger.info("Registered validation schema", schema=schema_name)

    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """Get a schema by name.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema class or None if not found
        """
        return self._schemas.get(schema_name)

    def list_schemas(self) -> List[str]:
        """List all registered schema names.

        Returns:
            List of schema names
        """
        return list(self._schemas.keys())

    def validate(
        self,
        data: Dict[str, Any],
        schema_name: str,
    ) -> ValidatedResult:
        """Validate data against a schema.

        Args:
            data: Data to validate
            schema_name: Name of the schema

        Returns:
            ValidatedResult with validation status
        """
        schema = self.get_schema(schema_name)
        if schema is None:
            return ValidatedResult(
                valid=False,
                data=None,
                errors=[f"Schema '{schema_name}' not found"],
                schema_name=schema_name,
            )

        return self._base_validator.validate(data, schema, schema_name)

    def validate_input(
        self,
        data: Dict[str, Any],
        schema_name: str,
    ) -> ValidatedResult:
        """Validate crew input.

        Args:
            data: Input data to validate
            schema_name: Name of the input schema

        Returns:
            ValidatedResult with validation status
        """
        return self.validate(data, schema_name)

    def validate_output(
        self,
        data: Dict[str, Any],
        schema_name: str,
    ) -> ValidatedResult:
        """Validate crew output.

        Args:
            data: Output data to validate
            schema_name: Name of the output schema

        Returns:
            ValidatedResult with validation status
        """
        return self.validate(data, schema_name)

    def validate_response(
        self,
        data: Dict[str, Any],
    ) -> ValidatedResult:
        """Validate final response.

        Args:
            data: Response data to validate

        Returns:
            ValidatedResult with validation status
        """
        return self._response_validator.validate_response(data)


_validator_registry: Optional[ValidatorRegistry] = None


def get_validator_registry() -> ValidatorRegistry:
    """Get the global validator registry instance.

    Returns:
        ValidatorRegistry instance
    """
    global _validator_registry
    if _validator_registry is None:
        _validator_registry = ValidatorRegistry()
    return _validator_registry


def reset_validator_registry() -> None:
    """Reset the global validator registry."""
    global _validator_registry
    _validator_registry = None
