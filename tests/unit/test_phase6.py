"""Unit tests for Phase 6 components."""

import pytest
from omni.memory.context import ContextManager, get_context_manager
from omni.orchestrator.prompts import (
    build_system_prompt,
    build_user_prompt,
    format_partial_results,
    format_history,
    get_departments_json,
)


class TestContextManager:
    """Tests for ContextManager."""

    def test_initialization(self):
        """Test context manager initialization."""
        cm = ContextManager()
        assert cm.max_tokens == 8192
        assert cm.available_tokens > 0

    def test_estimate_tokens(self):
        """Test token estimation."""
        cm = ContextManager()
        text = "Hello world this is a test"
        tokens = cm.estimate_tokens(text)
        assert tokens > 0

    def test_build_context_empty(self):
        """Test building context with empty state."""
        cm = ContextManager()
        state = {
            "original_task": "Test task",
            "current_objective": "",
            "partial_results": {},
            "history": [],
            "context_messages": [],
        }
        context = cm.build_context(state)
        assert "task" in context
        assert "results" in context

    def test_format_partial_results(self):
        """Test formatting partial results."""
        results = {
            "research": {"summary": "Found information about AI"},
            "writing": {"summary": "Wrote blog post"},
        }
        formatted = format_partial_results(results)
        assert "research" in formatted
        assert "Found information" in formatted

    def test_format_partial_results_empty(self):
        """Test formatting empty results."""
        formatted = format_partial_results({})
        assert "(No completed work yet)" in formatted

    def test_format_history(self):
        """Test formatting history."""
        history = [
            {
                "step_number": 1,
                "step_type": "query_analysis",
                "node_name": "query_analyzer",
                "output_data": {"intent": "research"},
            },
            {
                "step_number": 2,
                "step_type": "orchestrator_decision",
                "node_name": "orchestrator_decision",
                "output_data": {"action": "delegate"},
            },
        ]
        formatted = format_history(history)
        assert "Step 1" in formatted
        assert "delegate" in formatted

    def test_build_user_prompt(self):
        """Test building user prompt."""
        prompt = build_user_prompt(
            original_task="Test task",
            current_objective="Find info",
            current_step=1,
            max_steps=10,
            formatted_partial_results="- research: done",
            last_3_steps_summary="Step 1: analysis",
            recent_context_messages="context here",
        )
        assert "Test task" in prompt
        assert "STEP: 1 / 10" in prompt


class TestPrompts:
    """Tests for prompt builders."""

    def test_get_departments_json(self):
        """Test building departments JSON."""
        crews = [
            {"name": "research", "description": "Web research"},
            {"name": "writing", "description": "Content writing"},
        ]
        result = get_departments_json(crews)
        assert "research" in result
        assert "Web research" in result

    def test_build_system_prompt(self):
        """Test building system prompt."""
        departments = '[{"name": "research", "description": "Research dept"}]'
        prompt = build_system_prompt(departments)
        assert "OMNI Orchestrator" in prompt
        assert "Research dept" in prompt
        assert "delegate" in prompt
        assert "ask_human" in prompt
        assert "complete" in prompt
        assert "error" in prompt
