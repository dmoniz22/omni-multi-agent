"""Do Department Agents.

Defines the agents for the Do (Executor) department that can execute
computer tasks using available skills.
"""

from typing import List

from crewai import Agent

from omni.core.logging import get_logger
from omni.core.config import get_settings

logger = get_logger(__name__)


class DoAgents:
    """Factory for creating Do department agents.

    Creates agents that can execute tasks on the computer using
    mouse, keyboard, shell, and other automation skills.
    """

    def __init__(self):
        """Initialize the agents factory."""
        self.settings = get_settings()

    def _create_llm(self, model: str, temperature: float = 0.7) -> str:
        """Create a CrewAI LLM identifier for Ollama."""
        return f"ollama/{model}"

    def create_planner_agent(self) -> Agent:
        """Create the Planner agent - breaks down tasks into steps."""
        llm = self._create_llm("qwen3:14b", temperature=0.7)

        return Agent(
            role="Planner",
            goal="Break down complex tasks into clear, executable steps",
            backstory="""You are an expert task planner. You analyze what the user wants 
            to accomplish and create a detailed step-by-step plan. You think about what 
            tools and actions are needed, anticipate potential issues, and sequence 
            steps in the most efficient order. You always consider the current state 
            of the computer before executing actions.""",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def create_executor_agent(self) -> Agent:
        """Create the Executor agent - executes actions using skills."""
        llm = self._create_llm("qwen3:14b", temperature=0.3)

        return Agent(
            role="Executor",
            goal="Execute tasks using available computer skills accurately and safely",
            backstory="""You are an expert at executing automation tasks. You have access 
            to computer skills including mouse control, keyboard input, shell commands, 
            screenshots, and browser automation. You carefully execute each step, verify 
            success, and handle errors gracefully. You always check the current state 
            before taking actions and confirm results.""",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def create_verifier_agent(self) -> Agent:
        """Create the Verifier agent - verifies task completion."""
        llm = self._create_llm("gemma3:12b", temperature=0.5)

        return Agent(
            role="Verifier",
            goal="Verify that tasks have been completed successfully",
            backstory="""You are a thorough verifier. After each action, you check that 
            it completed successfully. You take screenshots to verify visual changes, 
            check outputs of commands, and confirm the final state matches expectations. 
            If something went wrong, you identify the issue and recommend fixes.""",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        )

    def create_all(self) -> List[Agent]:
        """Create all Do department agents."""
        agents = [
            self.create_planner_agent(),
            self.create_executor_agent(),
            self.create_verifier_agent(),
        ]

        logger.debug(
            "Created Do department agents",
            agent_count=len(agents),
            agent_roles=[a.role for a in agents],
        )

        return agents
