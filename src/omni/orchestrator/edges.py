"""Edge routing functions for the LangGraph workflow."""
from omni.core.state import OmniState
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.edges")


def route_after_decision(state: OmniState) -> str:
    """Route after orchestrator decision.
    
    Args:
        state: Current workflow state
        
    Returns:
        str: Next node name
    """
    decision = state.get("current_decision", {})
    action = decision.get("action")
    
    if action == "delegate":
        return "department_router"
    elif action == "ask_human":
        return "human_in_the_loop"
    elif action == "complete":
        return "response_collator"
    elif action == "error":
        return "exception_handler"
    else:
        logger.warning(f"Unknown action: {action}, defaulting to exception_handler")
        return "exception_handler"


def route_after_validation(state: OmniState) -> str:
    """Route after validation node.
    
    Args:
        state: Current workflow state
        
    Returns:
        str: Next node name
    """
    # For Phase 3: Always valid
    # In production, check validation results
    return "orchestrator_decision"


def route_after_exception(state: OmniState) -> str:
    """Route after exception handler.
    
    Args:
        state: Current workflow state
        
    Returns:
        str: Next node name
    """
    error_state = state.get("error_state", {})
    retry_count = error_state.get("retry_count", 0)
    max_retries = error_state.get("max_retries", 3)
    
    if retry_count < max_retries:
        return "orchestrator_decision"
    else:
        return "response_collator"
