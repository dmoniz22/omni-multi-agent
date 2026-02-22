"""Base skill class and interface for OMNI skills system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from omni.core.logging import get_logger

logger = get_logger(__name__)


class SkillAction(BaseModel):
    """Definition of a skill action."""

    name: str = Field(..., description="Unique name of the action")
    description: str = Field(..., description="Human-readable description")
    input_schema: type[BaseModel] = Field(
        default=dict, description="Pydantic input schema"
    )
    output_schema: type[BaseModel] = Field(
        default=dict, description="Pydantic output schema"
    )


class SkillInfo(BaseModel):
    """Information about a registered skill."""

    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Skill description")
    version: str = Field(default="1.0.0", description="Skill version")
    enabled: bool = Field(default=True, description="Whether skill is enabled")
    actions: List[str] = Field(
        default_factory=list, description="List of available action names"
    )


class BaseSkill(ABC):
    """Abstract base class for all skills in OMNI.

    Skills are reusable tools that can be used by CrewAI agents.
    Each skill provides one or more actions that agents can invoke.

    Usage:
        class MySkill(BaseSkill):
            name = "my_skill"
            description = "Does something useful"

            def get_actions(self) -> Dict[str, SkillAction]:
                return {
                    "do_something": SkillAction(
                        name="do_something",
                        description="Does something",
                        input_schema=DoSomethingInput,
                        output_schema=DoSomethingOutput
                    )
                }

            def execute(self, action: str, params: dict) -> dict:
                if action == "do_something":
                    return self._do_something(params)
                raise ValueError(f"Unknown action: {action}")

        skill = MySkill()
        result = skill.execute("do_something", {"param": "value"})
    """

    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    def __init__(self):
        """Initialize the skill."""
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """Check if skill is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set skill enabled state."""
        self._enabled = value

    @abstractmethod
    def get_actions(self) -> Dict[str, SkillAction]:
        """Get all available actions for this skill.

        Returns:
            Dict mapping action names to SkillAction definitions.
        """
        pass

    @abstractmethod
    def execute(self, action: str, params: dict) -> dict:
        """Execute a skill action.

        Args:
            action: The action name to execute.
            params: Parameters for the action.

        Returns:
            Dict with action results.

        Raises:
            ValueError: If action is not recognized.
            RuntimeError: If execution fails.
        """
        pass

    def get_info(self) -> SkillInfo:
        """Get skill information for registry.

        Returns:
            SkillInfo with skill metadata.
        """
        return SkillInfo(
            name=self.name,
            description=self.description,
            version=self.version,
            enabled=self._enabled,
            actions=list(self.get_actions().keys()),
        )

    def health_check(self) -> bool:
        """Verify skill is operational.

        Returns:
            True if skill is ready to use.
        """
        return self._enabled

    def to_crewai_tools(self) -> List[Any]:
        """Convert skill actions to CrewAI-compatible tools.

        This method should be overridden by subclasses to provide
        proper CrewAI tool integration.

        Returns:
            List of CrewAI Tool objects.
        """
        from crewai.tools import Tool

        tools = []
        for action_name, action in self.get_actions().items():
            tool = Tool(
                name=f"{self.name}_{action_name}",
                description=action.description,
                func=lambda p, a=action_name: self.execute(a, p),
            )
            tools.append(tool)

        return tools
