"""Analysis Department Crew.

Implements the AnalysisCrew for data analysis and insights.
"""

from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from omni.core.logging import get_logger
from omni.crews.base import BaseCrew
from omni.crews.analysis.agents import AnalysisAgents

logger = get_logger(__name__)


class AnalysisTaskInput(BaseModel):
    subject: str
    analysis_type: str = "general"
    focus: List[str] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    summary: str = ""
    findings: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    visualizations: List[str] = Field(default_factory=list)
    data_summary: str = ""


class AnalysisCrew(BaseCrew):
    name = "analysis"
    description = "Analyzes data and generates insights"
    input_schema = AnalysisTaskInput
    output_schema = AnalysisReport

    def __init__(self):
        super().__init__()
        self.agents_factory = AnalysisAgents()
        self._agents: Optional[List[Agent]] = None

    def get_agents(self) -> List[Agent]:
        if self._agents is None:
            self._agents = self.agents_factory.create_all()
        return self._agents

    def build_crew(self) -> Crew:
        agents = self.get_agents()
        analyst, insights, reporter = agents

        analyze_task = Task(
            description="""Analyze: {subject}
            Type: {analysis_type}
            Focus: {focus}""",
            expected_output="Data analysis with metrics.",
            agent=analyst,
        )

        insights_task = Task(
            description="Generate insights from analysis.",
            expected_output="Key insights and recommendations.",
            agent=insights,
            context=[analyze_task],
        )

        report_task = Task(
            description="Create comprehensive report.",
            expected_output="Final analysis report.",
            agent=reporter,
            context=[insights_task],
        )

        return Crew(
            agents=agents,
            tasks=[analyze_task, insights_task, report_task],
            process=Process.sequential,
            verbose=True,
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.input_schema.model_validate(input_data)
        logger.info("Starting Analysis", subject=validated.subject)
        result = super().execute(validated.model_dump())

        try:
            output = self.output_schema.model_validate(result)
            return output.model_dump()
        except Exception:
            return {
                "summary": str(result),
                "findings": [],
                "insights": [],
                "recommendations": [],
                "visualizations": [],
            }
