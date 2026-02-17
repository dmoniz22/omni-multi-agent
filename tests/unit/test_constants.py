"""Unit tests for omni.core.constants module."""
import pytest

from omni.core import constants


class TestConstants:
    """Test suite for constants module."""
    
    def test_system_constants(self):
        """Test system-level constants are defined."""
        assert constants.SYSTEM_NAME == "OMNI"
        assert constants.SYSTEM_VERSION == "0.1.0"
        assert isinstance(constants.SYSTEM_DESCRIPTION, str)
    
    def test_default_values(self):
        """Test default value constants."""
        assert constants.DEFAULT_MAX_STEPS == 20
        assert constants.DEFAULT_TIMEOUT_SECONDS == 300
        assert constants.DEFAULT_MAX_RETRIES == 3
        assert constants.DEFAULT_RETRY_DELAY_SECONDS == 1
    
    def test_state_constants(self):
        """Test state-related constants."""
        assert constants.MAX_HISTORY_STEPS == 100
        assert constants.MAX_PARTIAL_RESULTS == 50
        assert constants.MAX_CONTEXT_MESSAGES == 20
    
    def test_database_constants(self):
        """Test database constants."""
        assert constants.DEFAULT_POOL_SIZE == 10
        assert constants.DEFAULT_MAX_OVERFLOW == 20
        assert constants.DEFAULT_POSTGRES_PORT == 5432
    
    def test_ollama_constants(self):
        """Test Ollama constants."""
        assert isinstance(constants.DEFAULT_OLLAMA_BASE_URL, str)
        assert constants.DEFAULT_OLLAMA_TIMEOUT == 120
    
    def test_memory_constants(self):
        """Test memory constants."""
        assert constants.DEFAULT_EMBEDDING_DIMENSION == 768
        assert constants.DEFAULT_SIMILARITY_THRESHOLD == 0.7
        assert constants.DEFAULT_MEMORY_TOP_K == 5
    
    def test_api_constants(self):
        """Test API constants."""
        assert constants.DEFAULT_API_HOST == "0.0.0.0"
        assert constants.DEFAULT_API_PORT == 8000
        assert constants.DEFAULT_GRADIO_PORT == 7860
    
    def test_status_values(self):
        """Test status constants."""
        assert constants.STATUS_PENDING == "pending"
        assert constants.STATUS_RUNNING == "running"
        assert constants.STATUS_WAITING_HUMAN == "waiting_human"
        assert constants.STATUS_COMPLETED == "completed"
        assert constants.STATUS_FAILED == "failed"
    
    def test_complexity_levels(self):
        """Test complexity level constants."""
        assert constants.COMPLEXITY_SIMPLE == "simple"
        assert constants.COMPLEXITY_MODERATE == "moderate"
        assert constants.COMPLEXITY_COMPLEX == "complex"
        assert len(constants.COMPLEXITY_LEVELS) == 3
    
    def test_role_types(self):
        """Test role type constants."""
        assert constants.ROLE_SYSTEM == "system"
        assert constants.ROLE_USER == "user"
        assert constants.ROLE_ASSISTANT == "assistant"
    
    def test_enum_lists(self):
        """Test that enum lists contain expected values."""
        assert "simple" in constants.COMPLEXITY_LEVELS
        assert "moderate" in constants.COMPLEXITY_LEVELS
        assert "complex" in constants.COMPLEXITY_LEVELS
        
        assert "single_crew" in constants.WORKFLOW_PATTERNS
        assert "sequential" in constants.WORKFLOW_PATTERNS
        assert "parallel" in constants.WORKFLOW_PATTERNS
        assert "iterative" in constants.WORKFLOW_PATTERNS
        
        assert "delegate" in constants.ACTION_TYPES
        assert "ask_human" in constants.ACTION_TYPES
        assert "complete" in constants.ACTION_TYPES
        assert "error" in constants.ACTION_TYPES
