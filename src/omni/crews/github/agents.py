"""GitHub Department Agents.

Implements specialized agents for GitHub operations.
"""

from typing import List

from crewai import Agent

from omni.core.logging import get_logger

logger = get_logger(__name__)


class GitHubAgents:
    """Factory for GitHub department agents."""

    def __init__(self):
        """Initialize GitHub agents factory."""
        self._agents: List[Agent] = []

    def create_github_researcher(self) -> Agent:
        """Create the GitHub Researcher agent.

        Returns:
            Agent for repository search and analysis
        """
        return Agent(
            role="GitHub Researcher",
            goal="Find and analyze GitHub repositories, trending projects, and user profiles",
            backstory="""You are an expert at finding and analyzing GitHub repositories.
            
            Your strengths include:
            - Searching for repositories by topic, language, or keyword
            - Identifying trending and popular projects
            - Analyzing repository metadata (stars, forks, issues)
            - Finding user profiles and their contributions
            
            You provide detailed information about repositories including:
            - Description, topics, and languages
            - Community activity and health metrics
            - Recent commits and releases
            - Contributor information""",
            verbose=True,
            allow_delegation=False,
        )

    def create_code_analyst(self) -> Agent:
        """Create the Code Analyst agent.

        Returns:
            Agent for code review and pattern recognition
        """
        return Agent(
            role="Code Analyst",
            goal="Perform code reviews, recognize patterns, and analyze dependencies",
            backstory="""You are an expert code analyst with deep knowledge of:
            
            - Multiple programming languages and frameworks
            - Code quality assessment
            - Design patterns and anti-patterns
            - Dependency analysis
            - Security vulnerability identification
            
            You analyze code by:
            - Reviewing code structure and organization
            - Identifying potential bugs or issues
            - Assessing code quality and maintainability
            - Finding dependencies and their versions
            - Providing constructive feedback""",
            verbose=True,
            allow_delegation=False,
        )

    def create_gist_creator(self) -> Agent:
        """Create the Gist Creator agent.

        Returns:
            Agent for creating and managing gists
        """
        return Agent(
            role="Gist Creator",
            goal="Create and manage code snippets through GitHub Gists",
            backstory="""You specialize in creating and sharing code snippets via GitHub Gists.
            
            You excel at:
            - Formatting code for different languages
            - Creating both public and secret gists
            - Organizing related snippets
            - Providing shareable links
            
            Your output includes properly formatted code snippets
            with appropriate syntax highlighting and language tags.""",
            verbose=True,
            allow_delegation=False,
        )

    def create_all(self) -> List[Agent]:
        """Create all GitHub department agents.

        Returns:
            List of agents in order: Researcher, Analyst, Gist Creator
        """
        if not self._agents:
            self._agents = [
                self.create_github_researcher(),
                self.create_code_analyst(),
                self.create_gist_creator(),
            ]
        return self._agents
