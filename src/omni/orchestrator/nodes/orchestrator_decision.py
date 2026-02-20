"""Orchestrator decision node for the LangGraph workflow.

Makes the high-level decision about next action using LLM.
"""

import json
import time
from datetime import datetime

from omni.core.state import OmniState, StepType, OrchestratorDecision, Action
from omni.core.models import get_model
from omni.core.logging import get_logger
from omni.registry import get_crew_registry
from omni.orchestrator.prompts import (
    build_system_prompt,
    build_user_prompt,
    format_partial_results,
    format_history,
    get_departments_json,
)

logger = get_logger("omni.orchestrator.nodes.orchestrator_decision")


async def orchestrator_decision(state: OmniState) -> dict:
    """Make orchestration decision using LLM.

    Args:
        state: Current workflow state

    Returns:
        Dict with updates to state (current_decision)
    """
    logger.info("Making orchestration decision", task_id=state["task_id"])

    start_time = time.time()

    # Check step limits
    current_step = state["control"]["current_step"]
    max_steps = state["control"]["max_steps"]

    if current_step >= max_steps:
        logger.warning("Max steps reached, forcing completion")
        decision = OrchestratorDecision(
            action=Action.COMPLETE,
            reasoning="Maximum step limit reached",
            confidence=1.0,
        )
        return {
            "current_decision": decision.model_dump(),
            "control": {**state["control"], "current_step": current_step + 1},
            "history": [
                {
                    "step_number": current_step,
                    "step_type": StepType.ORCHESTRATOR_DECISION,
                    "node_name": "orchestrator_decision",
                    "input_data": {"max_steps_reached": True},
                    "output_data": decision.model_dump(),
                    "timestamp": datetime.utcnow().isoformat(),
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "model_used": "qwen3:14b",
                }
            ],
        }

    # Get available crews from registry
    crew_registry = get_crew_registry()
    available_crews = crew_registry.list_available()
    departments_json = get_departments_json(available_crews)

    # Build prompts
    system_prompt = build_system_prompt(departments_json)

    # Extract context from state
    original_task = state.get("original_task", "")
    current_objective = state.get("current_objective", original_task)
    partial_results = state.get("partial_results", {})
    history = state.get("history", [])
    context_messages = state.get("context_messages", [])

    # Format context
    formatted_results = format_partial_results(partial_results)
    history_summary = format_history(history)
    context_str = (
        "\n".join(
            [
                f"{msg.get('role', 'user')}: {msg.get('content', '')[:100]}"
                for msg in context_messages[-5:]
            ]
        )
        if context_messages
        else "(No additional context)"
    )

    user_prompt = build_user_prompt(
        original_task=original_task,
        current_objective=current_objective,
        current_step=current_step,
        max_steps=max_steps,
        formatted_partial_results=formatted_results,
        last_3_steps_summary=history_summary,
        recent_context_messages=context_str,
    )

    # Call LLM
    try:
        model = get_model("qwen3:14b", temperature=0.3)

        response = model.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        # Parse JSON response
        response_text = response.content

        # Try to extract JSON from response
        try:
            # Try direct parse first
            decision_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                decision_data = json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in response")

        # Validate with Pydantic
        decision = OrchestratorDecision(**decision_data)

        logger.info(
            "Orchestration decision made via LLM",
            action=decision.action.value,
            target_crew=decision.target_crew,
            confidence=decision.confidence,
        )

    except Exception as e:
        logger.error("LLM decision failed, using fallback", error=str(e))

        # Fallback to simple logic
        query_analysis = state.get("query_analysis", {})
        required_departments = query_analysis.get("required_departments", ["research"])

        missing_departments = [
            dept for dept in required_departments if dept not in partial_results
        ]

        if missing_departments:
            target_crew = missing_departments[0]

            if target_crew == "research":
                crew_input = {
                    "query": state["original_task"],
                    "depth": "standard",
                    "sources_required": 5,
                }
            else:
                crew_input = {
                    "task": state["original_task"],
                    "context": state.get("current_objective", ""),
                }

            decision = OrchestratorDecision(
                action=Action.DELEGATE,
                target_crew=target_crew,
                crew_input=crew_input,
                reasoning=f"Fallback: Delegating to {target_crew}",
                confidence=0.5,
            )
        else:
            decision = OrchestratorDecision(
                action=Action.COMPLETE,
                reasoning="Fallback: All required departments have results",
                confidence=0.5,
            )

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "current_decision": decision.model_dump(),
        "control": {**state["control"], "current_step": current_step + 1},
        "history": [
            {
                "step_number": current_step,
                "step_type": StepType.ORCHESTRATOR_DECISION,
                "node_name": "orchestrator_decision",
                "input_data": {
                    "step": current_step,
                    "max_steps": max_steps,
                    "original_task": original_task[:100],
                },
                "output_data": decision.model_dump(),
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": duration_ms,
                "model_used": "qwen3:14b",
            }
        ],
    }
