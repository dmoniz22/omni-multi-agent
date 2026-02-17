"""Global state schema for OMNI.

Defines the state structures used throughout the LangGraph workflow.
Uses TypedDict for the top-level state (required by LangGraph) and
Pydantic models for nested structures that need validation.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Annotated

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from omni.core.constants import (
    ACTION_TYPES,
    COMPLEXITY_LEVELS,
    ROLE_SYSTEM,
    ROLE_USER,
    ROLE_ASSISTANT,
    STATUS_PENDING,
    STATUS_RUNNING,
    STATUS_WAITING_HUMAN,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STEP_TYPES,
    WORKFLOW_PATTERNS,
)


# =============================================================================
# Enums
# =============================================================================

class Status(str, Enum):
    """Task status values."""
    PENDING = STATUS_PENDING
    RUNNING = STATUS_RUNNING
    WAITING_HUMAN = STATUS_WAITING_HUMAN
    COMPLETED = STATUS_COMPLETED
    FAILED = STATUS_FAILED


class Role(str, Enum):
    """Context message roles."""
    SYSTEM = ROLE_SYSTEM
    USER = ROLE_USER
    ASSISTANT = ROLE_ASSISTANT


class Complexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class WorkflowPattern(str, Enum):
    """Workflow pattern types."""
    SINGLE_CREW = "single_crew"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ITERATIVE = "iterative"


class StepType(str, Enum):
    """Step record types."""
    QUERY_ANALYSIS = "query_analysis"
    ORCHESTRATOR_DECISION = "orchestrator_decision"
    CREW_EXECUTION = "crew_execution"
    VALIDATION = "validation"
    HUMAN_INPUT = "human_input"
    ERROR = "error"
    RESPONSE_COLLATION = "response_collation"


class Action(str, Enum):
    """Orchestrator action types."""
    DELEGATE = "delegate"
    ASK_HUMAN = "ask_human"
    COMPLETE = "complete"
    ERROR = "error"


# =============================================================================
# Pydantic Models (Nested Structures)
# =============================================================================

class StepRecord(BaseModel):
    """Record of a single step in execution history."""
    step_number: int
    step_type: StepType
    node_name: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: int = 0
    model_used: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextMessage(BaseModel):
    """A message in the conversation context."""
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QueryAnalysis(BaseModel):
    """Analysis of the user query."""
    intent: str
    required_departments: List[str]
    complexity: Complexity
    workflow_pattern: WorkflowPattern
    parameters: Dict[str, Any] = Field(default_factory=dict)


class OrchestratorDecision(BaseModel):
    """Decision made by the orchestrator."""
    action: Action
    target_crew: Optional[str] = None
    crew_input: Optional[Dict[str, Any]] = None
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class CrewInfo(BaseModel):
    """Information about an available crew."""
    name: str
    description: str
    input_schema_name: str
    output_schema_name: str


class SkillInfo(BaseModel):
    """Information about an available skill."""
    name: str
    description: str
    enabled: bool = True


class ControlFlags(BaseModel):
    """Control flags for workflow execution."""
    max_steps: int = 20
    current_step: int = 0
    is_complete: bool = False
    timeout_seconds: int = 300
    started_at: Optional[datetime] = None


class HITLState(BaseModel):
    """Human-in-the-loop state."""
    pending: bool = False
    prompt: str = ""
    options: Optional[List[str]] = None
    response: Optional[str] = None
    responded_at: Optional[datetime] = None


class ErrorState(BaseModel):
    """Error tracking state."""
    error_type: str
    error_message: str
    retry_count: int = 0
    max_retries: int = 3
    fallback_crew: Optional[str] = None


# =============================================================================
# Helper Functions for Reducers
# =============================================================================

def add_to_list(existing: List[Any], new: List[Any]) -> List[Any]:
    """Reducer function for appending to lists."""
    return existing + new


def update_dict(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer function for merging dictionaries."""
    result = existing.copy()
    result.update(new)
    return result


# =============================================================================
# Main State TypedDict
# =============================================================================

class OmniState(TypedDict):
    """Global state for the LangGraph workflow.
    
    This is a TypedDict (not Pydantic BaseModel) as required by LangGraph.
    All fields must be JSON-serializable for PostgreSQL checkpointing.
    """
    # Identifiers
    task_id: str
    session_id: str
    
    # Task Information
    original_task: str
    current_objective: str
    status: str
    
    # Execution History
    history: Annotated[List[Dict[str, Any]], add_to_list]
    
    # Results
    partial_results: Annotated[Dict[str, Any], update_dict]
    
    # Context
    context: List[Dict[str, Any]]
    
    # Analysis and Decisions
    query_analysis: Optional[Dict[str, Any]]
    current_decision: Optional[Dict[str, Any]]
    
    # Available Resources
    available_crews: List[Dict[str, Any]]
    available_skills: List[Dict[str, Any]]
    
    # Control
    control: Dict[str, Any]
    
    # Human-in-the-Loop
    human_in_the_loop: Optional[Dict[str, Any]]
    
    # Error Handling
    error_state: Optional[Dict[str, Any]]
    
    # Output
    final_response: Optional[str]


# =============================================================================
# State Factory Functions
# =============================================================================

def create_initial_state(
    task_id: str,
    session_id: str,
    original_task: str,
) -> OmniState:
    """Create initial state for a new task.
    
    Args:
        task_id: Unique task identifier
        session_id: Session identifier
        original_task: The original user task
        
    Returns:
        OmniState: Initial state dictionary
    """
    return {
        "task_id": task_id,
        "session_id": session_id,
        "original_task": original_task,
        "current_objective": original_task,
        "status": STATUS_PENDING,
        "history": [],
        "partial_results": {},
        "context": [],
        "query_analysis": None,
        "current_decision": None,
        "available_crews": [],
        "available_skills": [],
        "control": {
            "max_steps": 20,
            "current_step": 0,
            "is_complete": False,
            "timeout_seconds": 300,
            "started_at": datetime.utcnow().isoformat(),
        },
        "human_in_the_loop": None,
        "error_state": None,
        "final_response": None,
    }


def state_to_pydantic(state: OmniState) -> Dict[str, Any]:
    """Convert state values to Pydantic models where applicable.
    
    This is useful for validation before passing to components
    that expect Pydantic models.
    
    Args:
        state: The raw state dictionary
        
    Returns:
        Dict with Pydantic model instances where applicable
    """
    result = dict(state)
    
    if state.get("query_analysis"):
        result["query_analysis"] = QueryAnalysis(**state["query_analysis"])
    
    if state.get("current_decision"):
        result["current_decision"] = OrchestratorDecision(**state["current_decision"])
    
    if state.get("control"):
        result["control"] = ControlFlags(**state["control"])
    
    if state.get("human_in_the_loop"):
        result["human_in_the_loop"] = HITLState(**state["human_in_the_loop"])
    
    if state.get("error_state"):
        result["error_state"] = ErrorState(**state["error_state"])
    
    return result
