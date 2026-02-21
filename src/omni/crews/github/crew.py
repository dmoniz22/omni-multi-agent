"""GitHub Department Crew.

Implements the GitHubCrew for repository analysis, code review, and gist creation.
"""

from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from omni.core.logging import get_logger
from omni.crews.base import BaseCrew
from omni.crews.github.agents import GitHubAgents

logger = get_logger(__name__)


class GitHubTaskInput(BaseModel):
    """Input schema for GitHub crew tasks."""

    query: str = Field(..., description="The GitHub-related task or query")
    repository: Optional[str] = Field(
        default=None, description="Specific repository (owner/repo)"
    )
    scope: str = Field(default="all", description="Scope: repos, users, issues, or all")


class CodeSnippet(BaseModel):
    """Code snippet from analysis."""

    filename: str = Field(..., description="Filename or path")
    code: str = Field(..., description="The code snippet")
    language: str = Field(default="unknown", description="Programming language")


class GitHubOutput(BaseModel):
    """Output schema for GitHub crew results."""

    success: bool = Field(default=True, description="Whether the operation succeeded")
    analysis: str = Field(default="", description="Summary of the analysis")
    code_snippets: List[CodeSnippet] = Field(
        default_factory=list, description="Code snippets found"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations"
    )
    gist_urls: List[str] = Field(default_factory=list, description="Gist URLs created")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class GitHubCrew(BaseCrew):
    """GitHub department crew for repository analysis and operations.

    This crew uses a hierarchical process with three specialized agents:
    1. GitHub Researcher: Repository search and metadata
    2. Code Analyst: Code review and pattern analysis
    3. Gist Creator: Code snippet management

    Usage:
        crew = GitHubCrew()
        result = crew.execute({
            "query": "Find popular Python ML projects",
            "repository": "owner/repo",
            "scope": "repos"
        })
    """

    name = "github"
    description = (
        "Analyzes GitHub repositories, performs code reviews, and creates gists"
    )
    input_schema = GitHubTaskInput
    output_schema = GitHubOutput

    def __init__(self):
        """Initialize the GitHub crew."""
        super().__init__()
        self.agents_factory = GitHubAgents()
        self._agents: Optional[List[Agent]] = None

    def get_agents(self) -> List[Agent]:
        """Get all GitHub department agents."""
        if self._agents is None:
            self._agents = self.agents_factory.create_all()
        return self._agents

    def build_crew(self) -> Crew:
        """Build and configure the GitHub crew."""
        agents = self.get_agents()
        researcher, analyst, gist_creator = agents

        # Task 1: Repository Research
        research_task = Task(
            description="""Research GitHub based on the following task: {query}
            
            Repository: {repository}
            Scope: {scope}
            
            Your task is to:
            1. Search for relevant repositories, users, or issues
            2. Gather metadata about the target (if specified)
            3. Identify trending projects related to the query
            4. Compile a list of relevant repositories with details
            
            Provide comprehensive information about each repository found.""",
            expected_output="""A detailed research report containing:
            - List of relevant repositories with descriptions
            - Repository metadata (stars, forks, language)
            - URLs to the repositories
            - Any trending or notable projects found""",
            agent=researcher,
        )

        # Task 2: Code Analysis
        analysis_task = Task(
            description="""Analyze the research findings and identify key patterns.
            
            Review the research results and:
            1. Identify common patterns in the repositories
            2. Note the most popular languages and frameworks
            3. Extract any interesting code patterns or solutions
            4. Provide recommendations based on the analysis
            
            Focus on actionable insights and best practices found.""",
            expected_output="""An analysis report containing:
            - Key patterns identified
            - Language and framework distribution
            - Notable code solutions found
            - Recommendations for further exploration""",
            agent=analyst,
            context=[research_task],
        )

        # Task 3: Gist Creation (optional)
        gist_task = Task(
            description="""Create useful code snippets from the analysis.
            
            Based on the research and analysis:
            1. Identify useful code examples or snippets
            2. Format them appropriately for sharing
            3. Create gists with proper descriptions
            4. Ensure code is properly syntax-highlighted
            
            Note: Gist creation is optional - only create if useful snippets were found.""",
            expected_output="""A list of gist URLs created, or a note that no gists were created.""",
            agent=gist_creator,
            context=[analysis_task],
        )

        # Build the crew with hierarchical process
        crew = Crew(
            agents=agents,
            tasks=[research_task, analysis_task, gist_task],
            process=Process.hierarchical,
            verbose=True,
        )

        logger.debug("GitHub crew built successfully")
        return crew

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the GitHub crew with the given input."""
        validated_input = self.input_schema.model_validate(input_data)

        logger.info(
            "Starting GitHub task",
            query=validated_input.query,
            repository=validated_input.repository,
        )

        result = super().execute(validated_input.model_dump())

        try:
            output = self.output_schema.model_validate(result)
            logger.info("GitHub task completed", success=output.success)
            return output.model_dump()
        except Exception as e:
            logger.warning("Could not parse result, returning raw")
            return {
                "success": True,
                "analysis": str(result),
                "code_snippets": [],
                "recommendations": [],
                "gist_urls": [],
            }
