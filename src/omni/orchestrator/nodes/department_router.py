"""Department router node for the LangGraph workflow.

Routes to the appropriate crew based on orchestrator decision.
"""
from datetime import datetime

from omni.core.state import OmniState, StepType
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.nodes.department_router")


async def department_router(state: OmniState) -> dict:
    """Route to the appropriate department/crew.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict with updates to state
    """
    decision = state.get("current_decision", {})
    target_crew = decision.get("target_crew")
    
    logger.info("Routing to department", crew=target_crew)
    
    if not target_crew:
        logger.error("No target crew specified")
        return {
            "error_state": {
                "error_type": "RoutingError",
                "error_message": "No target crew specified in decision",
                "retry_count": 0,
                "max_retries": 3
            },
            "history": [{
                "step_number": state["control"]["current_step"],
                "step_type": StepType.ERROR,
                "node_name": "department_router",
                "input_data": decision,
                "output_data": {"error": "No target crew specified"},
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": 0,
                "error": "No target crew specified"
            }]
        }
    
    # For Phase 3: just validate the crew name
    valid_crews = ["github", "research", "social", "analysis", "writing", "coding"]
    
    if target_crew not in valid_crews:
        logger.error("Invalid crew specified", crew=target_crew)
        return {
            "error_state": {
                "error_type": "RoutingError",
                "error_message": f"Invalid crew: {target_crew}",
                "retry_count": 0,
                "max_retries": 3
            },
            "history": [{
                "step_number": state["control"]["current_step"],
                "step_type": StepType.ERROR,
                "node_name": "department_router",
                "input_data": decision,
                "output_data": {"error": f"Invalid crew: {target_crew}"},
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": 0,
                "error": f"Invalid crew: {target_crew}"
            }]
        }
    
    logger.info("Routing successful", crew=target_crew)
    
    return {
        "history": [{
            "step_number": state["control"]["current_step"],
            "step_type": StepType.ORCHESTRATOR_DECISION,
            "node_name": "department_router",
            "input_data": decision,
            "output_data": {"target_crew": target_crew, "status": "routed"},
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 0
        }]
    }
