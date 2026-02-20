"""Context window management for OMNI.

Provides context building and truncation for the orchestrator.
"""

from typing import Any, Dict, List, Optional

from omni.core.logging import get_logger

logger = get_logger(__name__)


class ContextManager:
    """Manages context window for LLM calls.

    Handles priority-based truncation when context exceeds
    model limits.
    """

    DEFAULT_MAX_TOKENS = 8192
    TASK_TOKENS = 500
    OBJECTIVE_TOKENS = 300
    RESULTS_TOKENS = 2000
    HISTORY_TOKENS = 1000
    CONTEXT_TOKENS = 2000

    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        reserved_tokens: int = 2048,
    ):
        """Initialize context manager.

        Args:
            max_tokens: Maximum tokens in context window
            reserved_tokens: Tokens reserved for response
        """
        self.max_tokens = max_tokens
        self.reserved_tokens = reserved_tokens
        self.available_tokens = max_tokens - reserved_tokens

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Rough estimate: ~4 characters per token.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def build_context(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, str]:
        """Build context from state with truncation.

        Args:
            state: Current workflow state

        Returns:
            Dict with context sections
        """
        # Extract context sections
        original_task = state.get("original_task", "")
        current_objective = state.get("current_objective", "")
        partial_results = state.get("partial_results", {})
        history = state.get("history", [])

        # Build sections
        context = {
            "task": original_task[: self.TASK_TOKENS * 4],
            "objective": current_objective[: self.OBJECTIVE_TOKENS * 4]
            if current_objective
            else "",
            "results": self._format_results(partial_results),
            "history": self._format_history(history),
            "context_msgs": self._get_context_messages(state),
        }

        # Truncate if needed
        total_tokens = sum(self.estimate_tokens(v) for v in context.values())

        if total_tokens > self.available_tokens:
            context = self._truncate(context, total_tokens)

        return context

    def _format_results(self, partial_results: Dict[str, Any]) -> str:
        """Format partial results for context.

        Args:
            partial_results: Results from completed crews

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

        return "\n".join(lines)[: self.RESULTS_TOKENS * 4]

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """Format recent history for context.

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
            action = step.get("output_data", {}).get("action", "N/A")
            lines.append(
                f"- Step {step.get('step_number', '?')}: {step_type} ({node}) -> {action}"
            )

        return "\n".join(lines)[: self.HISTORY_TOKENS * 4]

    def _get_context_messages(self, state: Dict[str, Any]) -> str:
        """Get context messages from state.

        Args:
            state: Current state

        Returns:
            Context messages string
        """
        context_msgs = state.get("context_messages", [])

        if not context_msgs:
            return "(No additional context)"

        lines = []
        for msg in context_msgs[-5:]:  # Last 5 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")[:100]
            lines.append(f"{role}: {content}")

        return "\n".join(lines)[: self.CONTEXT_TOKENS * 4]

    def _truncate(
        self,
        context: Dict[str, str],
        total_tokens: int,
    ) -> Dict[str, str]:
        """Truncate context to fit available tokens.

        Truncates in order of priority: context_msgs first, then history,
        then results.

        Args:
            context: Current context dict
            total_tokens: Current total tokens

        Returns:
            Truncated context
        """
        # First, truncate context_msgs (lowest priority)
        context["context_msgs"] = context["context_msgs"][
            : len(context["context_msgs"]) // 2
        ]

        # Recalculate
        total_tokens = sum(self.estimate_tokens(v) for v in context.values())

        if total_tokens > self.available_tokens:
            # Truncate history
            context["history"] = context["history"][: len(context["history"]) // 2]

        total_tokens = sum(self.estimate_tokens(v) for v in context.values())

        if total_tokens > self.available_tokens:
            # Truncate results
            context["results"] = context["results"][: len(context["results"]) // 2]

        return context

    def build_user_prompt(
        self,
        state: Dict[str, Any],
    ) -> str:
        """Build the full user prompt for orchestrator.

        Args:
            state: Current workflow state

        Returns:
            Formatted user prompt
        """
        context = self.build_context(state)

        control = state.get("control", {})
        current_step = control.get("current_step", 0)
        max_steps = control.get("max_steps", 20)

        prompt = f"""TASK: {context["task"]}
CURRENT OBJECTIVE: {context["objective"]}
STEP: {current_step} / {max_steps}

COMPLETED WORK:
{context["results"]}

RECENT HISTORY:
{context["history"]}

CONTEXT:
{context["context_msgs"]}

What is the next action?"""

        return prompt


_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get the global context manager instance.

    Returns:
        ContextManager instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
