"""Task and TaskStep repository for database operations."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omni.db.models import Task, TaskStep
from omni.core.exceptions import RepositoryError
from omni.core.logging import get_db_logger

logger = get_db_logger()


class TaskRepository:
    """Repository for task CRUD operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        session_id: UUID,
        original_task: str,
    ) -> Task:
        """Create a new task.
        
        Args:
            session_id: Session UUID
            original_task: The original task description
            
        Returns:
            Task: The created task
        """
        try:
            task = Task(
                session_id=session_id,
                original_task=original_task,
                status="pending",
                total_steps=0,
            )
            self.session.add(task)
            await self.session.flush()
            await self.session.refresh(task)
            
            logger.info("Task created", task_id=str(task.id), session_id=str(session_id))
            return task
            
        except Exception as e:
            logger.error("Failed to create task", error=str(e))
            raise RepositoryError(f"Failed to create task: {e}")
    
    async def get(self, task_id: UUID) -> Optional[Task]:
        """Get a task by ID.
        
        Args:
            task_id: Task UUID
            
        Returns:
            Optional[Task]: The task if found
        """
        try:
            result = await self.session.execute(
                select(Task).where(Task.id == task_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get task", task_id=str(task_id), error=str(e))
            raise RepositoryError(f"Failed to get task: {e}")
    
    async def update(
        self,
        task_id: UUID,
        status: Optional[str] = None,
        final_response: Optional[dict] = None,
        execution_summary: Optional[dict] = None,
    ) -> Optional[Task]:
        """Update a task.
        
        Args:
            task_id: Task UUID
            status: Updated status
            final_response: Final response data
            execution_summary: Execution summary
            
        Returns:
            Optional[Task]: The updated task
        """
        try:
            task = await self.get(task_id)
            if task is None:
                return None
            
            if status is not None:
                task.status = status
            if final_response is not None:
                task.final_response = final_response
            if execution_summary is not None:
                task.execution_summary = execution_summary
            
            if status == "completed":
                task.completed_at = datetime.utcnow()
            
            await self.session.flush()
            await self.session.refresh(task)
            
            logger.info("Task updated", task_id=str(task_id), status=status)
            return task
            
        except Exception as e:
            logger.error("Failed to update task", task_id=str(task_id), error=str(e))
            raise RepositoryError(f"Failed to update task: {e}")
    
    async def list_by_session(self, session_id: UUID) -> List[Task]:
        """List all tasks for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List[Task]: List of tasks
        """
        try:
            result = await self.session.execute(
                select(Task)
                .where(Task.session_id == session_id)
                .order_by(Task.created_at.desc())
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error("Failed to list tasks", session_id=str(session_id), error=str(e))
            raise RepositoryError(f"Failed to list tasks: {e}")


class TaskStepRepository:
    """Repository for task step CRUD operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        task_id: UUID,
        step_number: int,
        step_type: str,
        node_name: str,
        input_data: Optional[dict] = None,
        output_data: Optional[dict] = None,
        model_used: Optional[str] = None,
        duration_ms: int = 0,
        error: Optional[str] = None,
    ) -> TaskStep:
        """Create a new task step.
        
        Args:
            task_id: Task UUID
            step_number: Step number in sequence
            step_type: Type of step
            node_name: Name of the node
            input_data: Input data
            output_data: Output data
            model_used: Model used
            duration_ms: Duration in milliseconds
            error: Error message if any
            
        Returns:
            TaskStep: The created step
        """
        try:
            step = TaskStep(
                task_id=task_id,
                step_number=step_number,
                step_type=step_type,
                node_name=node_name,
                input_data=input_data,
                output_data=output_data,
                model_used=model_used,
                duration_ms=duration_ms,
                error=error,
            )
            self.session.add(step)
            await self.session.flush()
            await self.session.refresh(step)
            
            # Update task step count
            task_result = await self.session.execute(
                select(Task).where(Task.id == task_id)
            )
            task = task_result.scalar_one_or_none()
            if task:
                task.total_steps = max(task.total_steps, step_number)
            
            logger.info("Task step created", task_id=str(task_id), step_number=step_number)
            return step
            
        except Exception as e:
            logger.error("Failed to create task step", error=str(e))
            raise RepositoryError(f"Failed to create task step: {e}")
    
    async def get(self, step_id: UUID) -> Optional[TaskStep]:
        """Get a step by ID.
        
        Args:
            step_id: Step UUID
            
        Returns:
            Optional[TaskStep]: The step if found
        """
        try:
            result = await self.session.execute(
                select(TaskStep).where(TaskStep.id == step_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get task step", step_id=str(step_id), error=str(e))
            raise RepositoryError(f"Failed to get task step: {e}")
    
    async def list_by_task(self, task_id: UUID) -> List[TaskStep]:
        """List all steps for a task.
        
        Args:
            task_id: Task UUID
            
        Returns:
            List[TaskStep]: List of steps ordered by step_number
        """
        try:
            result = await self.session.execute(
                select(TaskStep)
                .where(TaskStep.task_id == task_id)
                .order_by(TaskStep.step_number)
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error("Failed to list task steps", task_id=str(task_id), error=str(e))
            raise RepositoryError(f"Failed to list task steps: {e}")
