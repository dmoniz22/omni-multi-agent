"""Unit tests for omni.core.exceptions module."""
import pytest

from omni.core import exceptions


class TestOmniError:
    """Test suite for OmniError base class."""
    
    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = exceptions.OmniError("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.details == {}
    
    def test_exception_with_details(self):
        """Test exception with details."""
        details = {"key": "value", "count": 42}
        exc = exceptions.OmniError("Test error", details=details)
        assert exc.details == details
    
    def test_exception_can_be_raised(self):
        """Test exception can be raised and caught."""
        with pytest.raises(exceptions.OmniError) as exc_info:
            raise exceptions.OmniError("Test message")
        assert str(exc_info.value) == "Test message"


class TestExceptionHierarchy:
    """Test suite for exception hierarchy."""
    
    def test_orchestration_errors_inherit(self):
        """Test orchestration errors inherit from OmniError."""
        assert issubclass(exceptions.OrchestrationError, exceptions.OmniError)
        assert issubclass(exceptions.GraphError, exceptions.OrchestrationError)
        assert issubclass(exceptions.NodeError, exceptions.OrchestrationError)
        assert issubclass(exceptions.EdgeError, exceptions.OrchestrationError)
        assert issubclass(exceptions.StateError, exceptions.OrchestrationError)
        assert issubclass(exceptions.CheckpointError, exceptions.OrchestrationError)
    
    def test_crew_errors_inherit(self):
        """Test crew errors inherit from OmniError."""
        assert issubclass(exceptions.CrewError, exceptions.OmniError)
        assert issubclass(exceptions.CrewNotFoundError, exceptions.CrewError)
        assert issubclass(exceptions.CrewExecutionError, exceptions.CrewError)
        assert issubclass(exceptions.AgentError, exceptions.CrewError)
        assert issubclass(exceptions.TaskError, exceptions.CrewError)
    
    def test_validation_errors_inherit(self):
        """Test validation errors inherit from OmniError."""
        assert issubclass(exceptions.ValidationError, exceptions.OmniError)
        assert issubclass(exceptions.SchemaValidationError, exceptions.ValidationError)
        assert issubclass(exceptions.SchemaNotFoundError, exceptions.ValidationError)
        assert issubclass(exceptions.ValidationAgentError, exceptions.ValidationError)
    
    def test_skill_errors_inherit(self):
        """Test skill errors inherit from OmniError."""
        assert issubclass(exceptions.SkillError, exceptions.OmniError)
        assert issubclass(exceptions.SkillNotFoundError, exceptions.SkillError)
        assert issubclass(exceptions.SkillExecutionError, exceptions.SkillError)
        assert issubclass(exceptions.SkillActionError, exceptions.SkillError)
        assert issubclass(exceptions.SkillNotEnabledError, exceptions.SkillError)
    
    def test_database_errors_inherit(self):
        """Test database errors inherit from OmniError."""
        assert issubclass(exceptions.DatabaseError, exceptions.OmniError)
        assert issubclass(exceptions.ConnectionError, exceptions.DatabaseError)
        assert issubclass(exceptions.QueryError, exceptions.DatabaseError)
        assert issubclass(exceptions.RepositoryError, exceptions.DatabaseError)
        assert issubclass(exceptions.MigrationError, exceptions.DatabaseError)
    
    def test_model_errors_inherit(self):
        """Test model errors inherit from OmniError."""
        assert issubclass(exceptions.ModelError, exceptions.OmniError)
        assert issubclass(exceptions.ModelNotFoundError, exceptions.ModelError)
        assert issubclass(exceptions.ModelConnectionError, exceptions.ModelError)
        assert issubclass(exceptions.ModelTimeoutError, exceptions.ModelError)
        assert issubclass(exceptions.ModelResponseError, exceptions.ModelError)
    
    def test_auth_errors_inherit(self):
        """Test auth errors inherit from OmniError."""
        assert issubclass(exceptions.AuthError, exceptions.OmniError)
        assert issubclass(exceptions.AuthenticationError, exceptions.AuthError)
        assert issubclass(exceptions.AuthorizationError, exceptions.AuthError)
        assert issubclass(exceptions.TokenError, exceptions.AuthError)
        assert issubclass(exceptions.SessionError, exceptions.AuthError)
    
    def test_memory_errors_inherit(self):
        """Test memory errors inherit from OmniError."""
        assert issubclass(exceptions.MemoryError, exceptions.OmniError)
        assert issubclass(exceptions.EmbeddingError, exceptions.MemoryError)
        assert issubclass(exceptions.SimilaritySearchError, exceptions.MemoryError)
        assert issubclass(exceptions.ContextError, exceptions.MemoryError)
    
    def test_configuration_errors_inherit(self):
        """Test configuration errors inherit from OmniError."""
        assert issubclass(exceptions.ConfigurationError, exceptions.OmniError)
        assert issubclass(exceptions.ConfigFileError, exceptions.ConfigurationError)
        assert issubclass(exceptions.ConfigValidationError, exceptions.ConfigurationError)
    
    def test_api_errors_inherit(self):
        """Test API errors inherit from OmniError."""
        assert issubclass(exceptions.APIError, exceptions.OmniError)
        assert issubclass(exceptions.RouteError, exceptions.APIError)
        assert issubclass(exceptions.MiddlewareError, exceptions.APIError)


class TestExceptionUsage:
    """Test suite for exception usage patterns."""
    
    def test_catching_base_exception(self):
        """Test that all exceptions can be caught via base class."""
        exceptions_to_test = [
            exceptions.OrchestrationError("test"),
            exceptions.CrewError("test"),
            exceptions.ValidationError("test"),
            exceptions.SkillError("test"),
            exceptions.DatabaseError("test"),
            exceptions.ModelError("test"),
            exceptions.AuthError("test"),
            exceptions.MemoryError("test"),
            exceptions.ConfigurationError("test"),
            exceptions.APIError("test"),
        ]
        
        for exc in exceptions_to_test:
            with pytest.raises(exceptions.OmniError):
                raise exc
    
    def test_exception_attributes(self):
        """Test exception attributes are accessible."""
        details = {"key": "value"}
        exc = exceptions.CrewNotFoundError(
            "Crew not found",
            details=details
        )
        assert exc.message == "Crew not found"
        assert exc.details == details
        assert isinstance(exc, exceptions.OmniError)
