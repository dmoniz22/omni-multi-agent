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

from omni.core.logging import get_logger
from omni.core.config import get_settings

logger = get_logger(__name__)


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
        """Create a CrewAI LLM identifier for Ollama.
        
        Args:
            model: Model name (e.g., "gemma3:12b")
            temperature: Sampling temperature (not used in identifier)
            
        Returns:
            str: LLM identifier string for CrewAI
        """
        # CrewAI expects format: "ollama/model_name"
        return f"ollama/{model}"
        
    def create_web_researcher(self) -> Agent:
        """Create the Web Researcher agent.
        
        Responsible for:
        - Searching and navigating web sources
        - Extracting relevant information
        - Gathering raw data on research topics
        
        Returns:
            Agent: Configured Web Researcher agent
        """
        # Get model from config - uses gemma3:12b for research
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
        )
        
    def create_content_analyzer(self) -> Agent:
        """Create the Content Analyzer agent.
        
        Responsible for:
        - Summarizing research findings
        - Extracting key points and insights
        - Identifying patterns and trends
        - Citing sources appropriately
        
        Returns:
            Agent: Configured Content Analyzer agent
        """
        # Uses gemma3:12b for analysis
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
        """Create the Fact Checker agent.
        
        Responsible for:
        - Verifying claims against sources
        - Cross-referencing information
        - Assessing confidence levels
        - Identifying potential misinformation
        
        Returns:
            Agent: Configured Fact Checker agent
        """
        # Uses llama3.1:8b for fact checking (lighter model for verification tasks)
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
        """Create all Research department agents.
        
        Returns:
            List[Agent]: List containing all three research agents
        """
        agents = [
            self.create_web_researcher(),
            self.create_content_analyzer(),
            self.create_fact_checker(),
        ]
        
        logger.debug(
            "Created Research department agents",
            agent_count=len(agents),
            agent_roles=[a.role for a in agents]
        )
        
        return agents
