"""Coding Department Agents.

Implements specialized agents for coding tasks.
"""

from typing import List

from crewai import Agent


class CodingAgents:
    """Factory for Coding department agents."""

    def create_code_generator(self) -> Agent:
        return Agent(
            role="Code Generator",
            goal="Write new code based on requirements",
            backstory="""""Expert programmer skilled in:
            - Multiple languages (Python, JS, etc.)
            - Writing clean, maintainable code
            - Following best practices""",
            verbose=True,
            allow_delegation=False,
        )

    def create_refactoring_agent(self) -> Agent:
        return Agent(
            role="Refactoring Agent",
            goal="Improve existing code",
            backstory="""Code quality expert focused on:
            - Code optimization
            - Design patterns
            - Removing technical debt""",
            verbose=True,
            allow_delegation=False,
        )

    def create_architecture_agent(self) -> Agent:
        return Agent(
            role="Architecture Agent",
            goal="Design system architecture",
            backstory="""Software architect specializing in:
            - System design
            - Scalability
            - Best practices""",
            verbose=True,
            allow_delegation=False,
        )

    def create_all(self) -> List[Agent]:
        return [
            self.create_code_generator(),
            self.create_refactoring_agent(),
            self.create_architecture_agent(),
        ]
