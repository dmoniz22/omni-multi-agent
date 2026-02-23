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
    elif action == "complete":
        return "response_collator"
    elif action == "ask_human":
        # For now, skip to response collator (human-in-the-loop not implemented)
        logger.info("Human-in-the-loop requested, skipping to response")
        return "response_collator"
    elif action == "error":
        logger.warning("Error action returned, going to response")
        return "response_collator"
    else:
        # Default to department router for unknown actions
        logger.warning(f"Unknown action: {action}, defaulting to department_router")
        return "department_router"


def route_after_validation(state: OmniState) -> str:
    """Route after validation node.

    Args:
        state: Current workflow state

    Returns:
        str: Next node name
    """
    # For now, always go back to orchestrator decision
    # In production, could check validation results and route accordingly
    return "orchestrator_decision"
