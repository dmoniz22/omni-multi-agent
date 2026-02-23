"""Research Department Agents.

Defines the agents for the Research department that work together
to conduct web research, analyze content, and fact-check findings.

Agents:
    - Web Researcher: Gathers information from web sources
    - Content Analyzer: Summarizes and extracts key insights
    - Fact Checker: Verifies claims and cross-references sources
"""

from typing import List, Optional

from crewai import Agent
from crewai.tools import tool

from omni.core.logging import get_logger
from omni.core.config import get_settings

logger = get_logger(__name__)


@tool("web_search")
def web_search(query: str, num_results: int = 5) -> str:
    """Search the web for information on any topic.

    Args:
        query: The search query
        num_results: Number of results to return (default 5)

    Returns:
        Search results as string
    """
    from omni.skills.search import SearchSkill

    skill = SearchSkill()
    result = skill.execute("web_search", {"query": query, "num_results": num_results})
    return str(result)


@tool("browse_web")
def browse_web(url: str) -> str:
    """Navigate to a URL and extract information.

    Args:
        url: The URL to navigate to

    Returns:
        Page content as string
    """
    from omni.skills.browser import BrowserSkill

    skill = BrowserSkill()
    result = skill.execute("navigate", {"url": url})
    content = result.get("content", "No content")[:2000]
    title = result.get("title", "No title")
    return f"Title: {title}\n\nContent:\n{content}"


class ResearchAgents:
    """Factory for creating Research department agents.

    Creates agents with appropriate roles, goals, and backstories
    for conducting comprehensive research tasks.

    Usage:
        factory = ResearchAgents()
        agents = factory.create_all()
    """

    def __init__(self):
        """Initialize the agents factory."""
        self.settings = get_settings()
        self.base_url = self.settings.ollama.base_url

    def _create_llm(self, model: str, temperature: float = 0.7) -> str:
        """Create a CrewAI LLM identifier for Ollama."""
        return f"ollama/{model}"

    def create_web_researcher(self) -> Agent:
        """Create the Web Researcher agent."""
        llm = self._create_llm("gemma3:12b", temperature=0.7)

        return Agent(
            role="Web Researcher",
            goal="Gather comprehensive and accurate information from web sources on any given topic",
            backstory="""You are an expert web researcher with years of experience in information 
            gathering. You excel at finding relevant sources, extracting key information, and 
            organizing findings in a structured manner. You are thorough, methodical, and always 
            verify the credibility of your sources. You understand how to navigate complex websites, 
            use search engines effectively, and synthesize information from multiple sources.
            """,
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=[web_search, browse_web],
        )

    def create_content_analyzer(self) -> Agent:
        """Create the Content Analyzer agent."""
        llm = self._create_llm("gemma3:12b", temperature=0.6)

        return Agent(
            role="Content Analyzer",
            goal="Analyze and synthesize research findings into clear, actionable insights with proper citations",
            backstory="""You are a skilled content analyst specializing in synthesizing complex 
            information into digestible insights. You have a talent for identifying key themes, 
            extracting meaningful patterns, and presenting findings in a structured format. You 
            are meticulous about source attribution and ensure all claims are supported by evidence. 
            Your analysis is always objective, comprehensive, and well-organized.
            """,
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def create_fact_checker(self) -> Agent:
        """Create the Fact Checker agent."""
        llm = self._create_llm("llama3.1:8b", temperature=0.3)

        return Agent(
            role="Fact Checker",
            goal="Verify all claims and ensure accuracy by cross-referencing sources and assessing confidence levels",
            backstory="""You are a meticulous fact-checker with a background in investigative 
            research. You have an eye for detail and a commitment to accuracy. You excel at 
            cross-referencing information, identifying inconsistencies, and assessing the 
            reliability of sources. You are skeptical but fair, and you always provide evidence 
            for your assessments. Your goal is to ensure that all information is accurate and 
            trustworthy.
            """,
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def create_all(self) -> List[Agent]:
        """Create all Research department agents."""
        agents = [
            self.create_web_researcher(),
            self.create_content_analyzer(),
            self.create_fact_checker(),
        ]

        logger.debug(
            "Created Research department agents",
            agent_count=len(agents),
            agent_roles=[a.role for a in agents],
        )

        return agents
