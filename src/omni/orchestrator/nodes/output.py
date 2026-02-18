"""Output node for the LangGraph workflow.

Formats and outputs the final response.
"""
from datetime import datetime

from omni.core.state import OmniState
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.nodes.output")


async def output(state: OmniState) -> dict:
    """Output the final response.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict with final response (terminal node)
    """
    logger.info("Outputting final response", task_id=state["task_id"])
    
    final_response = state.get("final_response", "No response generated.")
    
    # Store in database (async operation would go here)
    # For now, just log it
    logger.info(
        "Task completed",
        task_id=state["task_id"],
        response_length=len(final_response)
    )
    
    # Return the final state
    return {
        "final_response": final_response,
        "status": "completed"
    }
