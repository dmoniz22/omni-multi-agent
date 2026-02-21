"""Analysis Department Agents.

Implements specialized agents for data analysis.
"""

from typing import List

from crewai import Agent


class AnalysisAgents:
    """Factory for Analysis department agents."""

    def create_data_analyst(self) -> Agent:
        return Agent(
            role="Data Analyst",
            goal="Analyze data and identify patterns",
            backstory="""You are an expert data analyst skilled in:
            - Statistical analysis and pattern recognition
            - Data visualization recommendations
            - Trend identification
            - Metric calculation""",
            verbose=True,
            allow_delegation=False,
        )

    def create_insight_generator(self) -> Agent:
        return Agent(
            role="Insight Generator",
            goal="Generate actionable insights from data",
            backstory="""You excel at:
            - Identifying trends and patterns
            - Generating actionable recommendations
            - Connecting data to business outcomes""",
            verbose=True,
            allow_delegation=False,
        )

    def create_report_creator(self) -> Agent:
        return Agent(
            role="Report Creator",
            goal="Create comprehensive analysis reports",
            backstory="""You specialize in:
            - Structuring analysis reports
            - Creating visualizations
            - Presenting findings clearly""",
            verbose=True,
            allow_delegation=False,
        )

    def create_all(self) -> List[Agent]:
        return [
            self.create_data_analyst(),
            self.create_insight_generator(),
            self.create_report_creator(),
        ]
