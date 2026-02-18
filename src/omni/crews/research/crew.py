"""Research Department Crew.

Implements the ResearchCrew that orchestrates web research, content analysis,
and fact-checking through a sequential process.
"""
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from omni.core.logging import get_logger
from omni.crews.base import BaseCrew
from omni.crews.research.agents import ResearchAgents

logger = get_logger(__name__)


class ResearchTaskInput(BaseModel):
    """Input schema for Research crew tasks."""
    query: str = Field(..., description="The research query or topic to investigate")
    depth: str = Field(default="standard", description="Research depth: quick, standard, or deep")
    sources_required: int = Field(default=5, description="Minimum number of sources to find")


class FactCheckResult(BaseModel):
    """Individual fact-check result."""
    claim: str = Field(..., description="The claim being checked")
    verified: bool = Field(..., description="Whether the claim is verified")
    confidence: str = Field(..., description="Confidence level: high, medium, low")
    notes: str = Field(default="", description="Additional notes about the verification")


class ResearchReport(BaseModel):
    """Output schema for Research crew results."""
    summary: str = Field(..., description="Executive summary of findings")
    key_findings: List[str] = Field(default_factory=list, description="List of key findings")
    sources: List[str] = Field(default_factory=list, description="List of sources consulted")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence score")
    fact_check_results: List[FactCheckResult] = Field(default_factory=list, description="Fact-check results")


class ResearchCrew(BaseCrew):
    """Research department crew for conducting web research and analysis.
    
    This crew uses a sequential process with three specialized agents:
    1. Web Researcher: Gathers information from web sources
    2. Content Analyzer: Synthesizes and structures the findings
    3. Fact Checker: Verifies claims and assesses accuracy
    
    Usage:
        crew = ResearchCrew()
        result = crew.execute({
            "query": "Latest trends in AI agents",
            "depth": "standard",
            "sources_required": 5
        })
    """
    
    # Class attributes
    name = "research"
    description = "Conducts web research, content analysis, and fact-checking"
    input_schema = ResearchTaskInput
    output_schema = ResearchReport
    
    def __init__(self):
        """Initialize the Research crew."""
        super().__init__()
        self.agents_factory = ResearchAgents(self.model_factory)
        self._agents: Optional[List[Agent]] = None
        
    def get_agents(self) -> List[Agent]:
        """Get all Research department agents.
        
        Returns:
            List[Agent]: List of agents in order: Web Researcher, 
                Content Analyzer, Fact Checker
        """
        if self._agents is None:
            self._agents = self.agents_factory.create_all()
        return self._agents
        
    def build_crew(self) -> Crew:
        """Build and configure the Research crew.
        
        Creates a sequential crew with three tasks:
        1. Research Task: Gather information on the query
        2. Analysis Task: Synthesize findings into structured insights
        3. Fact-Check Task: Verify claims and assess accuracy
        
        Returns:
            Crew: Configured CrewAI Crew instance
        """
        agents = self.get_agents()
        web_researcher, content_analyzer, fact_checker = agents
        
        # Task 1: Web Research
        research_task = Task(
            description="""Research the following topic thoroughly: {query}
            
            Research Depth: {depth}
            Minimum Sources Required: {sources_required}
            
            Your task is to:
            1. Search for relevant information from credible web sources
            2. Gather comprehensive data on the topic
            3. Compile raw findings with source URLs
            4. Note key statistics, quotes, and facts
            
            Provide your findings in a structured format including:
            - Raw research notes with source URLs
            - Key facts and statistics discovered
            - Any relevant quotes or expert opinions
            - A list of all sources consulted
            """,
            expected_output="""A comprehensive research report containing:
            - Detailed research notes organized by subtopic
            - At least {sources_required} credible sources with URLs
            - Key facts, statistics, and quotes with attribution
            - Any conflicting information or differing viewpoints found
            """,
            agent=web_researcher,
        )
        
        # Task 2: Content Analysis
        analysis_task = Task(
            description="""Analyze and synthesize the research findings into a structured report.
            
            Review the research notes and:
            1. Identify the most important findings and insights
            2. Organize information into clear themes or categories
            3. Create an executive summary (2-3 paragraphs)
            4. Extract 5-7 key findings as bullet points
            5. Ensure all major claims are attributed to sources
            
            The analysis should be:
            - Objective and balanced
            - Well-organized and easy to understand
            - Supported by evidence from the research
            - Comprehensive yet concise
            """,
            expected_output="""A structured analysis containing:
            - Executive summary (2-3 paragraphs)
            - 5-7 key findings (bullet points)
            - Organized themes/categories
            - Source attribution for major claims
            """,
            agent=content_analyzer,
            context=[research_task],
        )
        
        # Task 3: Fact Checking
        fact_check_task = Task(
            description="""Verify the accuracy of the key findings and claims.
            
            Review the analysis and:
            1. Identify all significant claims and statements
            2. Cross-reference each claim with the original sources
            3. Assess the credibility of sources
            4. Note any potential biases or limitations
            5. Assign confidence levels (high/medium/low) to each finding
            6. Flag any claims that could not be verified
            
            For each claim, provide:
            - The claim text
            - Verification status (verified/unverified/questionable)
            - Confidence level
            - Any notes or caveats
            """,
            expected_output="""A fact-check report containing:
            - List of verified claims with confidence levels
            - List of unverified or questionable claims
            - Overall confidence score (0.0-1.0)
            - Assessment of source credibility
            - Any warnings or limitations about the findings
            """,
            agent=fact_checker,
            context=[analysis_task],
        )
        
        # Build the crew with sequential process
        crew = Crew(
            agents=agents,
            tasks=[research_task, analysis_task, fact_check_task],
            process=Process.sequential,
            verbose=True,
        )
        
        logger.debug("Research crew built successfully")
        
        return crew
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the research crew with the given input.
        
        Args:
            input_data: Dictionary containing:
                - query: The research topic
                - depth: Research depth (quick/standard/deep)
                - sources_required: Minimum number of sources
                
        Returns:
            Dict containing the research report with summary, findings,
            sources, confidence score, and fact-check results
        """
        # Validate input
        validated_input = self.input_schema.model_validate(input_data)
        
        logger.info(
            "Starting research task",
            query=validated_input.query,
            depth=validated_input.depth,
            sources_required=validated_input.sources_required
        )
        
        # Execute using parent class method
        result = super().execute(validated_input.model_dump())
        
        # Structure the output
        try:
            # Try to parse as ResearchReport
            report = self.output_schema.model_validate(result)
            logger.info(
                "Research completed",
                confidence_score=report.confidence_score,
                findings_count=len(report.key_findings),
                sources_count=len(report.sources)
            )
            return report.model_dump()
        except Exception as e:
            logger.warning(
                "Could not parse result as ResearchReport, returning raw",
                error=str(e)
            )
            return {
                "summary": result.get("raw_output", str(result)),
                "key_findings": [],
                "sources": [],
                "confidence_score": 0.5,
                "fact_check_results": [],
                "raw_output": result
            }
