"""Session management endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from omni.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SessionCreate(BaseModel):
    """Request model for creating a session."""

    user_id: Optional[str] = Field(default=None, description="Optional user ID")
    metadata: dict = Field(default_factory=dict, description="Session metadata")


class SessionResponse(BaseModel):
    """Response model for session."""

    session_id: str
    user_id: Optional[str]
    status: str


@router.post("", response_model=SessionResponse)
async def create_session(session_create: SessionCreate) -> SessionResponse:
    """Create a new session.

    Args:
        session_create: Session creation request

    Returns:
        Session response with session ID
    """
    session_id = str(uuid.uuid4())

    logger.info("Session created", session_id=session_id)

    return SessionResponse(
        session_id=session_id,
        user_id=session_create.user_id,
        status="active",
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """Get session details.

    Args:
        session_id: Session ID

    Returns:
        Session response
    """
    return SessionResponse(
        session_id=session_id,
        user_id=None,
        status="active",
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a session.

    Args:
        session_id: Session ID

    Returns:
        Deletion confirmation
    """
    logger.info("Session deleted", session_id=session_id)
    return {"deleted": True, "session_id": session_id}
