"""Long-term memory using PostgreSQL with pgvector.

Provides comprehensive memory storage and retrieval across sessions.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from pydantic import BaseModel, Field

from omni.core.logging import get_logger
from omni.db.engine import get_session
from omni.db.models import Task, TaskStep, Session as DBSession, MemoryVector

logger = get_logger(__name__)


class MemoryEntry(BaseModel):
    """A stored memory entry."""

    id: Optional[str] = Field(default=None, description="Memory ID")
    session_id: str = Field(..., description="Session ID")
    content: str = Field(..., description="Memory content")
    memory_type: str = Field(default="task", description="Type: task, insight, context")
    embedding: Optional[List[float]] = Field(
        default=None, description="Vector embedding"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    relevance_score: Optional[float] = Field(
        default=None, description="Similarity score"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation time"
    )


class TaskEntry(BaseModel):
    """A stored task entry."""

    id: Optional[str] = Field(default=None, description="Task ID")
    session_id: str = Field(..., description="Session ID")
    original_task: str = Field(..., description="Original task description")
    status: str = Field(default="pending", description="Task status")
    final_response: Optional[Dict] = Field(default=None, description="Final response")
    execution_summary: Optional[Dict] = Field(
        default=None, description="Execution summary"
    )
    total_steps: int = Field(default=0, description="Total steps executed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)


class LongTermMemory:
    """Manages long-term memory via PostgreSQL.

    Stores task summaries, insights, and context for retrieval
    in future sessions.
    """

    def __init__(
        self,
        vector_dimension: int = 768,
        top_k: int = 5,
    ):
        """Initialize long-term memory."""
        self._vector_dimension = vector_dimension
        self._top_k = top_k
        self._db_available = True  # Assume available if we're using sync operations

    @property
    def is_configured(self) -> bool:
        """Check if vector database is configured."""
        return self._db_available

    async def add_memory(
        self,
        session_id: str,
        content: str,
        memory_type: str = "task",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a memory entry."""
        try:
            async with get_session() as session:
                memory = MemoryVector(
                    session_id=uuid.UUID(session_id),
                    content=content,
                    memory_type=memory_type,
                    metadata_json=metadata or {},
                )
                session.add(memory)
                await session.flush()
                await session.refresh(memory)

                logger.debug("Added memory", session_id=session_id, type=memory_type)
                return str(memory.id)
        except Exception as e:
            logger.error("Failed to add memory", error=str(e))
            return ""

    async def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[MemoryEntry]:
        """Search memories by text similarity (simple contains search)."""
        try:
            async with get_session() as session:
                from sqlalchemy import select, desc

                stmt = select(MemoryVector).order_by(desc(MemoryVector.created_at))

                if session_id:
                    stmt = stmt.where(MemoryVector.session_id == uuid.UUID(session_id))

                if memory_type:
                    stmt = stmt.where(MemoryVector.memory_type == memory_type)

                stmt = stmt.limit(top_k or self._top_k)

                result = await session.execute(stmt)
                memories = result.scalars().all()

                # Simple text search
                results = []
                query_lower = query.lower()
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
    ) -> List[MemoryEntry]:
        """Get all memories for a session."""
        try:
            async with get_session() as session:
                from sqlalchemy import select, desc

                stmt = (
                    select(MemoryVector)
                    .where(MemoryVector.session_id == uuid.UUID(session_id))
                    .order_by(desc(MemoryVector.created_at))
                    .limit(limit)
                )

                result = await session.execute(stmt)
                memories = result.scalars().all()

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

    async def delete_session_memories(
        self,
        session_id: str,
    ) -> int:
        """Delete all memories for a session."""
        try:
            async with get_session() as session:
                from sqlalchemy import delete

                stmt = delete(MemoryVector).where(
                    MemoryVector.session_id == uuid.UUID(session_id)
                )

                result = await session.execute(stmt)

                logger.debug("Deleted session memories", session_id=session_id)
                return result.rowcount
        except Exception as e:
            logger.error("Failed to delete session memories", error=str(e))
            return 0

    async def cleanup_old_memories(
        self,
        days: int = 30,
    ) -> int:
        """Clean up memories older than specified days."""
        # Not implemented - would need to track created_at for cleanup
        return 0

    # ========== Task Persistence Methods ==========

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
                # Check if session exists
                db_session = await session.get(DBSession, uuid.UUID(session_id))
                if not db_session:
                    # Create session if doesn't exist
                    db_session = DBSession(id=uuid.UUID(session_id))
                    session.add(db_session)
                    await session.flush()

                task = Task(
                    id=uuid.UUID(task_id),
                    session_id=uuid.UUID(session_id),
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
        status: Optional[str] = None,
        final_response: Optional[Dict] = None,
        execution_summary: Optional[Dict] = None,
    ) -> bool:
        """Update a task."""
        try:
            async with get_session() as session:
                task = await session.get(Task, uuid.UUID(task_id))
                if not task:
                    logger.warning("Task not found", task_id=task_id)
                    return False

                if status:
                    task.status = status
                    if status == "completed":
                        task.completed_at = datetime.utcnow()
                if final_response:
                    task.final_response = final_response
                if execution_summary:
                    task.execution_summary = execution_summary

                logger.info("Task updated", task_id=task_id, status=status)
                return True
        except Exception as e:
            logger.error("Failed to update task", error=str(e))
            return False

    async def get_task(
        self,
        task_id: str,
    ) -> Optional[TaskEntry]:
        """Get a task by ID."""
        try:
            async with get_session() as session:
                task = await session.get(Task, uuid.UUID(task_id))
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
    ) -> List[TaskEntry]:
        """Get all tasks for a session."""
        try:
            async with get_session() as session:
                from sqlalchemy import select, desc

                stmt = (
                    select(Task)
                    .where(Task.session_id == uuid.UUID(session_id))
                    .order_by(desc(Task.created_at))
                    .limit(limit)
                )

                result = await session.execute(stmt)
                tasks = result.scalars().all()

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
                    for t in tasks
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
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> str:
        """Save a task step."""
        try:
            async with get_session() as session:
                step = TaskStep(
                    task_id=uuid.UUID(task_id),
                    step_number=step_number,
                    step_type=step_type,
                    node_name=node_name,
                    input_data=input_data,
                    output_data=output_data,
                    error=error,
                )
                session.add(step)

                # Update task step count
                task = await session.get(Task, uuid.UUID(task_id))
                if task:
                    task.total_steps = max(task.total_steps, step_number)

                await session.flush()

                return str(step.id)
        except Exception as e:
            logger.error("Failed to save task step", error=str(e))
            return ""

    async def get_task_steps(
        self,
        task_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all steps for a task."""
        try:
            async with get_session() as session:
                from sqlalchemy import select

                stmt = (
                    select(TaskStep)
                    .where(TaskStep.task_id == uuid.UUID(task_id))
                    .order_by(TaskStep.step_number)
                )

                result = await session.execute(stmt)
                steps = result.scalars().all()

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


_long_term_memory: Optional[LongTermMemory] = None


def get_long_term_memory() -> LongTermMemory:
    """Get the global long-term memory instance."""
    global _long_term_memory
    if _long_term_memory is None:
        _long_term_memory = LongTermMemory()
    return _long_term_memory
