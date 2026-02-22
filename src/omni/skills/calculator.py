"""Calculator skill for OMNI.

Provides mathematical operations: calculate expressions, unit conversions.
Uses sympy for safe expression evaluation (no eval()).
"""

import re
from typing import Any, Dict

from pydantic import BaseModel, Field

from omni.skills.base import BaseSkill, SkillAction


class CalculateInput(BaseModel):
    """Input for calculate action."""

    expression: str = Field(..., description="Mathematical expression to evaluate")


class CalculateOutput(BaseModel):
    """Output from calculate action."""

    result: float = Field(..., description="Numeric result")
    formatted: str = Field(..., description="Formatted result as string")


class ConvertInput(BaseModel):
    """Input for convert action."""

    value: float = Field(..., description="Value to convert")
    from_unit: str = Field(..., description="Source unit")
    to_unit: str = Field(..., description="Target unit")


class ConvertOutput(BaseModel):
    """Output from convert action."""

    result: float = Field(..., description="Converted value")
    from_value: float = Field(..., description="Original value")
    from_unit: str = Field(..., description="Source unit")
    to_unit: str = Field(..., description="Target unit")


UNIT_CONVERSIONS = {
    ("km", "m"): 1000,
    ("m", "km"): 0.001,
    ("m", "cm"): 100,
    ("cm", "m"): 0.01,
    ("km", "mi"): 0.621371,
    ("mi", "km"): 1.60934,
    ("kg", "lb"): 2.20462,
    ("lb", "kg"): 0.453592,
    ("g", "oz"): 0.035274,
    ("oz", "g"): 28.3495,
    ("c", "f"): lambda c: c * 9 / 5 + 32,
    ("f", "c"): lambda f: (f - 32) * 5 / 9,
    ("c", "k"): lambda c: c + 273.15,
    ("k", "c"): lambda k: k - 273.15,
    ("bytes", "kb"): 1 / 1024,
    ("kb", "bytes"): 1024,
    ("kb", "mb"): 1 / 1024,
    ("mb", "kb"): 1024,
}


class CalculatorSkill(BaseSkill):
    """Calculator skill for mathematical operations.

    Provides safe expression evaluation and unit conversions.
    Uses sympy for parsing to avoid eval() security risks.

    Actions:
        - calculate: Evaluate mathematical expressions
        - convert: Convert between units

    Usage:
        skill = CalculatorSkill()
        result = skill.execute("calculate", {"expression": "2 + 2"})
        result = skill.execute("convert", {"value": 100, "from_unit": "c", "to_unit": "f"})
    """

    name = "calculator"
    description = "Mathematical calculations and unit conversions"
    version = "1.0.0"

    def __init__(self):
        """Initialize calculator skill."""
        super().__init__()
        try:
            import sympy

            self._sympy = sympy
        except ImportError:
            self._sympy = None

    def get_actions(self) -> Dict[str, SkillAction]:
        """Get available calculator actions."""
        return {
            "calculate": SkillAction(
                name="calculate",
                description="Evaluate a mathematical expression",
                input_schema=CalculateInput,
                output_schema=CalculateOutput,
            ),
            "convert": SkillAction(
                name="convert",
                description="Convert between units",
                input_schema=ConvertInput,
                output_schema=ConvertOutput,
            ),
        }

    def execute(self, action: str, params: dict) -> dict:
        """Execute a calculator action.

        Args:
            action: Action name (calculate, convert)
            params: Action parameters

        Returns:
            Dict with action results

        Raises:
            ValueError: If action is unknown or invalid
        """
        if action == "calculate":
            return self._calculate(params)
        elif action == "convert":
            return self._convert(params)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _calculate(self, params: dict) -> dict:
        """Evaluate mathematical expression."""
        validated = CalculateInput.model_validate(params)
        expression = validated.expression

        expression = re.sub(r"[^0-9+\-*/().%^ ]", "", expression)

        if self._sympy:
            try:
                result = float(self._sympy.sympify(expression).evalf())
            except Exception as e:
                raise ValueError(f"Invalid expression: {e}")
        else:
            result = self._fallback_evaluate(expression)

        return {
            "result": result,
            "formatted": str(result),
        }

    def _fallback_evaluate(self, expression: str) -> float:
        """Fallback evaluation without sympy."""
        try:
            ops = {
                "+": float.__add__,
                "-": float.__sub__,
                "*": float.__mul__,
                "/": float.__truediv__,
            }
            tokens = (
                expression.replace("-", " -")
                .replace("+", " +")
                .replace("*", " *")
                .replace("/", " /")
                .split()
            )
            if not tokens:
                raise ValueError("Empty expression")
            result = float(tokens[0])
            i = 1
            while i < len(tokens):
                op = tokens[i]
                if op not in ops:
                    raise ValueError(f"Invalid operator: {op}")
                next_val = float(tokens[i + 1])
                result = ops[op](result, next_val)
                i += 2
            return result
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")

    def _convert(self, params: dict) -> dict:
        """Convert between units."""
        validated = ConvertInput.model_validate(params)
        from_unit = validated.from_unit.lower()
        to_unit = validated.to_unit.lower()
        value = validated.value

        key = (from_unit, to_unit)
        if key not in UNIT_CONVERSIONS:
            raise ValueError(f"Conversion not supported: {from_unit} -> {to_unit}")

        conversion = UNIT_CONVERSIONS[key]
        if callable(conversion):
            result = conversion(value)
        else:
            result = value * conversion

        return {
            "result": result,
            "from_value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
        }

    def health_check(self) -> bool:
        """Verify calculator is operational."""
        try:
            test_result = self._calculate({"expression": "2 + 2"})
            return test_result["result"] == 4.0
        except Exception:
            return False
