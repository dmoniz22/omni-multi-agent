"""Validator agents for OMNI.

Provides validation for crew inputs, outputs, and final responses.
Consolidated into SchemaValidator with backward-compatible aliases.
"""

from omni.validators.agents.schema_validator import (
    SchemaValidator,
    get_input_validator,
    get_output_validator,
    get_response_validator,
)

# Backward-compatible aliases
InputValidator = SchemaValidator
OutputValidator = SchemaValidator
ResponseValidator = SchemaValidator

__all__ = [
    "SchemaValidator",
    "InputValidator",
    "OutputValidator",
    "ResponseValidator",
    "get_input_validator",
    "get_output_validator",
    "get_response_validator",
]
