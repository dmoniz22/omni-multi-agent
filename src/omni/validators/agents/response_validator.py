"""Response validator agent.

Validates final response before returning to user.
"""

from typing import Any, Dict, Type

from pydantic import BaseModel

from omni.core.logging import get_logger
from omni.validators.base import BaseValidator
from omni.validators.schemas.common import ValidatedResult

logger = get_logger(__name__)


class ResponseValidator:
    """Validator for final response output.

    Validates the final collated response against the FinalResponse
    schema before returning to the user.
    """

    def __init__(self):
        """Initialize the response validator."""
        self.validator = BaseValidator()

    def validate_response(
        self,
        data: Dict[str, Any],
    ) -> ValidatedResult:
        """Validate final response data.

        Args:
            data: Response data to validate

        Returns:
            ValidatedResult with validation status
        """
        from omni.validators.schemas.responses import FinalResponse

        logger.info("Validating final response")

        result = self.validator.validate(
            data, FinalResponse, schema_name="FinalResponse"
        )

        if result.valid:
            logger.info("Final response validation passed")
        else:
            logger.warning(
                "Final response validation failed",
                errors=result.errors,
            )

        return result

    def validate_or_raise(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate and raise on failure.

        Args:
            data: Response data to validate

        Returns:
            Validated data dict

        Raises:
            ValidationError: If validation fails
        """
        from omni.validators.schemas.responses import FinalResponse

        return self.validator.validate_or_raise(
            data, FinalResponse, schema_name="FinalResponse"
        )
