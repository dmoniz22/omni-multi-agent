"""Unit tests for omni.core.state module."""
import pytest
from datetime import datetime

from omni.core.state import (
    Status,
    Role,
    Complexity,
    WorkflowPattern,
    StepType,
    Action,
    StepRecord,
    ContextMessage,
    QueryAnalysis,
    OrchestratorDecision,
    CrewInfo,
    SkillInfo,
    ControlFlags,
    HITLState,
    ErrorState,
    create_initial_state,
    state_to_pydantic,
)


class TestEnums:
    """Test suite for state enums."""
    
    def test_status_enum(self):
        """Test Status enum values."""
        assert Status.PENDING == "pending"
        assert Status.RUNNING == "running"
        assert Status.WAITING_HUMAN == "waiting_human"
        assert Status.COMPLETED == "completed"
        assert Status.FAILED == "failed"
    
    def test_role_enum(self):
        """Test Role enum values."""
        assert Role.SYSTEM == "system"
        assert Role.USER == "user"
        assert Role.ASSISTANT == "assistant"
    
    def test_complexity_enum(self):
        """Test Complexity enum values."""
        assert Complexity.SIMPLE == "simple"
        assert Complexity.MODERATE == "moderate"
        assert Complexity.COMPLEX == "complex"
    
    def test_workflow_pattern_enum(self):
        """Test WorkflowPattern enum values."""
        assert WorkflowPattern.SINGLE_CREW == "single_crew"
        assert WorkflowPattern.SEQUENTIAL == "sequential"
        assert WorkflowPattern.PARALLEL == "parallel"
        assert WorkflowPattern.ITERATIVE == "iterative"
    
    def test_step_type_enum(self):
        """Test StepType enum values."""
        assert StepType.QUERY_ANALYSIS == "query_analysis"
        assert StepType.ORCHESTRATOR_DECISION == "orchestrator_decision"
        assert StepType.CREW_EXECUTION == "crew_execution"
        assert StepType.VALIDATION == "validation"
        assert StepType.HUMAN_INPUT == "human_input"
        assert StepType.ERROR == "error"
        assert StepType.RESPONSE_COLLATION == "response_collation"
    
    def test_action_enum(self):
        """Test Action enum values."""
        assert Action.DELEGATE == "delegate"
        assert Action.ASK_HUMAN == "ask_human"
        assert Action.COMPLETE == "complete"
        assert Action.ERROR == "error"


class TestStepRecord:
    """Test suite for StepRecord model."""
    
    def test_basic_creation(self):
        """Test basic StepRecord creation."""
        record = StepRecord(
            step_number=1,
            step_type=StepType.QUERY_ANALYSIS,
            node_name="query_analyzer"
        )
        assert record.step_number == 1
        assert record.step_type == StepType.QUERY_ANALYSIS
        assert record.node_name == "query_analyzer"
        assert record.timestamp is not None
    
    def test_with_optional_fields(self):
        """Test StepRecord with all optional fields."""
        record = StepRecord(
            step_number=1,
            step_type=StepType.CREW_EXECUTION,
            node_name="crew_execution",
            input_data={"query": "test"},
            output_data={"result": "success"},
            duration_ms=1000,
            model_used="qwen3:14b",
            metadata={"key": "value"}
        )
        assert record.input_data == {"query": "test"}
        assert record.output_data == {"result": "success"}
        assert record.duration_ms == 1000
        assert record.model_used == "qwen3:14b"
        assert record.metadata == {"key": "value"}
    
    def test_with_error(self):
        """Test StepRecord with error."""
        record = StepRecord(
            step_number=2,
            step_type=StepType.ERROR,
            node_name="exception_handler",
            error="Something went wrong"
        )
        assert record.error == "Something went wrong"


class TestQueryAnalysis:
    """Test suite for QueryAnalysis model."""
    
    def test_basic_creation(self):
        """Test basic QueryAnalysis creation."""
        analysis = QueryAnalysis(
            intent="research",
            required_departments=["research"],
            complexity=Complexity.SIMPLE,
            workflow_pattern=WorkflowPattern.SINGLE_CREW
        )
        assert analysis.intent == "research"
        assert analysis.required_departments == ["research"]
        assert analysis.complexity == Complexity.SIMPLE
        assert analysis.workflow_pattern == WorkflowPattern.SINGLE_CREW
    
    def test_with_parameters(self):
        """Test QueryAnalysis with parameters."""
        analysis = QueryAnalysis(
            intent="coding",
            required_departments=["coding", "github"],
            complexity=Complexity.COMPLEX,
            workflow_pattern=WorkflowPattern.SEQUENTIAL,
            parameters={"language": "python", "framework": "fastapi"}
        )
        assert analysis.parameters == {"language": "python", "framework": "fastapi"}


class TestOrchestratorDecision:
    """Test suite for OrchestratorDecision model."""
    
    def test_delegate_action(self):
        """Test delegation decision."""
        decision = OrchestratorDecision(
            action=Action.DELEGATE,
            target_crew="research",
            crew_input={"query": "AI trends"},
            reasoning="User wants research",
            confidence=0.9
        )
        assert decision.action == Action.DELEGATE
        assert decision.target_crew == "research"
        assert decision.confidence == 0.9
    
    def test_complete_action(self):
        """Test completion decision."""
        decision = OrchestratorDecision(
            action=Action.COMPLETE,
            reasoning="Task is finished",
            confidence=1.0
        )
        assert decision.action == Action.COMPLETE
        assert decision.target_crew is None
    
    def test_confidence_bounds(self):
        """Test confidence field bounds."""
        # Valid values
        OrchestratorDecision(action=Action.COMPLETE, reasoning="test", confidence=0.0)
        OrchestratorDecision(action=Action.COMPLETE, reasoning="test", confidence=0.5)
        OrchestratorDecision(action=Action.COMPLETE, reasoning="test", confidence=1.0)
        
        # Invalid values should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            OrchestratorDecision(action=Action.COMPLETE, reasoning="test", confidence=-0.1)
        
        with pytest.raises(Exception):
            OrchestratorDecision(action=Action.COMPLETE, reasoning="test", confidence=1.1)


class TestInitialState:
    """Test suite for create_initial_state function."""
    
    def test_state_creation(self, sample_task_id, sample_session_id, sample_task):
        """Test initial state creation."""
        state = create_initial_state(sample_task_id, sample_session_id, sample_task)
        
        assert state["task_id"] == sample_task_id
        assert state["session_id"] == sample_session_id
        assert state["original_task"] == sample_task
        assert state["current_objective"] == sample_task
        assert state["status"] == "pending"
        assert state["history"] == []
        assert state["partial_results"] == {}
        assert state["context"] == []
        assert state["query_analysis"] is None
        assert state["current_decision"] is None
        assert state["available_crews"] == []
        assert state["available_skills"] == []
        assert state["human_in_the_loop"] is None
        assert state["error_state"] is None
        assert state["final_response"] is None
    
    def test_control_flags(self, sample_task_id, sample_session_id, sample_task):
        """Test control flags in initial state."""
        state = create_initial_state(sample_task_id, sample_session_id, sample_task)
        
        control = state["control"]
        assert control["max_steps"] == 20
        assert control["current_step"] == 0
        assert control["is_complete"] is False
        assert control["timeout_seconds"] == 300
        assert "started_at" in control


class TestStateConversion:
    """Test suite for state_to_pydantic function."""
    
    def test_empty_state_conversion(self, sample_task_id, sample_session_id, sample_task):
        """Test conversion of empty state."""
        state = create_initial_state(sample_task_id, sample_session_id, sample_task)
        result = state_to_pydantic(state)
        
        assert result["query_analysis"] is None
        assert result["current_decision"] is None
        assert result["control"] is not None
    
    def test_state_with_analysis(self, sample_task_id, sample_session_id, sample_task):
        """Test conversion with query analysis."""
        state = create_initial_state(sample_task_id, sample_session_id, sample_task)
        state["query_analysis"] = {
            "intent": "research",
            "required_departments": ["research"],
            "complexity": "simple",
            "workflow_pattern": "single_crew"
        }
        
        result = state_to_pydantic(state)
        assert isinstance(result["query_analysis"], QueryAnalysis)
        assert result["query_analysis"].intent == "research"
    
    def test_state_with_decision(self, sample_task_id, sample_session_id, sample_task):
        """Test conversion with decision."""
        state = create_initial_state(sample_task_id, sample_session_id, sample_task)
        state["current_decision"] = {
            "action": "delegate",
            "target_crew": "research",
            "crew_input": {"query": "test"},
            "reasoning": "Test reasoning",
            "confidence": 0.8
        }
        
        result = state_to_pydantic(state)
        assert isinstance(result["current_decision"], OrchestratorDecision)
        assert result["current_decision"].action == Action.DELEGATE


class TestModels:
    """Test suite for other Pydantic models."""
    
    def test_crew_info(self):
        """Test CrewInfo model."""
        crew = CrewInfo(
            name="research",
            description="Research department",
            input_schema_name="ResearchTaskInput",
            output_schema_name="ResearchReport"
        )
        assert crew.name == "research"
        assert crew.description == "Research department"
    
    def test_skill_info(self):
        """Test SkillInfo model."""
        skill = SkillInfo(
            name="browser",
            description="Web browsing skill",
            enabled=True
        )
        assert skill.name == "browser"
        assert skill.enabled is True
    
    def test_control_flags(self):
        """Test ControlFlags model."""
        flags = ControlFlags(max_steps=30, current_step=5)
        assert flags.max_steps == 30
        assert flags.current_step == 5
        assert flags.is_complete is False
    
    def test_hitl_state(self):
        """Test HITLState model."""
        hitl = HITLState(
            pending=True,
            prompt="Please confirm",
            options=["yes", "no"]
        )
        assert hitl.pending is True
        assert hitl.prompt == "Please confirm"
        assert hitl.options == ["yes", "no"]
    
    def test_error_state(self):
        """Test ErrorState model."""
        error = ErrorState(
            error_type="ValidationError",
            error_message="Invalid input",
            retry_count=1,
            max_retries=3
        )
        assert error.error_type == "ValidationError"
        assert error.retry_count == 1
