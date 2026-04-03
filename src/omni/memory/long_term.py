"""Long-term memory using PostgreSQL with pgvector.

Provides comprehensive memory storage and retrieval across sessions.
Delegates to repository classes to avoid code duplication.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from omni.core.logging import get_logger
from omni.db.engine import get_session
from omni.db.repositories.memory import MemoryRepository
from omni.db.repositories.session import SessionRepository
from omni.db.repositories.task import TaskRepository, TaskStepRepository
from omni.db.models import Session as DBSession, Task, TaskStep, MemoryVector

logger = get_logger(__name__)


class MemoryEntry(BaseModel):
    """A stored memory entry."""

    id: str | None = Field(default=None, description="Memory ID")
    session_id: str = Field(..., description="Session ID")
    content: str = Field(..., description="Memory content")
    memory_type: str = Field(default="task", description="Type: task, insight, context")
    embedding: list[float] | None = Field(default=None, description="Vector embedding")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    relevance_score: float | None = Field(default=None, description="Similarity score")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation time"
    )


class TaskEntry(BaseModel):
    """A stored task entry."""

    id: str | None = Field(default=None, description="Task ID")
    session_id: str = Field(..., description="Session ID")
    original_task: str = Field(..., description="Original task description")
    status: str = Field(default="pending", description="Task status")
    final_response: dict | None = Field(default=None, description="Final response")
    execution_summary: dict | None = Field(
        default=None, description="Execution summary"
    )
    total_steps: int = Field(default=0, description="Total steps executed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = Field(default=None)


class LongTermMemory:
    """Manages long-term memory via PostgreSQL.

    Stores task summaries, insights, and context for retrieval
    in future sessions. Delegates to repository classes.
    """

    def __init__(
        self,
        vector_dimension: int = 768,
        top_k: int = 5,
    ):
        """Initialize long-term memory."""
        self._vector_dimension = vector_dimension
        self._top_k = top_k
        self._db_available = True

    @property
    def is_configured(self) -> bool:
        """Check if vector database is configured."""
        return self._db_available

    async def add_memory(
        self,
        session_id: str,
        content: str,
        memory_type: str = "task",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a memory entry."""
        try:
            async with get_session() as session:
                repo = MemoryRepository(session)
                memory = await repo.store(
                    session_id=UUID(session_id),
                    content=content,
                    embedding=[],  # LongTermMemory doesn't generate embeddings
                    memory_type=memory_type,
                    metadata=metadata,
                )
                logger.debug("Added memory", session_id=session_id, type=memory_type)
                return str(memory.id)
        except Exception as e:
            logger.error("Failed to add memory", error=str(e))
            return ""

    async def search_memories(
        self,
        query: str,
        session_id: str | None = None,
        memory_type: str | None = None,
        top_k: int | None = None,
    ) -> list[MemoryEntry]:
        """Search memories by text similarity (simple contains search)."""
        try:
            async with get_session() as session:
                repo = MemoryRepository(session)
                memories = await repo.list_by_session(
                    session_id=UUID(session_id) if session_id else None,
                    memory_type=memory_type,
                    limit=top_k or self._top_k,
                )
                query_lower = query.lower()
                results = []
                for mem in memories:
                    if query_lower in mem.content.lower():
                        results.append(
                            MemoryEntry(
                                id=str(mem.id),
                                session_id=str(mem.session_id),
                                content=mem.content,
                                memory_type=mem.memory_type,
                                metadata=mem.metadata_json or {},
                                created_at=mem.created_at,
                                relevance_score=1.0,
                            )
                        )
                return results
        except Exception as e:
            logger.error("Failed to search memories", error=str(e))
            return []

    async def get_session_memories(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        """Get all memories for a session."""
        try:
            async with get_session() as session:
                repo = MemoryRepository(session)
                memories = await repo.list_by_session(
                    session_id=UUID(session_id),
                    limit=limit,
                )
                return [
                    MemoryEntry(
                        id=str(mem.id),
                        session_id=str(mem.session_id),
                        content=mem.content,
                        memory_type=mem.memory_type,
                        metadata=mem.metadata_json or {},
                        created_at=mem.created_at,
                    )
                    for mem in memories
                ]
        except Exception as e:
            logger.error("Failed to get session memories", error=str(e))
            return []

    async def delete_session_memories(self, session_id: str) -> int:
        """Delete all memories for a session."""
        try:
            async with get_session() as session:
                repo = MemoryRepository(session)
                count = await repo.delete_by_session(UUID(session_id))
                logger.debug(
                    "Deleted session memories", session_id=session_id, count=count
                )
                return count
        except Exception as e:
            logger.error("Failed to delete session memories", error=str(e))
            return 0

    async def cleanup_old_memories(self, days: int = 30) -> int:
        """Clean up memories older than specified days."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            async with get_session() as session:
                repo = MemoryRepository(session)
                count = await repo.delete_older_than(cutoff)
                logger.info(
                    "Cleaned up old memories",
                    days=days,
                    cutoff=cutoff.isoformat(),
                    deleted=count,
                )
                return count
        except Exception as e:
            logger.error("Failed to cleanup old memories", error=str(e))
            return 0

    # ========== Task Persistence Methods (delegate to repositories) ==========

    async def save_task(
        self,
        session_id: str,
        task_id: str,
        original_task: str,
        status: str = "pending",
    ) -> str:
        """Save a task to the database."""
        try:
            async with get_session() as session:
                session_repo = SessionRepository(session)
                task_repo = TaskRepository(session)

                # Ensure session exists
                db_session = await session_repo.get(UUID(session_id))
                if not db_session:
                    db_session = DBSession(id=UUID(session_id))
                    session.add(db_session)
                    await session.flush()

                task = Task(
                    id=UUID(task_id),
                    session_id=UUID(session_id),
                    original_task=original_task,
                    status=status,
                )
                session.add(task)
                await session.flush()

                logger.info("Task saved", task_id=task_id, session_id=session_id)
                return str(task.id)
        except Exception as e:
            logger.error("Failed to save task", error=str(e))
            return ""

    async def update_task(
        self,
        task_id: str,
        status: str | None = None,
        final_response: dict | None = None,
        execution_summary: dict | None = None,
    ) -> bool:
        """Update a task."""
        try:
            async with get_session() as session:
                repo = TaskRepository(session)
                task = await repo.update(
                    UUID(task_id),
                    status=status,
                    final_response=final_response,
                    execution_summary=execution_summary,
                )
                if task is None:
                    logger.warning("Task not found", task_id=task_id)
                    return False
                logger.info("Task updated", task_id=task_id, status=status)
                return True
        except Exception as e:
            logger.error("Failed to update task", error=str(e))
            return False

    async def get_task(self, task_id: str) -> TaskEntry | None:
        """Get a task by ID."""
        try:
            async with get_session() as session:
                repo = TaskRepository(session)
                task = await repo.get(UUID(task_id))
                if not task:
                    return None
                return TaskEntry(
                    id=str(task.id),
                    session_id=str(task.session_id),
                    original_task=task.original_task,
                    status=task.status,
                    final_response=task.final_response,
                    execution_summary=task.execution_summary,
                    total_steps=task.total_steps,
                    created_at=task.created_at,
                    completed_at=task.completed_at,
                )
        except Exception as e:
            logger.error("Failed to get task", error=str(e))
            return None

    async def get_session_tasks(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[TaskEntry]:
        """Get all tasks for a session."""
        try:
            async with get_session() as session:
                repo = TaskRepository(session)
                tasks = await repo.list_by_session(UUID(session_id))
                return [
                    TaskEntry(
                        id=str(t.id),
                        session_id=str(t.session_id),
                        original_task=t.original_task,
                        status=t.status,
                        final_response=t.final_response,
                        execution_summary=t.execution_summary,
                        total_steps=t.total_steps,
                        created_at=t.created_at,
                        completed_at=t.completed_at,
                    )
                    for t in tasks[:limit]
                ]
        except Exception as e:
            logger.error("Failed to get session tasks", error=str(e))
            return []

    async def save_task_step(
        self,
        task_id: str,
        step_number: int,
        step_type: str,
        node_name: str,
        input_data: dict | None = None,
        output_data: dict | None = None,
        error: str | None = None,
    ) -> str:
        """Save a task step."""
        try:
            async with get_session() as session:
                repo = TaskStepRepository(session)
                step = await repo.create(
                    task_id=UUID(task_id),
                    step_number=step_number,
                    step_type=step_type,
                    node_name=node_name,
                    input_data=input_data,
                    output_data=output_data,
                    error=error,
                )
                return str(step.id)
        except Exception as e:
            logger.error("Failed to save task step", error=str(e))
            return ""

    async def get_task_steps(self, task_id: str) -> list[dict[str, Any]]:
        """Get all steps for a task."""
        try:
            async with get_session() as session:
                repo = TaskStepRepository(session)
                steps = await repo.list_by_task(UUID(task_id))
                return [
                    {
                        "step_number": s.step_number,
                        "step_type": s.step_type,
                        "node_name": s.node_name,
                        "input_data": s.input_data,
                        "output_data": s.output_data,
                        "error": s.error,
                        "created_at": s.created_at.isoformat()
                        if s.created_at
                        else None,
                    }
                    for s in steps
                ]
        except Exception as e:
            logger.error("Failed to get task steps", error=str(e))
            return []


_long_term_memory: LongTermMemory | None = None


def get_long_term_memory() -> LongTermMemory:
    """Get the global long-term memory instance."""
    global _long_term_memory
    if _long_term_memory is None:
        _long_term_memory = LongTermMemory()
    return _long_term_memory
