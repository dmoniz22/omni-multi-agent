"""Response collator node for the LangGraph workflow.

Synthesizes partial results into final response.
"""

import json
from datetime import datetime

from omni.core.state import OmniState, StepType
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.nodes.response_collator")


async def response_collator(state: OmniState) -> dict:
    """Collate partial results into final response.

    Args:
        state: Current workflow state

    Returns:
        Dict with updates to state
    """
    logger.info("Collating final response")

    partial_results = state.get("partial_results", {})

    # Simple collation: join all results
    response_parts = []
    for crew, result in partial_results.items():
        if isinstance(result, dict):
            # Handle different result formats
            if "summary" in result:
                # Research crew format
                response_parts.append(
                    f"**{crew.title()} Crew Result:**\n{result.get('summary', 'No summary')}"
                )
            elif "result" in result:
                response_parts.append(
                    f"**{crew.title()} Crew Result:**\n{result.get('result', 'N/A')}"
                )
            else:
                # Generic dict format
                response_parts.append(
                    f"**{crew.title()} Crew Result:**\n{json.dumps(result, indent=2)}"
                )
        else:
            response_parts.append(f"**{crew.title()} Crew Result:**\n{result}")

    final_response = "\n\n".join(response_parts)

    if not final_response:
        final_response = "Task completed successfully."

    logger.info("Response collation complete")

    return {
        "final_response": final_response,
        "status": "completed",
        "control": {**state["control"], "is_complete": True},
        "history": [
            {
                "step_number": state["control"]["current_step"],
                "step_type": StepType.RESPONSE_COLLATION,
                "node_name": "response_collator",
                "input_data": {"partial_results": list(partial_results.keys())},
                "output_data": {"final_response_length": len(final_response)},
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": 0,
            }
        ],
    }
