"""Validation schemas for OMNI."""

from omni.validators.schemas.common import StepRecord, ValidatedResult
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
from omni.validators.schemas.orchestrator import OrchestratorDecision, QueryAnalysis
from omni.validators.schemas.responses import FinalResponse, Source

__all__ = [
    "ValidatedResult",
    "StepRecord",
    "QueryAnalysis",
    "OrchestratorDecision",
    "GitHubTaskInput",
    "ResearchTaskInput",
    "SocialTaskInput",
    "AnalysisTaskInput",
    "WritingTaskInput",
    "CodingTaskInput",
    "GitHubOutput",
    "ResearchReport",
    "SocialContentOutput",
    "AnalysisReport",
    "WritingOutput",
    "CodingOutput",
    "FinalResponse",
    "Source",
]
