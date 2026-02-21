"""Social Department Crew.

Implements the SocialCrew for social media content creation.
"""

from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from omni.core.logging import get_logger
from omni.crews.base import BaseCrew
from omni.crews.social.agents import SocialAgents

logger = get_logger(__name__)


class SocialTaskInput(BaseModel):
    """Input schema for Social crew tasks."""

    topic: str = Field(..., description="Topic to create content about")
    platforms: List[str] = Field(default_factory=list, description="Target platforms")
    tone: str = Field(default="professional", description="Content tone")
    audience: Optional[str] = Field(default=None, description="Target audience")


class PlatformContent(BaseModel):
    """Content for a specific platform."""

    platform: str = Field(..., description="Platform name")
    content: str = Field(..., description="The content text")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags used")


class SocialContentOutput(BaseModel):
    """Output schema for Social crew results."""

    contents: Dict[str, str] = Field(
        default_factory=dict, description="Content per platform"
    )
    platform_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Platform-specific metadata"
    )
    hashtags: List[str] = Field(default_factory=list, description="All hashtags used")
    optimal_timing: Optional[str] = Field(
        default=None, description="Optimal posting time"
    )
    engagement_predictions: Dict[str, float] = Field(
        default_factory=dict, description="Predicted engagement"
    )


class SocialCrew(BaseCrew):
    """Social department crew for content creation and optimization."""

    name = "social"
    description = "Creates and optimizes social media content"
    input_schema = SocialTaskInput
    output_schema = SocialContentOutput

    def __init__(self):
        super().__init__()
        self.agents_factory = SocialAgents()
        self._agents: Optional[List[Agent]] = None

    def get_agents(self) -> List[Agent]:
        if self._agents is None:
            self._agents = self.agents_factory.create_all()
        return self._agents

    def build_crew(self) -> Crew:
        agents = self.get_agents()
        creator, optimizer, monitor = agents

        create_task = Task(
            description="""Create social media content about: {topic}
            
            Platforms: {platforms}
            Tone: {tone}
            Target Audience: {audience}
            
            Create engaging content appropriate for each platform.""",
            expected_output="""Platform-specific content with hashtags.""",
            agent=creator,
        )

        optimize_task = Task(
            description="""Optimize the content for maximum engagement.""",
            expected_output="""Optimized content with timing recommendations.""",
            agent=optimizer,
            context=[create_task],
        )

        analyze_task = Task(
            description="""Analyze and provide engagement predictions.""",
            expected_output="""Engagement predictions and insights.""",
            agent=monitor,
            context=[optimize_task],
        )

        crew = Crew(
            agents=agents,
            tasks=[create_task, optimize_task, analyze_task],
            process=Process.sequential,
            verbose=True,
        )
        return crew

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        validated_input = self.input_schema.model_validate(input_data)
        logger.info("Starting Social task", topic=validated_input.topic)
        result = super().execute(validated_input.model_dump())

        try:
            output = self.output_schema.model_validate(result)
            return output.model_dump()
        except Exception:
            return {
                "contents": {"default": str(result)},
                "platform_metadata": {},
                "hashtags": [],
            }
