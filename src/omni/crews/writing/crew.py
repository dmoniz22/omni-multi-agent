"""Writing Department Crew.

Implements the WritingCrew for content creation.
"""

from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from omni.core.logging import get_logger
from omni.crews.base import BaseCrew
from omni.crews.writing.agents import WritingAgents


class WritingTaskInput(BaseModel):
    topic: str
    content_type: str = "article"
    style: str = "professional"
    length: str = "medium"
    audience: Optional[str] = None


class WritingOutput(BaseModel):
    title: str = ""
    content: str = ""
    content_type: str = ""
    word_count: int = 0
    style: str = ""


class WritingCrew(BaseCrew):
    name = "writing"
    description = "Creates articles, documentation, and content"
    input_schema = WritingTaskInput
    output_schema = WritingOutput

    def __init__(self):
        super().__init__()
        self.agents_factory = WritingAgents()
        self._agents: Optional[List[Agent]] = None

    def get_agents(self) -> List[Agent]:
        if self._agents is None:
            self._agents = self.agents_factory.create_all()
        return self._agents

    def build_crew(self) -> Crew:
        agents = self.get_agents()
        editor, writer, social = agents

        write_task = Task(
            description="""Write about: {topic}
            Type: {content_type}
            Style: {style}
            Length: {length}
            Audience: {audience}""",
            expected_output="Complete written content.",
            agent=writer,
        )

        edit_task = Task(
            description="Edit and refine the content.",
            expected_output="Polished content.",
            agent=editor,
            context=[write_task],
        )

        return Crew(
            agents=agents,
            tasks=[write_task, edit_task],
            process=Process.sequential,
            verbose=True,
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.input_schema.model_validate(input_data)
        logger.info("Starting Writing", topic=validated.topic)
        result = super().execute(validated.model_dump())

        try:
            output = self.output_schema.model_validate(result)
            return output.model_dump()
        except Exception:
            return {"content": str(result), "title": "", "word_count": 0}
