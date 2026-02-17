"""System-wide constants for OMNI."""

# System Constants
SYSTEM_NAME = "OMNI"
SYSTEM_VERSION = "0.1.0"
SYSTEM_DESCRIPTION = "Multi-agent orchestration system with LangGraph, CrewAI, and PydanticAI"

# Default Values
DEFAULT_MAX_STEPS = 20
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_SECONDS = 1

# State Constants
MAX_HISTORY_STEPS = 100
MAX_PARTIAL_RESULTS = 50
MAX_CONTEXT_MESSAGES = 20

# Database Constants
DEFAULT_POOL_SIZE = 10
DEFAULT_MAX_OVERFLOW = 20
DEFAULT_POSTGRES_PORT = 5432

# Ollama Constants
DEFAULT_OLLAMA_BASE_URL = "http://host.docker.internal:11434"
DEFAULT_OLLAMA_TIMEOUT = 120

# Memory Constants
DEFAULT_EMBEDDING_DIMENSION = 768
DEFAULT_SIMILARITY_THRESHOLD = 0.7
DEFAULT_MEMORY_TOP_K = 5
DEFAULT_CHECKPOINT_RETENTION = 100

# API Constants
DEFAULT_API_HOST = "0.0.0.0"
DEFAULT_API_PORT = 8000
DEFAULT_GRADIO_PORT = 7860

# Session Constants
DEFAULT_SESSION_TIMEOUT_MINUTES = 60
DEFAULT_MAX_CONCURRENT_SESSIONS = 10

# Rate Limiting
DEFAULT_RATE_LIMIT_RPM = 60
DEFAULT_RATE_LIMIT_BURST = 10

# File Constants
DEFAULT_MAX_FILE_SIZE_MB = 10
DEFAULT_WORKSPACE_ROOT = "./workspace"

# Log Levels
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Process Types
PROCESS_TYPES = ["sequential", "hierarchical", "parallel"]

# Workflow Patterns
WORKFLOW_PATTERNS = ["single_crew", "sequential", "parallel", "iterative"]

# Step Types
STEP_TYPES = [
    "query_analysis",
    "orchestrator_decision",
    "crew_execution",
    "validation",
    "human_input",
    "error",
    "response_collation",
]

# Action Types
ACTION_TYPES = ["delegate", "ask_human", "complete", "error"]

# Status Values
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_WAITING_HUMAN = "waiting_human"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Role Types
ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"

# Complexity Levels
COMPLEXITY_SIMPLE = "simple"
COMPLEXITY_MODERATE = "moderate"
COMPLEXITY_COMPLEX = "complex"
COMPLEXITY_LEVELS = [COMPLEXITY_SIMPLE, COMPLEXITY_MODERATE, COMPLEXITY_COMPLEX]

# Intent Categories
INTENT_CATEGORIES = [
    "github_operations",
    "research",
    "social_media",
    "analysis",
    "writing",
    "coding",
    "general_query",
]
