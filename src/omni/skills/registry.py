"""Skill registry for OMNI.

Manages registration, discovery, and execution of skills/tools.
Provides auto-discovery from the skills directory and dynamic skill lookup.
"""

import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from omni.core.logging import get_logger
from omni.skills.base import BaseSkill, SkillInfo

logger = get_logger(__name__)


class SkillRegistry:
    """Registry for managing skills/tools.

    The registry provides:
    - Auto-discovery of skills from the skills directory
    - Registration and lookup of skill classes
    - Execution of skills by name
    - Listing of available skills
    - Conversion to CrewAI tools

    Usage:
        registry = SkillRegistry()
        registry.discover()  # Auto-discover all skills

        # Get skill info
        info = registry.get_info("file")

        # Execute a skill
        result = registry.execute("file", "read", {"path": "/tmp/test.txt"})

        # Get as CrewAI tools
        tools = registry.get_as_tools(["file", "calculator"])
    """

    def __init__(self):
        """Initialize the skill registry."""
        self._skills: Dict[str, BaseSkill] = {}
        self._skill_info: Dict[str, SkillInfo] = {}
        self._discovered = False

    def register(self, skill: BaseSkill) -> None:
        """Register a skill instance with the registry.

        Args:
            skill: A BaseSkill instance.

        Raises:
            ValueError: If the skill doesn't have a name or name is empty.
            ValueError: If a skill with the same name is already registered.
            TypeError: If skill doesn't inherit from BaseSkill.

        Example:
            registry.register(FileSkill())
        """
        if not isinstance(skill, BaseSkill):
            raise TypeError(f"Expected BaseSkill instance, got {type(skill)}")

        name = skill.name
        if not name:
            raise ValueError(
                f"Skill must have a 'name' attribute: {type(skill).__name__}"
            )

        if name in self._skills:
            logger.warning(
                "Skill already registered, overwriting",
                skill_name=name,
                existing_class=self._skills[name].__class__.__name__,
                new_class=skill.__class__.__name__,
            )

        self._skills[name] = skill
        self._skill_info[name] = skill.get_info()

        logger.debug(
            "Skill registered", skill_name=name, class_name=skill.__class__.__name__
        )

    def get(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by name.

        Args:
            name: The skill identifier (e.g., "file", "calculator").

        Returns:
            BaseSkill or None: The skill instance if found, None otherwise.

        Example:
            skill = registry.get("file")
            if skill:
                result = skill.execute("read", {"path": "/tmp/test.txt"})
        """
        skill = self._skills.get(name)
        if skill is None:
            logger.warning("Skill not found in registry", skill_name=name)
        return skill

    def get_info(self, name: str) -> Optional[SkillInfo]:
        """Get information about a registered skill.

        Args:
            name: The skill identifier.

        Returns:
            SkillInfo or None: Skill metadata including name, description, actions, etc.
        """
        return self._skill_info.get(name)

    def list_available(self) -> List[SkillInfo]:
        """List all available (registered) skills.

        Returns:
            List[SkillInfo]: List of skill info, one per registered skill.

        Example:
            skills = registry.list_available()
            for skill in skills:
                print(f"{skill.name}: {skill.description}")
        """
        return list(self._skill_info.values())

    def list_enabled(self) -> List[SkillInfo]:
        """List all enabled skills.

        Returns:
            List[SkillInfo]: List of enabled skill info.
        """
        return [info for info in self._skill_info.values() if info.enabled]

    def execute(self, skill_name: str, action: str, params: dict) -> dict:
        """Execute a skill action.

        Args:
            skill_name: The skill identifier.
            action: The action name to execute.
            params: Parameters for the action.

        Returns:
            Dict: Action execution results.

        Raises:
            ValueError: If the skill is not registered.
            ValueError: If the action is not found.

        Example:
            result = registry.execute("calculator", "calculate", {
                "expression": "2 + 2"
            })
        """
        skill = self.get(skill_name)
        if skill is None:
            raise ValueError(f"Skill '{skill_name}' not found in registry")

        if not skill.enabled:
            raise ValueError(f"Skill '{skill_name}' is disabled")

        logger.info("Executing skill action", skill=skill_name, action=action)

        return skill.execute(action, params)

    def enable(self, name: str) -> bool:
        """Enable a skill.

        Args:
            name: The skill identifier.

        Returns:
            bool: True if skill was enabled, False if not found.
        """
        skill = self._skills.get(name)
        if skill:
            skill.enabled = True
            self._skill_info[name] = skill.get_info()
            logger.debug("Skill enabled", skill_name=name)
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a skill.

        Args:
            name: The skill identifier.

        Returns:
            bool: True if skill was disabled, False if not found.
        """
        skill = self._skills.get(name)
        if skill:
            skill.enabled = False
            self._skill_info[name] = skill.get_info()
            logger.debug("Skill disabled", skill_name=name)
            return True
        return False

    def get_as_tools(self, names: Optional[List[str]] = None) -> List[Any]:
        """Get skills as CrewAI-compatible tools.

        Args:
            names: Optional list of skill names to convert. If None, all enabled skills are converted.

        Returns:
            List[Any]: List of CrewAI Tool objects.

        Example:
            tools = registry.get_as_tools(["file", "calculator"])
            # Use tools in CrewAI agent
            agent = Agent(tools=tools, ...)
        """
        try:
            from crewai.tools import tool as create_tool
        except ImportError:
            logger.warning("CrewAI not available, returning empty tool list")
            return []

        if names is None:
            skills_to_convert = [s for s in self._skills.values() if s.enabled]
        else:
            skills_to_convert = [self._skills[n] for n in names if n in self._skills]

        tools = []
        for skill in skills_to_convert:
            for action_name, action in skill.get_actions().items():

                def make_execute_func(s, a):
                    def execute_func(params):
                        return s.execute(a, params)

                    return execute_func

                try:
                    tool_func = make_execute_func(skill, action_name)
                    tool = create_tool(
                        name=f"{skill.name}_{action_name}",
                        description=action.description,
                    )(tool_func)
                    tools.append(tool)
                except Exception as e:
                    logger.warning(
                        "Failed to create tool",
                        skill=skill.name,
                        action=action_name,
                        error=str(e),
                    )

        logger.debug(
            "Converted skills to tools",
            skill_count=len(skills_to_convert),
            tool_count=len(tools),
        )
        return tools

    def discover(self, package_path: Optional[str] = None) -> int:
        """Auto-discover skills from the skills directory.

        Scans all modules in the skills package for classes
        that inherit from BaseSkill.

        Args:
            package_path: Optional path to scan. Defaults to omni.skills.

        Returns:
            int: Number of skills discovered and registered.

        Note:
            This method should be called once during application startup.
            It will not re-scan if already called.

        Example:
            count = registry.discover()
            print(f"Discovered {count} skills")
        """
        if self._discovered and package_path is None:
            logger.debug("Skills already discovered, skipping")
            return len(self._skills)

        if package_path is None:
            from omni import skills as skills_package

            package_path = skills_package.__path__[0]  # type: ignore
            package_name = "omni.skills"
        else:
            package_name = package_path.replace("/", ".").replace("\\", ".")

        discovered_count = 0
        skills_dir = Path(package_path)

        logger.info("Discovering skills", skills_dir=str(skills_dir))

        for py_file in skills_dir.glob("*.py"):
            if py_file.name.startswith("_") or py_file.stem == "base":
                continue

            module_name = f"{package_name}.{py_file.stem}"

            try:
                module = importlib.import_module(module_name)

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseSkill) and obj is not BaseSkill and obj.name:
                        skill_instance = obj()
                        self.register(skill_instance)
                        discovered_count += 1
                        logger.debug(
                            "Discovered skill",
                            skill_name=obj.name,
                            module=module_name,
                            class_name=name,
                        )

            except ImportError as e:
                logger.warning(
                    "Failed to import skill module",
                    module=module_name,
                    error=str(e),
                )
            except Exception as e:
                logger.error(
                    "Error discovering skill",
                    module=module_name,
                    error=str(e),
                )

        self._discovered = True

        logger.info(
            "Skill discovery complete",
            discovered_count=discovered_count,
            total_skills=len(self._skills),
        )

        return discovered_count

    def is_registered(self, name: str) -> bool:
        """Check if a skill is registered.

        Args:
            name: The skill identifier.

        Returns:
            bool: True if registered, False otherwise.
        """
        return name in self._skills

    def unregister(self, name: str) -> bool:
        """Unregister a skill.

        Args:
            name: The skill identifier.

        Returns:
            bool: True if skill was unregistered, False if not found.
        """
        if name in self._skills:
            del self._skills[name]
            del self._skill_info[name]
            logger.debug("Skill unregistered", skill_name=name)
            return True
        return False

    def clear(self) -> None:
        """Clear all registered skills.

        This is primarily useful for testing.
        """
        self._skills.clear()
        self._skill_info.clear()
        self._discovered = False
        logger.debug("Skill registry cleared")


_global_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Get the global skill registry instance.

    Returns:
        SkillRegistry: The global registry instance.

    Note:
        The registry is lazily initialized. First call will create
        and discover skills.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = SkillRegistry()
        _global_registry.discover()
    return _global_registry


def reset_skill_registry() -> SkillRegistry:
    """Reset and recreate the global skill registry.

    Useful for testing or when skills need to be re-discovered.

    Returns:
        SkillRegistry: The new global registry instance.
    """
    global _global_registry
    _global_registry = SkillRegistry()
    _global_registry.discover()
    return _global_registry
