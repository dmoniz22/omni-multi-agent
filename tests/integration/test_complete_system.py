"""Integration tests for the complete OMNI system."""

import pytest


class TestSystemIntegration:
    """Integration tests for the complete system."""

    def test_imports_all_modules(self):
        """Test that all main modules can be imported."""
        from omni import crews
        from omni.api import app
        from omni.memory import ContextManager
        from omni.skills import base
        from omni.validators import schemas

        assert crews is not None
        assert app is not None

    def test_crew_registry_discovery(self):
        """Test crew discovery works."""
        from omni.registry import reset_crew_registry

        registry = reset_crew_registry()
        available = registry.list_available()
        assert len(available) >= 1

    def test_skill_registry_discovery(self):
        """Test skill discovery works."""
        from omni.skills.registry import SkillRegistry

        registry = SkillRegistry()
        registry.discover()
        available = registry.list_available()
        assert len(available) >= 1

    def test_context_manager(self):
        """Test context manager works."""
        from omni.memory import ContextManager

        cm = ContextManager()
        state = {
            "original_task": "Test task",
            "control": {"current_step": 1, "max_steps": 20},
        }
        prompt = cm.build_user_prompt(state)
        assert "Test task" in prompt

    def test_api_app_creation(self):
        """Test API app can be created."""
        from omni.api.app import create_app

        app = create_app()
        assert app is not None
        assert app.title == "OMNI API"

    def test_file_skill_operations(self):
        """Test file skill operations."""
        from omni.skills.file import FileSkill

        skill = FileSkill()
        result = skill.execute("write", {"path": "test.txt", "content": "Hello"})
        assert result["success"] is True

        result = skill.execute("read", {"path": "test.txt"})
        assert result["content"] == "Hello"

    def test_calculator_skill(self):
        """Test calculator skill."""
        from omni.skills.calculator import CalculatorSkill

        skill = CalculatorSkill()
        result = skill.execute("calculate", {"expression": "10 + 5"})
        assert result["result"] == 15.0

    def test_state_models(self):
        """Test state models."""
        from omni.core.state import OmniState, create_initial_state

        state = create_initial_state(
            task_id="test-123",
            session_id="session-123",
            original_task="Test task",
        )
        assert state["task_id"] == "test-123"
        assert state["original_task"] == "Test task"

    def test_validation_schemas(self):
        """Test validation schemas."""
        from omni.validators.schemas.common import ValidatedResult

        result = ValidatedResult(
            schema_name="test_schema",
            valid=True,
            data={"key": "value"},
            errors=[],
        )
        assert result.valid is True
        assert result.data["key"] == "value"

    def test_crew_base_class(self):
        """Test base crew class."""
        from omni.crews.base import BaseCrew

        assert hasattr(BaseCrew, "name")
        assert hasattr(BaseCrew, "execute")

    def test_skill_base_class(self):
        """Test base skill class."""
        from omni.skills.base import BaseSkill

        assert hasattr(BaseSkill, "name")
        assert hasattr(BaseSkill, "execute")

    def test_api_routes_registered(self):
        """Test API routes are registered."""
        from omni.api.app import create_app

        app = create_app()
        routes = [r.path for r in app.routes]
        assert any("/health" in r for r in routes)
        assert any("/tasks" in r for r in routes)
        assert any("/sessions" in r for r in routes)
