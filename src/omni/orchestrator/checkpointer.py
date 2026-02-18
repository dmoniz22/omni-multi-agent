"""PostgreSQL checkpointer configuration for LangGraph.

Sets up PostgresSaver for workflow state persistence.
"""
from langgraph.checkpoint.postgres import PostgresSaver
from omni.core.config import get_settings
from omni.core.logging import get_logger

logger = get_logger("omni.orchestrator.checkpointer")

# Global checkpointer instance
_checkpointer: PostgresSaver | None = None


def get_checkpointer() -> PostgresSaver:
    """Get or create the PostgreSQL checkpointer.
    
    Returns:
        PostgresSaver: Configured checkpointer instance
    """
    global _checkpointer
    
    if _checkpointer is None:
        settings = get_settings()
        
        # Convert asyncpg URL to psycopg format for LangGraph
        # postgresql+asyncpg:// -> postgresql://
        db_url = settings.database.url.replace("postgresql+asyncpg://", "postgresql://")
        
        _checkpointer = PostgresSaver.from_conn_string(db_url)
        logger.info("PostgreSQL checkpointer initialized")
    
    return _checkpointer


def setup_checkpointer():
    """Setup the checkpointer tables.
    
    Should be called once during application startup.
    """
    checkpointer = get_checkpointer()
    # The checkpointer will create tables automatically on first use
    logger.info("Checkpointer setup complete")
