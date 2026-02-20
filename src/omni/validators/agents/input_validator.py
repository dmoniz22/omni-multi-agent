"""Input validator agent.

Validates crew input data against input schemas.
"""

from typing import Any, Dict, Type

from pydantic import BaseModel

from omni.core.logging import get_logger
from omni.validators.base import BaseValidator
from omni.validators.schemas.common import ValidatedResult

logger = get_logger(__name__)


class InputValidator:
    """Validator for crew input data.

    Validates input data against the appropriate input schema
    before passing to a crew.
    """

    def __init__(self):
        """Initialize the input validator."""
        self.validator = BaseValidator()

    def validate_input(
        self,
        data: Dict[str, Any],
        schema: Type[BaseModel],
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
        logger.info(
            "Validating crew input",
            crew=crew_name,
            schema=schema.__name__,
        )

        result = self.validator.validate(data, schema, schema_name=schema.__name__)

        if result.valid:
            logger.info(
                "Crew input validation passed",
                crew=crew_name,
            )
        else:
            logger.warning(
                "Crew input validation failed",
                crew=crew_name,
                errors=result.errors,
            )

        return result

    def validate_or_raise(
        self,
        data: Dict[str, Any],
        schema: Type[BaseModel],
        crew_name: str,
    ) -> Dict[str, Any]:
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
        return self.validator.validate_or_raise(data, schema, schema_name=crew_name)
