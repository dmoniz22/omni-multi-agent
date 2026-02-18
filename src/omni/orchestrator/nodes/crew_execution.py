"""Crew execution node for the LangGraph workflow.

Executes the crew with the given input.
"""
from datetime import datetime

from omni.core.state import OmniState, StepType
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.nodes.crew_execution")


async def crew_execution(state: OmniState) -> dict:
    """Execute the crew.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict with updates to state
    """
    decision = state.get("current_decision", {})
    target_crew = decision.get("target_crew")
    crew_input = decision.get("crew_input", {})
    
    logger.info("Executing crew", crew=target_crew)
    
    # For Phase 3: Mock crew execution
    # In production, this would call CrewAdapter.execute_crew()
    mock_output = {
        "crew": target_crew,
        "result": f"Mock result from {target_crew} crew",
        "status": "completed"
    }
    
    logger.info("Crew execution complete", crew=target_crew)
    
    return {
        "partial_results": {target_crew: mock_output},
        "history": [{
            "step_number": state["control"]["current_step"],
            "step_type": StepType.CREW_EXECUTION,
            "node_name": "crew_execution",
            "input_data": crew_input,
            "output_data": mock_output,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 1000,
            "model_used": f"{target_crew}_crew"
        }]
    }
