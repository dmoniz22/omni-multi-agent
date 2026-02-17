"""Session repository for database operations."""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omni.db.models import Session as SessionModel
from omni.core.exceptions import RepositoryError
from omni.core.logging import get_db_logger

logger = get_db_logger()


class SessionRepository:
    """Repository for session CRUD operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        expires_at: Optional[datetime] = None,
    ) -> SessionModel:
        """Create a new session.
        
        Args:
            user_id: Optional user identifier
            metadata: Optional session metadata
            expires_at: Optional expiration time
            
        Returns:
            SessionModel: The created session
        """
        try:
            session = SessionModel(
                user_id=user_id,
                metadata_json=metadata,
                expires_at=expires_at,
                status="active",
            )
            self.session.add(session)
            await self.session.flush()
            await self.session.refresh(session)
            
            logger.info("Session created", session_id=str(session.id))
            return session
            
        except Exception as e:
            logger.error("Failed to create session", error=str(e))
            raise RepositoryError(f"Failed to create session: {e}")
    
    async def get(self, session_id: UUID) -> Optional[SessionModel]:
        """Get a session by ID.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Optional[SessionModel]: The session if found
        """
        try:
            result = await self.session.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get session", session_id=str(session_id), error=str(e))
            raise RepositoryError(f"Failed to get session: {e}")
    
    async def get_by_user(self, user_id: str) -> List[SessionModel]:
        """Get all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List[SessionModel]: List of sessions
        """
        try:
            result = await self.session.execute(
                select(SessionModel)
                .where(SessionModel.user_id == user_id)
                .order_by(SessionModel.created_at.desc())
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error("Failed to get sessions by user", user_id=user_id, error=str(e))
            raise RepositoryError(f"Failed to get sessions: {e}")
    
    async def update(
        self,
        session_id: UUID,
        metadata: Optional[dict] = None,
        expires_at: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> Optional[SessionModel]:
        """Update a session.
        
        Args:
            session_id: Session UUID
            metadata: Updated metadata
            expires_at: Updated expiration
            status: Updated status
            
        Returns:
            Optional[SessionModel]: The updated session
        """
        try:
            session = await self.get(session_id)
            if session is None:
                return None
            
            if metadata is not None:
                session.metadata_json = metadata
            if expires_at is not None:
                session.expires_at = expires_at
            if status is not None:
                session.status = status
            
            session.updated_at = datetime.utcnow()
            await self.session.flush()
            await self.session.refresh(session)
            
            logger.info("Session updated", session_id=str(session_id))
            return session
            
        except Exception as e:
            logger.error("Failed to update session", session_id=str(session_id), error=str(e))
            raise RepositoryError(f"Failed to update session: {e}")
    
    async def delete(self, session_id: UUID) -> bool:
        """Delete a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            session = await self.get(session_id)
            if session is None:
                return False
            
            await self.session.delete(session)
            await self.session.flush()
            
            logger.info("Session deleted", session_id=str(session_id))
            return True
            
        except Exception as e:
            logger.error("Failed to delete session", session_id=str(session_id), error=str(e))
            raise RepositoryError(f"Failed to delete session: {e}")
    
    async def list_active(self, older_than_minutes: Optional[int] = None) -> List[SessionModel]:
        """List active sessions.
        
        Args:
            older_than_minutes: Filter sessions older than this many minutes
            
        Returns:
            List[SessionModel]: List of active sessions
        """
        try:
            query = select(SessionModel).where(SessionModel.status == "active")
            
            if older_than_minutes is not None:
                cutoff = datetime.utcnow() - timedelta(minutes=older_than_minutes)
                query = query.where(SessionModel.created_at < cutoff)
            
            query = query.order_by(SessionModel.created_at.desc())
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error("Failed to list active sessions", error=str(e))
            raise RepositoryError(f"Failed to list sessions: {e}")
    
    async def expire_old_sessions(self, max_age_minutes: int) -> int:
        """Mark old sessions as expired.
        
        Args:
            max_age_minutes: Maximum age in minutes
            
        Returns:
            int: Number of sessions expired
        """
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
            
            result = await self.session.execute(
                select(SessionModel)
                .where(SessionModel.status == "active")
                .where(SessionModel.created_at < cutoff)
            )
            sessions = result.scalars().all()
            
            count = 0
            for session in sessions:
                session.status = "expired"
                count += 1
            
            await self.session.flush()
            
            logger.info("Expired old sessions", count=count)
            return count
            
        except Exception as e:
            logger.error("Failed to expire old sessions", error=str(e))
            raise RepositoryError(f"Failed to expire sessions: {e}")
