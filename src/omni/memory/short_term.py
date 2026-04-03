"""Short-term memory using LangGraph checkpoints.

Provides workflow state persistence and resume capability.
"""

from datetime import datetime, timezone
from typing import Any

from omni.core.logging import get_logger
from omni.orchestrator.checkpointer import get_checkpointer

logger = get_logger(__name__)


class ShortTermMemory:
    """Manages short-term memory via LangGraph checkpointer.

    Stores workflow state at each node transition, enabling
    resume after interruption.
    """

    def __init__(self, checkpointer: Any = None):
        """Initialize short-term memory.

        Args:
            checkpointer: LangGraph checkpointer instance (defaults to PostgresSaver)
        """
        self._checkpointer = checkpointer

    @property
    def is_configured(self) -> bool:
        """Check if checkpointer is configured."""
        return self._checkpointer is not None

    def _get_checkpointer(self) -> Any:
        """Get the checkpointer instance."""
        if self._checkpointer is not None:
            return self._checkpointer
        try:
            return get_checkpointer()
        except Exception as e:
            logger.warning("Could not initialize checkpointer", error=str(e))
            return None

    async def save_checkpoint(
        self,
        thread_id: str,
        checkpoint: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Save a checkpoint.

        Args:
            thread_id: Session/thread identifier
            checkpoint: State data to checkpoint
            metadata: Optional metadata about the checkpoint

        Returns:
            True if saved successfully
        """
        checkpointer = self._get_checkpointer()
        if not checkpointer:
            logger.debug("No checkpointer configured, skipping checkpoint save")
            return False

        try:
            import json

            # Serialize checkpoint to JSON for storage
            checkpoint_json = json.dumps(checkpoint)
            metadata_json = json.dumps(metadata) if metadata else None

            # Get next version for the thread
            version = checkpointer.get_next_version(thread_id, "messages")

            # Store using a simple JSON format
            checkpoint_data = {
                "checkpoint": checkpoint_json,
                "metadata": metadata_json,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }

            # Use the checkpointer's internal storage
            checkpointer.put(
                thread_id=thread_id,
                channel="checkpoint",
                version=version,
                checkpoint=checkpoint_data,
            )

            logger.debug("Checkpoint saved", thread_id=thread_id, version=version)
            return True
        except Exception as e:
            logger.error("Failed to save checkpoint", thread_id=thread_id, error=str(e))
            return False

    async def get_checkpoint(self, thread_id: str) -> dict[str, Any] | None:
        """Get the latest checkpoint.

        Args:
            thread_id: Session/thread identifier

        Returns:
            Checkpoint data or None
        """
        checkpointer = self._get_checkpointer()
        if not checkpointer:
            return None

        try:
            import json

            # List versions and get the latest
            versions = checkpointer.list_versions(thread_id, "checkpoint", limit=1)
            if not versions:
                return None

            latest = versions[0]
            checkpoint_data = checkpointer.get(thread_id, "checkpoint", latest)

            if checkpoint_data and isinstance(checkpoint_data, dict):
                checkpoint_json = checkpoint_data.get("checkpoint", "{}")
                return json.loads(checkpoint_json)

            return None
        except Exception as e:
            logger.error("Failed to get checkpoint", thread_id=thread_id, error=str(e))
            return None

    async def list_checkpoints(
        self,
        thread_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List checkpoints for a thread.

        Args:
            thread_id: Session/thread identifier
            limit: Maximum number to return

        Returns:
            List of checkpoint metadata
        """
        checkpointer = self._get_checkpointer()
        if not checkpointer:
            return []

        try:
            versions = checkpointer.list_versions(thread_id, "checkpoint", limit=limit)
            results = []
            for v in versions:
                checkpoint_data = checkpointer.get(thread_id, "checkpoint", v)
                if checkpoint_data and isinstance(checkpoint_data, dict):
                    results.append(
                        {
                            "version": v,
                            "saved_at": checkpoint_data.get("saved_at"),
                        }
                    )
            return results
        except Exception as e:
            logger.error(
                "Failed to list checkpoints", thread_id=thread_id, error=str(e)
            )
            return []

    async def delete_checkpoint(self, thread_id: str) -> bool:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: Session/thread identifier

        Returns:
            True if deleted
        """
        checkpointer = self._get_checkpointer()
        if not checkpointer:
            return False

        try:
            # Delete all versions by listing and clearing
            versions = checkpointer.list_versions(thread_id, "checkpoint", limit=-1)
            for v in versions:
                checkpointer.delete(thread_id, "checkpoint", v)
            logger.debug(
                "Checkpoints deleted", thread_id=thread_id, count=len(versions)
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to delete checkpoints", thread_id=thread_id, error=str(e)
            )
            return False


_short_term_memory: ShortTermMemory | None = None


def get_short_term_memory() -> ShortTermMemory:
    """Get the global short-term memory instance."""
    global _short_term_memory
    if _short_term_memory is None:
        _short_term_memory = ShortTermMemory()
    return _short_term_memory
