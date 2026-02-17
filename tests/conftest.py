"""Test configuration and fixtures for OMNI."""
import pytest


@pytest.fixture
def sample_task_id():
    """Sample task ID for testing."""
    return "test-task-123"


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return "test-session-456"


@pytest.fixture
def sample_task():
    """Sample task description for testing."""
    return "Research the latest trends in AI agents"
