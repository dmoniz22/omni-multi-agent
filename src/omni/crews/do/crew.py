"""Do Department Crew.

Implements the DoCrew that executes computer automation tasks
using the available skills (computer, shell, browser, screenshot).
"""

from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from omni.core.logging import get_logger
from omni.crews.base import BaseCrew
from omni.crews.do.agents import DoAgents

logger = get_logger(__name__)


class DoTaskInput(BaseModel):
    """Input schema for Do crew tasks."""

    goal: str = Field(..., description="What the user wants to accomplish")
    max_steps: int = Field(default=20, description="Maximum number of steps to execute")


class DoTaskResult(BaseModel):
    """Output schema for Do crew results."""

    success: bool = Field(
        ..., description="Whether the task was completed successfully"
    )
    steps_executed: int = Field(default=0, description="Number of steps executed")
    summary: str = Field(..., description="Summary of what was accomplished")
    errors: List[str] = Field(
        default_factory=list, description="Any errors encountered"
    )


class DoCrew(BaseCrew):
    """Do (Executor) department crew for computer automation tasks.

    This crew uses a sequential process with three specialized agents:
    1. Planner: Breaks down tasks into executable steps
    2. Executor: Uses computer skills to execute actions
    3. Verifier: Verifies task completion

    Available Skills:
        - computer: Mouse/keyboard control
        - shell: Command execution
        - screenshot: Screen capture
        - browser: Web automation
        - file: File operations

    Usage:
        crew = DoCrew()
        result = crew.execute({
            "goal": "Open browser and search for AI news",
            "max_steps": 10
        })
    """

    name = "do"
    description = "Executes computer automation tasks using available skills"
    input_schema = DoTaskInput
    output_schema = DoTaskResult

    def __init__(self):
        """Initialize the Do crew."""
        super().__init__()
        self.agents_factory = DoAgents()
        self._agents: Optional[List[Agent]] = None

    def get_agents(self) -> List[Agent]:
        """Get all Do department agents."""
        if self._agents is None:
            self._agents = self.agents_factory.create_all()
        return self._agents

    def build_crew(self) -> Crew:
        """Build and configure the Do crew."""
        agents = self.get_agents()
        planner, executor, verifier = agents

        # Task 1: Planning
        planning_task = Task(
            description="""Analyze the user's goal and create a detailed execution plan.
            
            Goal: {goal}
            Max Steps: {max_steps}
            
            Available skills to use:
            - computer: move_mouse, click_mouse, type_text, press_key, hotkey, scroll
            - shell: run_command, run_script
            - screenshot: capture_screen, get_windows
            - browser: navigate, scrape, search
            
            Create a numbered step-by-step plan. For each step specify:
            1. What action to take
            2. Which skill and action to use
            3. Parameters needed
            4. How to verify success
            """,
            expected_output="""A numbered plan with each step containing:
            - Step number and description
            - Skill and action to use
            - Parameters (in JSON format)
            - Expected result
            """,
            agent=planner,
        )

        # Task 2: Execution
        execution_task = Task(
            description="""Execute the plan created by the Planner.
            
            Available skills:
            - computer: move_mouse(x, y), click_mouse(x, y, button), type_text(text), press_key(key), hotkey(keys), scroll(clicks)
            - shell: run_command(command, timeout), run_script(script, language)
            - screenshot: capture_screen(region), get_windows()
            - browser: navigate(url), scrape(), search(query)
            
            For each step in the plan:
            1. Execute the action using the appropriate skill
            2. Check if it succeeded
            3. If it failed, try an alternative approach
            4. Take a screenshot after important steps to verify
            
            Report the result of each step.
            """,
            expected_output="""Execution results for each step:
            - Step number
            - Action taken
            - Success/failure
            - Any errors
            - Screenshots if taken
            """,
            agent=executor,
            context=[planning_task],
        )

        # Task 3: Verification
        verification_task = Task(
            description="""Verify that the task was completed successfully.
            
            Review the execution results and:
            1. Check if all planned steps were executed
            2. Verify the final state matches the goal
            3. Identify any issues or errors
            4. Provide a summary of what was accomplished
            
            Goal: {goal}
            """,
            expected_output="""Final verification report containing:
            - Success status (true/false)
            - Steps executed count
            - Summary of accomplishments
            - Any errors or issues
            """,
            agent=verifier,
            context=[execution_task],
        )

        # Build the crew with sequential process
        crew = Crew(
            agents=agents,
            tasks=[planning_task, execution_task, verification_task],
            process=Process.sequential,
            verbose=True,
        )

        logger.debug("Do crew built successfully")

        return crew

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Do crew with the given input."""
        validated_input = self.input_schema.model_validate(input_data)

        logger.info(
            "Starting Do task",
            goal=validated_input.goal,
            max_steps=validated_input.max_steps,
        )

        result = super().execute(validated_input.model_dump())

        try:
            report = self.output_schema.model_validate(result)
            logger.info(
                "Do task completed", success=report.success, steps=report.steps_executed
            )
            return report.model_dump()
        except Exception as e:
            logger.warning("Could not parse result as DoTaskResult", error=str(e))
            return {
                "success": True,
                "steps_executed": 0,
                "summary": result.get("raw_output", str(result)),
                "errors": [],
                "raw_output": result,
            }
