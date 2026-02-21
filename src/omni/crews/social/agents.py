"""Social Department Agents.

Implements specialized agents for social media content creation.
"""

from typing import List

from crewai import Agent


class SocialAgents:
    """Factory for Social department agents."""

    def create_content_creator(self) -> Agent:
        """Create the Content Creator agent."""
        return Agent(
            role="Content Creator",
            goal="Generate engaging social media content for various platforms",
            backstory="""You are an expert content creator for social media platforms.
            
            You excel at:
            - Writing compelling posts for Twitter, LinkedIn, Discord, etc.
            - Adapting content for different platforms and audiences
            - Creating engaging hooks and calls-to-action
            - Optimizing content length and format for each platform""",
            verbose=True,
            allow_delegation=False,
        )

    def create_engagement_optimizer(self) -> Agent:
        """Create the Engagement Optimizer agent."""
        return Agent(
            role="Engagement Optimizer",
            goal="Optimize content for maximum engagement and reach",
            backstory="""You specialize in maximizing social media engagement.
            
            You know how to:
            - Analyze optimal posting times
            - Research audience demographics and preferences
            - Identify trending topics and hashtags
            - Craft engaging captions and CTAs""",
            verbose=True,
            allow_delegation=False,
        )

    def create_analytics_monitor(self) -> Agent:
        """Create the Analytics Monitor agent."""
        return Agent(
            role="Analytics Monitor",
            goal="Track and analyze social media performance metrics",
            backstory="""You are an expert at analyzing social media analytics.
            
            You can:
            - Interpret engagement metrics and trends
            - Identify top-performing content patterns
            - Provide data-driven recommendations
            - Generate insight reports""",
            verbose=True,
            allow_delegation=False,
        )

    def create_all(self) -> List[Agent]:
        """Create all Social department agents."""
        return [
            self.create_content_creator(),
            self.create_engagement_optimizer(),
            self.create_analytics_monitor(),
        ]
