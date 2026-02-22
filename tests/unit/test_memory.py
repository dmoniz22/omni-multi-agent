"""Tests for the memory system."""

import pytest

from omni.memory.context import ContextManager, get_context_manager
from omni.memory.short_term import ShortTermMemory, get_short_term_memory
from omni.memory.long_term import LongTermMemory, get_long_term_memory, MemoryEntry


class TestContextManager:
    """Test ContextManager."""

    def test_initialization(self):
        """Test ContextManager initialization."""
        cm = ContextManager()
        assert cm.max_tokens == 8192
        assert cm.available_tokens > 0

    def test_custom_tokens(self):
        """Test custom token limits."""
        cm = ContextManager(max_tokens=4096, reserved_tokens=1024)
        assert cm.max_tokens == 4096
        assert cm.available_tokens == 3072

    def test_estimate_tokens(self):
        """Test token estimation."""
        cm = ContextManager()
        text = "Hello world this is a test"
        tokens = cm.estimate_tokens(text)
        assert tokens > 0

    def test_build_context_empty(self):
        """Test building context with empty state."""
        cm = ContextManager()
        state = {}
        context = cm.build_context(state)
        assert "task" in context
        assert "objective" in context

    def test_build_context_with_data(self):
        """Test building context with state data."""
        cm = ContextManager()
        state = {
            "original_task": "Test task",
            "current_objective": "Test objective",
            "partial_results": {"research": {"summary": "Test result"}},
            "history": [],
        }
        context = cm.build_context(state)
        assert "Test task" in context["task"]

    def test_format_partial_results(self):
        """Test formatting partial results."""
        cm = ContextManager()
        results = {"research": {"summary": "Found information"}}
        formatted = cm._format_results(results)
        assert "research" in formatted

    def test_format_partial_results_empty(self):
        """Test formatting empty results."""
        cm = ContextManager()
        formatted = cm._format_results({})
        assert "No completed work" in formatted

    def test_format_history(self):
        """Test formatting history."""
        cm = ContextManager()
        history = [
            {
                "step_number": 1,
                "step_type": "query_analysis",
                "node_name": "analyzer",
                "output_data": {},
            },
        ]
        formatted = cm._format_history(history)
        assert "Step 1" in formatted

    def test_build_user_prompt(self):
        """Test building user prompt."""
        cm = ContextManager()
        state = {
            "original_task": "My task",
            "current_objective": "My objective",
            "partial_results": {},
            "history": [],
            "control": {"current_step": 1, "max_steps": 20},
        }
        prompt = cm.build_user_prompt(state)
        assert "My task" in prompt
        assert "STEP: 1 / 20" in prompt


class TestShortTermMemory:
    """Test ShortTermMemory."""

    def test_initialization(self):
        """Test ShortTermMemory initialization."""
        memory = ShortTermMemory()
        assert memory.is_configured is False

    def test_with_checkpointer(self):
        """Test with checkpointer."""
        memory = ShortTermMemory(checkpointer="mock")
        assert memory.is_configured is True


class TestLongTermMemory:
    """Test LongTermMemory."""

    def test_initialization(self):
        """Test LongTermMemory initialization."""
        memory = LongTermMemory()
        assert memory.is_configured is False
        assert memory._vector_dimension == 768
        assert memory._top_k == 5

    def test_custom_config(self):
        """Test custom configuration."""
        memory = LongTermMemory(vector_dimension=384, top_k=10)
        assert memory._vector_dimension == 384
        assert memory._top_k == 10


class TestMemoryEntry:
    """Test MemoryEntry model."""

    def test_creation(self):
        """Test creating MemoryEntry."""
        entry = MemoryEntry(
            session_id="test-session",
            content="Test memory",
            memory_type="task",
        )
        assert entry.session_id == "test-session"
        assert entry.content == "Test memory"
        assert entry.memory_type == "task"

    def test_with_metadata(self):
        """Test with metadata."""
        entry = MemoryEntry(
            session_id="test-session",
            content="Test memory",
            metadata={"key": "value"},
        )
        assert entry.metadata["key"] == "value"


class TestGlobalMemory:
    """Test global memory instances."""

    def test_get_context_manager(self):
        """Test getting global context manager."""
        cm = get_context_manager()
        assert isinstance(cm, ContextManager)

    def test_get_short_term_memory(self):
        """Test getting global short-term memory."""
        memory = get_short_term_memory()
        assert isinstance(memory, ShortTermMemory)

    def test_get_long_term_memory(self):
        """Test getting global long-term memory."""
        memory = get_long_term_memory()
        assert isinstance(memory, LongTermMemory)
