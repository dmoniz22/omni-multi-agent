"""Task management endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from omni.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class TaskCreate(BaseModel):
    """Request model for creating a task."""

    task: str = Field(..., description="Task description")
    session_id: Optional[str] = Field(default=None, description="Optional session ID")
    parameters: dict = Field(default_factory=dict, description="Additional parameters")


class TaskResponse(BaseModel):
    """Response model for task."""

    task_id: str
    session_id: str
    status: str
    result: Optional[dict] = None


@router.post("", response_model=TaskResponse)
async def create_task(task_create: TaskCreate) -> TaskResponse:
    """Create a new task.

    Args:
        task_create: Task creation request

    Returns:
        Task response with task ID
    """
    task_id = str(uuid.uuid4())
    session_id = task_create.session_id or str(uuid.uuid4())

    logger.info("Task created", task_id=task_id, session_id=session_id)

    return TaskResponse(
        task_id=task_id,
        session_id=session_id,
        status="pending",
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """Get task status.

    Args:
        task_id: Task ID

    Returns:
        Task response

    Raises:
        HTTPException: If task not found
    """
    return TaskResponse(
        task_id=task_id,
        session_id="mock-session",
        status="completed",
        result={"output": "Task result placeholder"},
    )


@router.delete("/{task_id}")
async def delete_task(task_id: str) -> dict:
    """Delete a task.

    Args:
        task_id: Task ID

    Returns:
        Deletion confirmation
    """
    logger.info("Task deleted", task_id=task_id)
    return {"deleted": True, "task_id": task_id}
