"""Writing Department Agents.

Implements specialized agents for writing content.
"""

from typing import List

from crewai import Agent


class WritingAgents:
    """Factory for Writing department agents."""

    def create_editor(self) -> Agent:
        return Agent(
            role="Editorial Agent",
            goal="Edit and refine written content",
            backstory="""Expert editor focused on:
            - Grammar and style consistency
            - Clarity and readability improvements
            - Structural suggestions""",
            verbose=True,
            allow_delegation=False,
        )

    def create_longform_writer(self) -> Agent:
        return Agent(
            role="Long-form Writer",
            goal="Create detailed articles and documentation",
            backstory="""Skilled in:
            - Technical writing
            - Article composition
            - Documentation""",
            verbose=True,
            allow_delegation=False,
        )

    def create_social_writer(self) -> Agent:
        return Agent(
            role="Social Media Writer",
            goal="Create short-form platform content",
            backstory="""Expert in:
            - Twitter/X posts
            - LinkedIn content
            - Engagement optimization""",
            verbose=True,
            allow_delegation=False,
        )

    def create_all(self) -> List[Agent]:
        return [
            self.create_editor(),
            self.create_longform_writer(),
            self.create_social_writer(),
        ]
