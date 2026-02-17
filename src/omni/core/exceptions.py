"""Exception hierarchy for OMNI."""
from typing import Optional


class OmniError(Exception):
    """Base exception for all OMNI errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# =============================================================================
# Orchestration Errors
# =============================================================================

class OrchestrationError(OmniError):
    """Base exception for orchestration-related errors."""
    pass


class GraphError(OrchestrationError):
    """Error in the LangGraph state graph."""
    pass


class NodeError(OrchestrationError):
    """Error in a graph node execution."""
    pass


class EdgeError(OrchestrationError):
    """Error in graph edge routing."""
    pass


class StateError(OrchestrationError):
    """Error in state management."""
    pass


class CheckpointError(OrchestrationError):
    """Error in checkpoint persistence."""
    pass


# =============================================================================
# Crew Errors
# =============================================================================

class CrewError(OmniError):
    """Base exception for CrewAI-related errors."""
    pass


class CrewNotFoundError(CrewError):
    """Requested crew not found in registry."""
    pass


class CrewExecutionError(CrewError):
    """Error during crew execution."""
    pass


class AgentError(CrewError):
    """Error in agent execution."""
    pass


class TaskError(CrewError):
    """Error in task definition or execution."""
    pass


# =============================================================================
# Validation Errors
# =============================================================================

class ValidationError(OmniError):
    """Base exception for validation-related errors."""
    pass


class SchemaValidationError(ValidationError):
    """Error validating data against schema."""
    pass


class SchemaNotFoundError(ValidationError):
    """Requested schema not found."""
    pass


class ValidationAgentError(ValidationError):
    """Error in validation agent execution."""
    pass


# =============================================================================
# Skill Errors
# =============================================================================

class SkillError(OmniError):
    """Base exception for skill-related errors."""
    pass


class SkillNotFoundError(SkillError):
    """Requested skill not found."""
    pass


class SkillExecutionError(SkillError):
    """Error during skill execution."""
    pass


class SkillActionError(SkillError):
    """Error in skill action execution."""
    pass


class SkillNotEnabledError(SkillError):
    """Skill is registered but not enabled."""
    pass


# =============================================================================
# Database Errors
# =============================================================================

class DatabaseError(OmniError):
    """Base exception for database-related errors."""
    pass


class ConnectionError(DatabaseError):
    """Error connecting to database."""
    pass


class QueryError(DatabaseError):
    """Error executing database query."""
    pass


class RepositoryError(DatabaseError):
    """Error in repository operation."""
    pass


class MigrationError(DatabaseError):
    """Error during database migration."""
    pass


# =============================================================================
# Model Errors
# =============================================================================

class ModelError(OmniError):
    """Base exception for LLM model-related errors."""
    pass


class ModelNotFoundError(ModelError):
    """Requested model not found."""
    pass


class ModelConnectionError(ModelError):
    """Error connecting to model provider."""
    pass


class ModelTimeoutError(ModelError):
    """Model request timed out."""
    pass


class ModelResponseError(ModelError):
    """Error in model response."""
    pass


# =============================================================================
# Authentication/Authorization Errors
# =============================================================================

class AuthError(OmniError):
    """Base exception for authentication/authorization errors."""
    pass


class AuthenticationError(AuthError):
    """User authentication failed."""
    pass


class AuthorizationError(AuthError):
    """User not authorized for operation."""
    pass


class TokenError(AuthError):
    """Error with JWT token."""
    pass


class SessionError(AuthError):
    """Error with session management."""
    pass


# =============================================================================
# Memory Errors
# =============================================================================

class MemoryError(OmniError):
    """Base exception for memory-related errors."""
    pass


class EmbeddingError(MemoryError):
    """Error generating embeddings."""
    pass


class SimilaritySearchError(MemoryError):
    """Error in similarity search."""
    pass


class ContextError(MemoryError):
    """Error managing context window."""
    pass


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(OmniError):
    """Base exception for configuration errors."""
    pass


class ConfigFileError(ConfigurationError):
    """Error loading configuration file."""
    pass


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed."""
    pass


# =============================================================================
# API Errors
# =============================================================================

class APIError(OmniError):
    """Base exception for API-related errors."""
    pass


class RouteError(APIError):
    """Error in API route."""
    pass


class MiddlewareError(APIError):
    """Error in middleware."""
    pass
