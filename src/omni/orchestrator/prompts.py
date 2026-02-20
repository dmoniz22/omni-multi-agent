"""Orchestrator prompts for OMNI.

Provides system and user prompts for the orchestrator LLM.
"""

import json
from typing import Any, Dict, List


def get_departments_json(crews: List[Dict[str, Any]]) -> str:
    """Build departments JSON from crew registry.

    Args:
        crews: List of crew info from registry

    Returns:
        JSON string of department info
    """
    departments = []
    for crew in crews:
        departments.append(
            {
                "name": crew.get("name", ""),
                "description": crew.get("description", ""),
            }
        )
    return json.dumps(departments, indent=2)


def build_system_prompt(departments_json: str) -> str:
    """Build the system prompt for orchestrator.

    Args:
        departments_json: JSON string of available departments

    Returns:
        System prompt string
    """
    return f"""You are the OMNI Orchestrator — an AI that coordinates multi-agent workflows.

Your role is to analyze the current task state and decide the next action.

AVAILABLE ACTIONS:
- "delegate": Send a subtask to a department crew
- "ask_human": Request human input for a decision
- "complete": The task is finished, collate and return results
- "error": Report an unrecoverable error

AVAILABLE DEPARTMENTS:
{departments_json}

RULES:
1. Choose the most appropriate department for each subtask
2. Do not delegate to a department that has already been called unless the task requires iteration
3. If you have all needed partial results, choose "complete"
4. If a destructive action is needed (code execution, file writes, API mutations), choose "ask_human" first
5. If confidence is below 0.5, choose "ask_human" for guidance
6. You MUST respond with valid JSON matching the schema below

RESPONSE SCHEMA:
{{
  "action": "delegate" | "ask_human" | "complete" | "error",
  "target_crew": "<crew_name or null>",
  "crew_input": {{ <structured input for the crew, or null> }},
  "reasoning": "<brief explanation of your decision>",
  "confidence": <float 0.0-1.0>
}}"""


def build_user_prompt(
    original_task: str,
    current_objective: str,
    current_step: int,
    max_steps: int,
    formatted_partial_results: str,
    last_3_steps_summary: str,
    recent_context_messages: str,
) -> str:
    """Build the user prompt for orchestrator.

    Args:
        original_task: The original user task
        current_objective: Current objective being worked on
        current_step: Current step number
        max_steps: Maximum allowed steps
        formatted_partial_results: Formatted string of completed work
        last_3_steps_summary: Summary of last 3 steps
        recent_context_messages: Recent context messages

    Returns:
        User prompt string
    """
    return f"""TASK: {original_task}
CURRENT OBJECTIVE: {current_objective}
STEP: {current_step} / {max_steps}

COMPLETED WORK:
{formatted_partial_results}

RECENT HISTORY:
{last_3_steps_summary}

CONTEXT:
{recent_context_messages}

What is the next action?"""


def format_partial_results(partial_results: Dict[str, Any]) -> str:
    """Format partial results for the prompt.

    Args:
        partial_results: Dict of crew results

    Returns:
        Formatted string
    """
    if not partial_results:
        return "(No completed work yet)"

    lines = []
    for crew_name, result in partial_results.items():
        if isinstance(result, dict):
            summary = result.get("summary", str(result))[:200]
            lines.append(f"- {crew_name}: {summary}")
        else:
            lines.append(f"- {crew_name}: {str(result)[:200]}")

    return "\n".join(lines)


def format_history(history: List[Dict[str, Any]]) -> str:
    """Format recent history for the prompt.

    Args:
        history: Execution history

    Returns:
        Formatted string
    """
    if not history:
        return "(No history yet)"

    recent = history[-3:] if len(history) > 3 else history
    lines = []

    for step in recent:
        step_type = step.get("step_type", "unknown")
        node = step.get("node_name", "unknown")
        output = step.get("output_data", {})
        action = output.get("action", "N/A") if isinstance(output, dict) else "N/A"
        lines.append(
            f"- Step {step.get('step_number', '?')}: {step_type} ({node}) -> {action}"
        )

    return "\n".join(lines)
