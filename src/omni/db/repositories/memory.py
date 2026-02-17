"""Memory vector repository for database operations."""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from omni.db.models import MemoryVector
from omni.core.exceptions import RepositoryError
from omni.core.logging import get_db_logger

logger = get_db_logger()


class MemoryRepository:
    """Repository for memory vector CRUD operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def store(
        self,
        session_id: UUID,
        content: str,
        embedding: List[float],
        memory_type: str = "general",
        metadata: Optional[dict] = None,
    ) -> MemoryVector:
        """Store a memory vector.
        
        Args:
            session_id: Session UUID
            content: Text content
            embedding: Vector embedding
            memory_type: Type of memory
            metadata: Optional metadata
            
        Returns:
            MemoryVector: The created memory vector
        """
        try:
            # Convert embedding list to string for pgvector
            embedding_str = f"[{','.join(str(x) for x in_embedding)}]"
            
            memory = MemoryVector(
                session_id=session_id,
                content=content,
                embedding=embedding_str,
                memory_type=memory_type,
                metadata_json=metadata,
            )
            self.session.add(memory)
            await self.session.flush()
            await self.session.refresh(memory)
            
            logger.info(
                "Memory stored",
                session_id=str(session_id),
                memory_id=str(memory.id),
                memory_type=memory_type,
            )
            return memory
            
        except Exception as e:
            logger.error("Failed to store memory", error=str(e))
            raise RepositoryError(f"Failed to store memory: {e}")
    
    async def get(self, memory_id: UUID) -> Optional[MemoryVector]:
        """Get a memory by ID.
        
        Args:
            memory_id: Memory UUID
            
        Returns:
            Optional[MemoryVector]: The memory if found
        """
        try:
            result = await self.session.execute(
                select(MemoryVector).where(MemoryVector.id == memory_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get memory", memory_id=str(memory_id), error=str(e))
            raise RepositoryError(f"Failed to get memory: {e}")
    
    async def search_similar(
        self,
        query_embedding: List[float],
        session_id: Optional[UUID] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        memory_type: Optional[str] = None,
    ) -> List[Tuple[MemoryVector, float]]:
        """Search for similar memories using cosine similarity.
        
        Args:
            query_embedding: The query vector
            session_id: Optional session filter
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            memory_type: Optional memory type filter
            
        Returns:
            List[Tuple[MemoryVector, float]]: List of (memory, score) tuples
        """
        try:
            # Convert query embedding to string
            embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"
            
            # Build query with cosine similarity
            query = text("""
                SELECT 
                    id,
                    session_id,
                    content,
                    embedding,
                    memory_type,
                    metadata_json,
                    created_at,
                    relevance_score,
                    1 - (embedding <=> :embedding) as similarity
                FROM memory_vectors
                WHERE 1 - (embedding <=> :embedding) >= :threshold
            """)
            
            params = {
                "embedding": embedding_str,
                "threshold": similarity_threshold,
            }
            
            if session_id is not None:
                query = text(query.text + " AND session_id = :session_id")
                params["session_id"] = str(session_id)
            
            if memory_type is not None:
                query = text(query.text + " AND memory_type = :memory_type")
                params["memory_type"] = memory_type
            
            query = text(query.text + " ORDER BY similarity DESC LIMIT :limit")
            params["limit"] = top_k
            
            result = await self.session.execute(query, params)
            rows = result.fetchall()
            
            memories = []
            for row in rows:
                memory = MemoryVector(
                    id=row.id,
                    session_id=row.session_id,
                    content=row.content,
                    embedding=row.embedding,
                    memory_type=row.memory_type,
                    metadata_json=row.metadata_json,
                    created_at=row.created_at,
                    relevance_score=row.relevance_score,
                )
                memories.append((memory, row.similarity))
            
            logger.info(
                "Memory search completed",
                results=len(memories),
                session_id=str(session_id) if session_id else None,
            )
            return memories
            
        except Exception as e:
            logger.error("Failed to search memories", error=str(e))
            raise RepositoryError(f"Failed to search memories: {e}")
    
    async def list_by_session(
        self,
        session_id: UUID,
        memory_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryVector]:
        """List memories for a session.
        
        Args:
            session_id: Session UUID
            memory_type: Optional type filter
            limit: Maximum results
            
        Returns:
            List[MemoryVector]: List of memories
        """
        try:
            query = select(MemoryVector).where(MemoryVector.session_id == session_id)
            
            if memory_type is not None:
                query = query.where(MemoryVector.memory_type == memory_type)
            
            query = query.order_by(MemoryVector.created_at.desc()).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(
                "Failed to list memories",
                session_id=str(session_id),
                error=str(e),
            )
            raise RepositoryError(f"Failed to list memories: {e}")
    
    async def delete(self, memory_id: UUID) -> bool:
        """Delete a memory.
        
        Args:
            memory_id: Memory UUID
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            memory = await self.get(memory_id)
            if memory is None:
                return False
            
            await self.session.delete(memory)
            await self.session.flush()
            
            logger.info("Memory deleted", memory_id=str(memory_id))
            return True
            
        except Exception as e:
            logger.error("Failed to delete memory", memory_id=str(memory_id), error=str(e))
            raise RepositoryError(f"Failed to delete memory: {e}")
    
    async def delete_by_session(self, session_id: UUID) -> int:
        """Delete all memories for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            int: Number of memories deleted
        """
        try:
            result = await self.session.execute(
                select(MemoryVector).where(MemoryVector.session_id == session_id)
            )
            memories = result.scalars().all()
            
            count = 0
            for memory in memories:
                await self.session.delete(memory)
                count += 1
            
            await self.session.flush()
            
            logger.info("Deleted session memories", session_id=str(session_id), count=count)
            return count
            
        except Exception as e:
            logger.error(
                "Failed to delete session memories",
                session_id=str(session_id),
                error=str(e),
            )
            raise RepositoryError(f"Failed to delete memories: {e}")
