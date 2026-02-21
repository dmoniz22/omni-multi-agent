"""Coding Department Crew.

Implements the CodingCrew for code generation and refactoring.
"""

from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from omni.core.logging import get_logger
from omni.crews.base import BaseCrew
from omni.crews.coding.agents import CodingAgents


class CodingTaskInput(BaseModel):
    task: str
    language: Optional[str] = None
    existing_code: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)


class CodingOutput(BaseModel):
    success: bool = True
    code: str = ""
    explanation: str = ""
    tests: Optional[str] = None
    files_created: List[str] = Field(default_factory=list)


class CodingCrew(BaseCrew):
    name = "coding"
    description = "Generates and refactors code"
    input_schema = CodingTaskInput
    output_schema = CodingOutput

    def __init__(self):
        super().__init__()
        self.agents_factory = CodingAgents()
        self._agents: Optional[List[Agent]] = None

    def get_agents(self) -> List[Agent]:
        if self._agents is None:
            self._agents = self.agents_factory.create_all()
        return self._agents

    def build_crew(self) -> Crew:
        agents = self.get_agents()
        generator, refactorer, architect = agents

        design_task = Task(
            description="""Design the architecture for: {task}
            Language: {language}
            Requirements: {requirements}""",
            expected_output="Architecture design document.",
            agent=architect,
        )

        generate_task = Task(
            description="Generate code based on the design.",
            expected_output="Code implementation.",
            agent=generator,
            context=[design_task],
        )

        return Crew(
            agents=agents,
            tasks=[design_task, generate_task],
            process=Process.hierarchical,
            verbose=True,
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.input_schema.model_validate(input_data)
        logger.info("Starting Coding", task=validated.task)
        result = super().execute(validated.model_dump())

        try:
            output = self.output_schema.model_validate(result)
            return output.model_dump()
        except Exception:
            return {
                "success": True,
                "code": str(result),
                "explanation": "",
                "files_created": [],
            }
