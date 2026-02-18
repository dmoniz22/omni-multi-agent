"""Validation node for the LangGraph workflow.

Validates crew output against expected schema.
"""
from datetime import datetime

from omni.core.state import OmniState, StepType
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.nodes.validation")


async def validation(state: OmniState) -> dict:
    """Validate crew output.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict with updates to state
    """
    logger.info("Validating crew output")
    
    # For Phase 3: Mock validation (always passes)
    # In production, this would call PydanticAI validator
    
    return {
        "history": [{
            "step_number": state["control"]["current_step"],
            "step_type": StepType.VALIDATION,
            "node_name": "validation",
            "input_data": {"partial_results": list(state.get("partial_results", {}).keys())},
            "output_data": {"valid": True},
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 100
        }]
    }
