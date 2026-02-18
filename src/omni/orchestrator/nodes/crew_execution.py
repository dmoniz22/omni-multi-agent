"""Crew execution node for the LangGraph workflow.

Executes the crew with the given input.
"""
from datetime import datetime

from omni.core.state import OmniState, StepType
from omni.core.logging import get_logger
from omni.registry import get_crew_registry

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
    
    # Get the crew registry
    registry = get_crew_registry()
    
    # Check if crew is registered
    if not registry.is_registered(target_crew):
        logger.error("Crew not found in registry", crew=target_crew)
        error_output = {
            "crew": target_crew,
            "error": f"Crew '{target_crew}' not found in registry",
            "status": "failed"
        }
        return {
            "partial_results": {target_crew: error_output},
            "history": [{
                "step_number": state["control"]["current_step"],
                "step_type": StepType.CREW_EXECUTION,
                "node_name": "crew_execution",
                "input_data": crew_input,
                "output_data": error_output,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": 0,
                "model_used": f"{target_crew}_crew",
                "error": f"Crew '{target_crew}' not found"
            }]
        }
    
    # Execute the crew
    start_time = datetime.utcnow()
    try:
        # Execute via registry
        result = registry.execute(target_crew, crew_input)
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        output = {
            "crew": target_crew,
            "result": result,
            "status": "completed"
        }
        
        logger.info(
            "Crew execution complete",
            crew=target_crew,
            duration_ms=duration_ms
        )
        
        return {
            "partial_results": {target_crew: output},
            "history": [{
                "step_number": state["control"]["current_step"],
                "step_type": StepType.CREW_EXECUTION,
                "node_name": "crew_execution",
                "input_data": crew_input,
                "output_data": output,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": duration_ms,
                "model_used": f"{target_crew}_crew"
            }]
        }
        
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        logger.error(
            "Crew execution failed",
            crew=target_crew,
            error=str(e)
        )
        
        error_output = {
            "crew": target_crew,
            "error": str(e),
            "status": "failed"
        }
        
        return {
            "partial_results": {target_crew: error_output},
            "history": [{
                "step_number": state["control"]["current_step"],
                "step_type": StepType.CREW_EXECUTION,
                "node_name": "crew_execution",
                "input_data": crew_input,
                "output_data": error_output,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": duration_ms,
                "model_used": f"{target_crew}_crew",
                "error": str(e)
            }]
        }
