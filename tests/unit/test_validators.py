"""Unit tests for validation schemas."""

import pytest
from pydantic import ValidationError

from omni.validators.schemas.common import ValidatedResult, StepRecord
from omni.validators.schemas.crew_inputs import (
    AnalysisTaskInput,
    CodingTaskInput,
    GitHubTaskInput,
    ResearchTaskInput,
    SocialTaskInput,
    WritingTaskInput,
)
from omni.validators.schemas.crew_outputs import (
    AnalysisReport,
    CodingOutput,
    GitHubOutput,
    ResearchReport,
    SocialContentOutput,
    WritingOutput,
)
from omni.validators.schemas.responses import FinalResponse, Source


class TestValidatedResult:
    """Tests for ValidatedResult schema."""

    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidatedResult(
            valid=True,
            data={"key": "value"},
            schema_name="TestSchema",
        )
        assert result.valid is True
        assert result.data == {"key": "value"}
        assert result.schema_name == "TestSchema"
        assert result.errors == []
        assert result.corrections is None

    def test_invalid_result(self):
        """Test invalid validation result."""
        result = ValidatedResult(
            valid=False,
            data=None,
            errors=["Error 1", "Error 2"],
            schema_name="TestSchema",
        )
        assert result.valid is False
        assert result.data is None
        assert result.errors == ["Error 1", "Error 2"]

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ValidatedResult(
            valid=True,
            data={"key": "value"},
            schema_name="TestSchema",
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["valid"] is True


class TestStepRecord:
    """Tests for StepRecord schema."""

    def test_basic_creation(self):
        """Test basic step record creation."""
        record = StepRecord(
            step_type="test_step",
            input={"data": "test"},
            output={"result": "success"},
            timestamp="2024-01-01T00:00:00",
            duration_ms=100,
            success=True,
        )
        assert record.step_type == "test_step"
        assert record.success is True

    def test_with_error(self):
        """Test step record with error."""
        record = StepRecord(
            step_type="failed_step",
            input={"data": "test"},
            timestamp="2024-01-01T00:00:00",
            success=False,
            error="Something went wrong",
        )
        assert record.success is False
        assert record.error == "Something went wrong"


class TestCrewInputSchemas:
    """Tests for crew input schemas."""

    def test_github_task_input(self):
        """Test GitHubTaskInput schema."""
        data = {
            "query": "Search for Python repos",
            "repository": "octocat/Hello-World",
            "operation": "search_repos",
        }
        input_obj = GitHubTaskInput(**data)
        assert input_obj.query == "Search for Python repos"
        assert input_obj.repository == "octocat/Hello-World"

    def test_research_task_input(self):
        """Test ResearchTaskInput schema."""
        data = {
            "query": "AI trends",
            "depth": "comprehensive",
            "sources_required": 5,
        }
        input_obj = ResearchTaskInput(**data)
        assert input_obj.query == "AI trends"
        assert input_obj.depth == "comprehensive"
        assert input_obj.sources_required == 5

    def test_social_task_input(self):
        """Test SocialTaskInput schema."""
        data = {
            "topic": "New product launch",
            "platforms": ["twitter", "linkedin"],
            "tone": "professional",
        }
        input_obj = SocialTaskInput(**data)
        assert input_obj.topic == "New product launch"
        assert input_obj.platforms == ["twitter", "linkedin"]

    def test_analysis_task_input(self):
        """Test AnalysisTaskInput schema."""
        data = {
            "subject": "Sales data",
            "analysis_type": "data",
            "focus": ["trends", "outliers"],
        }
        input_obj = AnalysisTaskInput(**data)
        assert input_obj.subject == "Sales data"
        assert input_obj.analysis_type == "data"

    def test_writing_task_input(self):
        """Test WritingTaskInput schema."""
        data = {
            "topic": "Python tips",
            "content_type": "blog_post",
            "style": "technical",
            "length": "medium",
        }
        input_obj = WritingTaskInput(**data)
        assert input_obj.topic == "Python tips"
        assert input_obj.content_type == "blog_post"

    def test_coding_task_input(self):
        """Test CodingTaskInput schema."""
        data = {
            "task": "Create a REST API",
            "language": "Python",
            "framework": "FastAPI",
            "test_code": True,
        }
        input_obj = CodingTaskInput(**data)
        assert input_obj.task == "Create a REST API"
        assert input_obj.language == "Python"
        assert input_obj.test_code is True


class TestCrewOutputSchemas:
    """Tests for crew output schemas."""

    def test_github_output(self):
        """Test GitHubOutput schema."""
        data = {
            "success": True,
            "operation": "search_repos",
            "result": [{"name": "repo1", "stars": 100}],
        }
        output = GitHubOutput(**data)
        assert output.success is True
        assert output.operation == "search_repos"

    def test_research_report(self):
        """Test ResearchReport schema."""
        data = {
            "summary": "AI summary",
            "findings": ["Finding 1", "Finding 2"],
            "sources": [{"title": "Source 1", "url": "https://example.com"}],
            "depth": "medium",
        }
        report = ResearchReport(**data)
        assert report.summary == "AI summary"
        assert len(report.findings) == 2

    def test_social_content_output(self):
        """Test SocialContentOutput schema."""
        data = {
            "contents": {
                "twitter": "Tweet content",
                "linkedin": "LinkedIn post",
            },
            "hashtags": ["#ai", "#tech"],
            "tone": "professional",
        }
        output = SocialContentOutput(**data)
        assert "twitter" in output.contents

    def test_analysis_report(self):
        """Test AnalysisReport schema."""
        data = {
            "summary": "Analysis summary",
            "findings": ["Finding 1"],
            "metrics": {"total": 100, "average": 50},
            "recommendations": ["Rec 1"],
        }
        report = AnalysisReport(**data)
        assert report.summary == "Analysis summary"

    def test_writing_output(self):
        """Test WritingOutput schema."""
        data = {
            "title": "My Blog Post",
            "content": "Blog content here",
            "content_type": "blog_post",
            "word_count": 500,
            "style": "technical",
        }
        output = WritingOutput(**data)
        assert output.title == "My Blog Post"
        assert output.word_count == 500

    def test_coding_output(self):
        """Test CodingOutput schema."""
        data = {
            "success": True,
            "code": "print('hello')",
            "language": "Python",
            "explanation": "Simple print",
            "files_created": ["main.py"],
        }
        output = CodingOutput(**data)
        assert output.success is True
        assert output.language == "Python"


class TestFinalResponse:
    """Tests for FinalResponse schema."""

    def test_final_response(self):
        """Test FinalResponse schema."""
        data = {
            "content": "The final answer",
            "sources": [
                {
                    "title": "Source 1",
                    "url": "https://example.com",
                    "department": "research",
                }
            ],
            "departments_used": ["research", "writing"],
            "execution_summary": {"steps": 3},
        }
        response = FinalResponse(**data)
        assert response.content == "The final answer"
        assert len(response.departments_used) == 2

    def test_final_response_minimal(self):
        """Test FinalResponse with minimal data."""
        response = FinalResponse(
            content="Simple answer",
        )
        assert response.content == "Simple answer"
        assert response.sources == []
        assert response.departments_used == []
