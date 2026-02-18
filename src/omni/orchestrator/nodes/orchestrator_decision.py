"""Orchestrator decision node for the LangGraph workflow.

Makes the high-level decision about next action.
"""
import json
from datetime import datetime

from omni.core.state import OmniState, StepType, OrchestratorDecision, Action
from omni.core.models import get_model
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.nodes.orchestrator_decision")


SYSTEM_PROMPT = """You are the OMNI Orchestrator - an AI that coordinates multi-agent workflows.

Your role is to analyze the current task state and decide the next action.

AVAILABLE ACTIONS:
- "delegate": Send a subtask to a department crew
- "ask_human": Request human input for a decision
- "complete": The task is finished, collate and return results
- "error": Report an unrecoverable error

AVAILABLE DEPARTMENTS:
- github: GitHub operations, repository analysis, code review
- research: Web research, content analysis, fact-checking  
- social: Social media content creation and optimization
- analysis: Data analysis, pattern recognition, insights
- writing: Long-form writing, editing, documentation
- coding: Code generation, refactoring, architecture

RULES:
1. Choose the most appropriate department for each subtask
2. Do not delegate to a department that has already been called unless the task requires iteration
3. If you have all needed partial results, choose "complete"
4. If a destructive action is needed, choose "ask_human" first
5. If confidence is below 0.5, choose "ask_human" for guidance
6. You MUST respond with valid JSON matching the schema below

RESPONSE SCHEMA:
{
  "action": "delegate" | "ask_human" | "complete" | "error",
  "target_crew": "<crew_name or null>",
  "crew_input": { <structured input for the crew, or null> },
  "reasoning": "<brief explanation of your decision>",
  "confidence": <float 0.0-1.0>
}"""


async def orchestrator_decision(state: OmniState) -> dict:
    """Make orchestration decision.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict with updates to state (current_decision)
    """
    logger.info("Making orchestration decision", task_id=state["task_id"])
    
    # Check step limits
    current_step = state["control"]["current_step"]
    max_steps = state["control"]["max_steps"]
    
    if current_step >= max_steps:
        logger.warning("Max steps reached, forcing completion")
        decision = OrchestratorDecision(
            action=Action.COMPLETE,
            reasoning="Maximum step limit reached",
            confidence=1.0
        )
        return {
            "current_decision": decision.model_dump(),
            "control": {**state["control"], "current_step": current_step + 1},
            "history": [{
                "step_number": current_step,
                "step_type": StepType.ORCHESTRATOR_DECISION,
                "node_name": "orchestrator_decision",
                "input_data": {"max_steps_reached": True},
                "output_data": decision.model_dump(),
                "timestamp": datetime.utcnow().isoformat(),
                "duration_ms": 0,
                "model_used": "qwen3:14b"
            }]
        }
    
    # For Phase 3 testing: use mock decision
    # In production, this would call the LLM
    query_analysis = state.get("query_analysis", {})
    required_departments = query_analysis.get("required_departments", ["research"])
    partial_results = state.get("partial_results", {})
    
    # Simple logic: if we have results from all required departments, complete
    # Otherwise, delegate to the first missing department
    missing_departments = [
        dept for dept in required_departments 
        if dept not in partial_results
    ]
    
    if missing_departments:
        target_crew = missing_departments[0]
        
        # Format crew_input based on the target crew
        if target_crew == "research":
            crew_input = {
                "query": state["original_task"],
                "depth": "standard",
                "sources_required": 5
            }
        else:
            # Generic input for other crews
            crew_input = {
                "task": state["original_task"],
                "context": state.get("current_objective", "")
            }
        
        decision = OrchestratorDecision(
            action=Action.DELEGATE,
            target_crew=target_crew,
            crew_input=crew_input,
            reasoning=f"Delegating to {target_crew} department",
            confidence=0.8
        )
    else:
        decision = OrchestratorDecision(
            action=Action.COMPLETE,
            reasoning="All required departments have provided results",
            confidence=0.9
        )
    
    logger.info(
        "Orchestration decision made",
        action=decision.action.value,
        target_crew=decision.target_crew
    )
    
    return {
        "current_decision": decision.model_dump(),
        "control": {**state["control"], "current_step": current_step + 1},
        "history": [{
            "step_number": current_step,
            "step_type": StepType.ORCHESTRATOR_DECISION,
            "node_name": "orchestrator_decision",
            "input_data": {"step": current_step, "max_steps": max_steps},
            "output_data": decision.model_dump(),
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 0,
            "model_used": "qwen3:14b"
        }]
    }
