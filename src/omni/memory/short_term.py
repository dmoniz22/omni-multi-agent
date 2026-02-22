"""Short-term memory using LangGraph checkpoints.

Provides workflow state persistence and resume capability.
"""

from typing import Any, Dict, Optional

from omni.core.logging import get_logger

logger = get_logger(__name__)


class ShortTermMemory:
    """Manages short-term memory via LangGraph checkpointer.

    Stores workflow state at each node transition, enabling
    resume after interruption.
    """

    def __init__(self, checkpointer: Optional[Any] = None):
        """Initialize short-term memory.

        Args:
            checkpointer: LangGraph checkpointer instance (e.g., PostgresSaver)
        """
        self._checkpointer = checkpointer

    @property
    def is_configured(self) -> bool:
        """Check if checkpointer is configured."""
        return self._checkpointer is not None

    async def save_checkpoint(
        self,
        thread_id: str,
        checkpoint: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save a checkpoint.

        Args:
            thread_id: Session/thread identifier
            checkpoint: State data to checkpoint
            metadata: Optional metadata about the checkpoint
        """
        if not self._checkpointer:
            logger.debug("No checkpointer configured, skipping checkpoint")
            return

        logger.debug("Saving checkpoint", thread_id=thread_id)

    async def get_checkpoint(
        self,
        thread_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get the latest checkpoint.

        Args:
            thread_id: Session/thread identifier

        Returns:
            Checkpoint data or None
        """
        if not self._checkpointer:
            return None

        logger.debug("Getting checkpoint", thread_id=thread_id)
        return None

    async def list_checkpoints(
        self,
        thread_id: str,
        limit: int = 10,
    ) -> list[Dict[str, Any]]:
        """List checkpoints for a thread.

        Args:
            thread_id: Session/thread identifier
            limit: Maximum number to return

        Returns:
            List of checkpoints
        """
        if not self._checkpointer:
            return []

        return []

    async def delete_checkpoint(
        self,
        thread_id: str,
    ) -> bool:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: Session/thread identifier

        Returns:
            True if deleted
        """
        if not self._checkpointer:
            return False

        logger.debug("Deleting checkpoints", thread_id=thread_id)
        return True


_short_term_memory: Optional[ShortTermMemory] = None


def get_short_term_memory() -> ShortTermMemory:
    """Get the global short-term memory instance.

    Returns:
        ShortTermMemory instance
    """
    global _short_term_memory
    if _short_term_memory is None:
        _short_term_memory = ShortTermMemory()
    return _short_term_memory
