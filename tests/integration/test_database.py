"""Integration tests for database operations."""
import pytest
from uuid import UUID

from omni.db.engine import get_session, health_check
from omni.db.repositories.session import SessionRepository
from omni.db.repositories.task import TaskRepository, TaskStepRepository


@pytest.mark.asyncio
async def test_database_health():
    """Test database connectivity."""
    is_healthy = await health_check()
    assert is_healthy is True


@pytest.mark.asyncio
async def test_session_crud():
    """Test session CRUD operations."""
    async with get_session() as db_session:
        repo = SessionRepository(db_session)
        
        # Create
        session = await repo.create(
            user_id="test_user",
            metadata={"test": True}
        )
        assert session.id is not None
        assert session.user_id == "test_user"
        assert session.status == "active"
        
        # Get
        retrieved = await repo.get(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id
        
        # Update
        updated = await repo.update(
            session.id,
            status="completed",
            metadata={"test": True, "updated": True}
        )
        assert updated is not None
        assert updated.status == "completed"
        
        # List by user
        sessions = await repo.get_by_user("test_user")
        assert len(sessions) >= 1
        
        print("Session CRUD test passed!")


@pytest.mark.asyncio
async def test_task_crud():
    """Test task CRUD operations."""
    async with get_session() as db_session:
        # Create a session first
        session_repo = SessionRepository(db_session)
        session = await session_repo.create(user_id="test_user")
        
        task_repo = TaskRepository(db_session)
        
        # Create task
        task = await task_repo.create(
            session_id=session.id,
            original_task="Test task"
        )
        assert task.id is not None
        assert task.session_id == session.id
        assert task.status == "pending"
        
        # Get
        retrieved = await task_repo.get(task.id)
        assert retrieved is not None
        assert retrieved.id == task.id
        
        # Update
        updated = await task_repo.update(
            task.id,
            status="completed",
            final_response={"result": "success"}
        )
        assert updated is not None
        assert updated.status == "completed"
        
        # List by session
        tasks = await task_repo.list_by_session(session.id)
        assert len(tasks) >= 1
        
        print("Task CRUD test passed!")


@pytest.mark.asyncio
async def test_task_step_crud():
    """Test task step CRUD operations."""
    async with get_session() as db_session:
        # Create session and task
        session_repo = SessionRepository(db_session)
        session = await session_repo.create(user_id="test_user")
        
        task_repo = TaskRepository(db_session)
        task = await task_repo.create(
            session_id=session.id,
            original_task="Test task"
        )
        
        step_repo = TaskStepRepository(db_session)
        
        # Create step
        step = await step_repo.create(
            task_id=task.id,
            step_number=1,
            step_type="query_analysis",
            node_name="query_analyzer",
            input_data={"query": "test"},
            output_data={"result": "analyzed"},
            model_used="qwen3:14b",
            duration_ms=1000
        )
        assert step.id is not None
        assert step.task_id == task.id
        assert step.step_number == 1
        
        # Get
        retrieved = await step_repo.get(step.id)
        assert retrieved is not None
        assert retrieved.id == step.id
        
        # List by task
        steps = await step_repo.list_by_task(task.id)
        assert len(steps) >= 1
        
        print("TaskStep CRUD test passed!")


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test a complete workflow."""
    async with get_session() as db_session:
        # Create session
        session_repo = SessionRepository(db_session)
        session = await session_repo.create(
            user_id="test_user",
            metadata={"workflow": "test"}
        )
        
        # Create task
        task_repo = TaskRepository(db_session)
        task = await task_repo.create(
            session_id=session.id,
            original_task="Research AI trends"
        )
        
        # Add steps
        step_repo = TaskStepRepository(db_session)
        await step_repo.create(
            task_id=task.id,
            step_number=1,
            step_type="query_analysis",
            node_name="query_analyzer",
            input_data={"task": "Research AI trends"},
            output_data={"intent": "research", "departments": ["research"]},
            duration_ms=500
        )
        
        await step_repo.create(
            task_id=task.id,
            step_number=2,
            step_type="crew_execution",
            node_name="crew_execution",
            input_data={"crew": "research", "query": "AI trends"},
            output_data={"result": "Found 5 trends"},
            model_used="gemma3:12b",
            duration_ms=5000
        )
        
        # Complete task
        await task_repo.update(
            task.id,
            status="completed",
            final_response={"trends": ["Trend 1", "Trend 2"]},
            execution_summary={"steps": 2, "duration_ms": 5500}
        )
        
        # Verify
        steps = await step_repo.list_by_task(task.id)
        assert len(steps) == 2
        
        completed_task = await task_repo.get(task.id)
        assert completed_task.status == "completed"
        
        print("End-to-end workflow test passed!")
