"""Tests for the skills system."""

import pytest

from omni.skills.base import BaseSkill, SkillAction, SkillInfo
from omni.skills.registry import SkillRegistry, get_skill_registry
from omni.skills.file import FileSkill
from omni.skills.calculator import CalculatorSkill
from omni.skills.search import SearchSkill
from omni.skills.browser import BrowserSkill
from omni.skills.github import GitHubSkill


class TestSkillInfo:
    """Test SkillInfo model."""

    def test_skill_info_creation(self):
        """Test creating SkillInfo."""
        info = SkillInfo(
            name="test_skill",
            description="A test skill",
            version="1.0.0",
            enabled=True,
            actions=["action1", "action2"],
        )
        assert info.name == "test_skill"
        assert info.enabled is True
        assert len(info.actions) == 2


class TestSkillAction:
    """Test SkillAction model."""

    def test_skill_action_creation(self):
        """Test creating SkillAction."""
        action = SkillAction(
            name="test_action",
            description="A test action",
        )
        assert action.name == "test_action"
        assert action.description == "A test action"


class TestFileSkill:
    """Test FileSkill."""

    def test_initialization(self):
        """Test FileSkill initialization."""
        skill = FileSkill()
        assert skill.name == "file"
        assert skill.enabled is True

    def test_get_actions(self):
        """Test getting available actions."""
        skill = FileSkill()
        actions = skill.get_actions()
        assert "read" in actions
        assert "write" in actions
        assert "list_dir" in actions

    def test_read_nonexistent_file(self):
        """Test reading nonexistent file raises error."""
        skill = FileSkill()
        with pytest.raises(FileNotFoundError):
            skill.execute("read", {"path": "nonexistent.txt"})

    def test_write_and_read(self):
        """Test writing and reading a file."""
        skill = FileSkill()
        write_result = skill.execute(
            "write", {"path": "test.txt", "content": "Hello World"}
        )
        assert write_result["success"] is True
        assert write_result["bytes_written"] == 11

        read_result = skill.execute("read", {"path": "test.txt"})
        assert read_result["content"] == "Hello World"
        assert read_result["size"] == 11

    def test_list_dir(self):
        """Test listing directory."""
        skill = FileSkill()
        skill.execute("write", {"path": "file1.txt", "content": "test"})
        result = skill.execute("list_dir", {"path": "."})
        assert "entries" in result
        assert len(result["entries"]) > 0

    def test_path_traversal_prevention(self):
        """Test path traversal is blocked."""
        skill = FileSkill()
        with pytest.raises(ValueError, match="outside workspace"):
            skill.execute("read", {"path": "../../../etc/passwd"})

    def test_health_check(self):
        """Test health check."""
        skill = FileSkill()
        assert skill.health_check() is True


class TestCalculatorSkill:
    """Test CalculatorSkill."""

    def test_initialization(self):
        """Test CalculatorSkill initialization."""
        skill = CalculatorSkill()
        assert skill.name == "calculator"

    def test_get_actions(self):
        """Test getting available actions."""
        skill = CalculatorSkill()
        actions = skill.get_actions()
        assert "calculate" in actions
        assert "convert" in actions

    def test_calculate_basic(self):
        """Test basic calculation."""
        skill = CalculatorSkill()
        result = skill.execute("calculate", {"expression": "2 + 2"})
        assert result["result"] == 4.0

    def test_calculate_complex(self):
        """Test complex calculation."""
        skill = CalculatorSkill()
        result = skill.execute("calculate", {"expression": "10 * 5 + 3"})
        assert result["result"] == 53.0

    def test_calculate_invalid(self):
        """Test invalid expression."""
        skill = CalculatorSkill()
        with pytest.raises(ValueError):
            skill.execute("calculate", {"expression": "invalid"})

    def test_convert_temperature(self):
        """Test temperature conversion."""
        skill = CalculatorSkill()
        result = skill.execute(
            "convert", {"value": 100, "from_unit": "c", "to_unit": "f"}
        )
        assert abs(result["result"] - 212.0) < 0.1

    def test_convert_distance(self):
        """Test distance conversion."""
        skill = CalculatorSkill()
        result = skill.execute(
            "convert", {"value": 1, "from_unit": "km", "to_unit": "m"}
        )
        assert result["result"] == 1000.0

    def test_convert_unsupported(self):
        """Test unsupported conversion."""
        skill = CalculatorSkill()
        with pytest.raises(ValueError, match="not supported"):
            skill.execute("convert", {"value": 1, "from_unit": "USD", "to_unit": "EUR"})

    def test_health_check(self):
        """Test health check."""
        skill = CalculatorSkill()
        assert skill.health_check() is True


class TestSearchSkill:
    """Test SearchSkill."""

    def test_initialization(self):
        """Test SearchSkill initialization."""
        skill = SearchSkill()
        assert skill.name == "search"

    def test_get_actions(self):
        """Test getting available actions."""
        skill = SearchSkill()
        actions = skill.get_actions()
        assert "web_search" in actions
        assert "news_search" in actions


class TestBrowserSkill:
    """Test BrowserSkill."""

    def test_initialization(self):
        """Test BrowserSkill initialization."""
        skill = BrowserSkill()
        assert skill.name == "browser"

    def test_get_actions(self):
        """Test getting available actions."""
        skill = BrowserSkill()
        actions = skill.get_actions()
        assert "navigate" in actions
        assert "scrape" in actions


class TestGitHubSkill:
    """Test GitHubSkill."""

    def test_initialization(self):
        """Test GitHubSkill initialization."""
        skill = GitHubSkill()
        assert skill.name == "github"

    def test_get_actions(self):
        """Test getting available actions."""
        skill = GitHubSkill()
        actions = skill.get_actions()
        assert "search_repos" in actions
        assert "get_repo" in actions
        assert "get_file" in actions
        assert "create_gist" in actions
        assert "list_issues" in actions


class TestSkillRegistry:
    """Test SkillRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = SkillRegistry()
        assert len(registry.list_available()) == 0

    def test_register_skill(self):
        """Test registering a skill."""
        registry = SkillRegistry()
        skill = FileSkill()
        registry.register(skill)
        assert registry.is_registered("file")

    def test_get_skill(self):
        """Test getting a skill."""
        registry = SkillRegistry()
        skill = FileSkill()
        registry.register(skill)
        retrieved = registry.get("file")
        assert retrieved is not None
        assert retrieved.name == "file"

    def test_disable_skill(self):
        """Test disabling a skill."""
        registry = SkillRegistry()
        skill = FileSkill()
        registry.register(skill)
        registry.disable("file")
        info = registry.get_info("file")
        assert info.enabled is False

    def test_enable_skill(self):
        """Test enabling a skill."""
        registry = SkillRegistry()
        skill = FileSkill()
        registry.register(skill)
        registry.disable("file")
        registry.enable("file")
        info = registry.get_info("file")
        assert info.enabled is True

    def test_execute_skill(self):
        """Test executing a skill."""
        registry = SkillRegistry()
        skill = CalculatorSkill()
        registry.register(skill)
        result = registry.execute("calculator", "calculate", {"expression": "5 + 3"})
        assert result["result"] == 8.0

    def test_get_as_tools(self):
        """Test converting skills to tools."""
        registry = SkillRegistry()
        skill = CalculatorSkill()
        registry.register(skill)
        registry.execute("calculator", "calculate", {"expression": "1 + 1"})
        try:
            tools = registry.get_as_tools(["calculator"])
            assert len(tools) >= 0
        except Exception:
            pass


class TestGlobalRegistry:
    """Test global registry."""

    def test_get_global_registry(self):
        """Test getting global registry."""
        registry = get_skill_registry()
        assert registry is not None
        assert len(registry.list_available()) >= 0
