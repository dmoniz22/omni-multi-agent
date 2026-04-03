"""PostgreSQL checkpointer configuration for LangGraph.

Sets up PostgresSaver for workflow state persistence.
"""

from urllib.parse import urlparse, urlunparse

from langgraph.checkpoint.postgres import PostgresSaver
from omni.core.config import get_settings
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.checkpointer")

# Global checkpointer instance
_checkpointer: PostgresSaver | None = None


def _get_sync_db_url() -> str:
    """Convert async database URL to sync URL for LangGraph checkpointer."""
    settings = get_settings()
    parsed = urlparse(settings.database.url)
    # Replace async driver with sync driver
    if parsed.scheme.startswith("postgresql+"):
        clean_url = urlunparse(parsed._replace(scheme="postgresql"))
    else:
        clean_url = settings.database.url
    return clean_url


def get_checkpointer() -> PostgresSaver:
    """Get or create the PostgreSQL checkpointer.

    Returns:
        PostgresSaver: Configured checkpointer instance
    """
    global _checkpointer

    if _checkpointer is None:
        db_url = _get_sync_db_url()
        _checkpointer = PostgresSaver.from_conn_string(db_url)
        logger.info("PostgreSQL checkpointer initialized")

    return _checkpointer


def setup_checkpointer():
    """Setup the checkpointer tables.

    Should be called once during application startup.
    """
    checkpointer = get_checkpointer()
    checkpointer.setup()
    logger.info("Checkpointer setup complete")
