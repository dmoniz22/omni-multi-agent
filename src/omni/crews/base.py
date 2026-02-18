"""Base crew interface for OMNI.

Defines the abstract interface that all CrewAI departments must implement.
This ensures consistency across all departments and enables dynamic discovery.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from crewai import Agent, Crew
from pydantic import BaseModel

from omni.core.config import get_settings
from omni.core.logging import get_logger
from omni.core.models import ModelFactory

logger = get_logger(__name__)


class BaseCrew(ABC):
    """Abstract base class for all CrewAI departments.
    
    All department crews must inherit from this class and implement
    the required abstract methods. The crew registry discovers crews
    by finding classes that inherit from BaseCrew.
    
    Example:
        class ResearchCrew(BaseCrew):
            name = "research"
            description = "Conducts web research and analysis"
            
            def build_crew(self) -> Crew:
                # Build and return CrewAI Crew instance
                pass
    """
    
    # Class attributes (must be overridden by subclasses)
    name: str = ""
    description: str = ""
    input_schema: Optional[Type[BaseModel]] = None
    output_schema: Optional[Type[BaseModel]] = None
    
    def __init__(self):
        """Initialize the crew with settings and model factory."""
        self.settings = get_settings()
        self.model_factory = ModelFactory()
        self._crew: Optional[Crew] = None
        self._agents: Optional[List[Agent]] = None
        
    @abstractmethod
    def build_crew(self) -> Crew:
        """Build and configure the CrewAI Crew instance.
        
        This method creates the agents, tasks, and assembles them into
        a Crew instance with the appropriate process type (sequential,
        hierarchical, etc.).
        
        Returns:
            Crew: Configured CrewAI Crew instance ready for execution.
            
        Raises:
            CrewError: If crew construction fails.
        """
        pass
    
    @abstractmethod
    def get_agents(self) -> List[Agent]:
        """Get the list of agents defined for this crew.
        
        Returns:
            List[Agent]: List of CrewAI Agent instances.
            
        Note:
            This is used for introspection and monitoring purposes.
        """
        pass
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the crew with the given input data.
        
        This is the main entry point for running a crew. It validates
        input, builds the crew (if not already built), executes it,
        and returns the results.
        
        Args:
            input_data: Dictionary containing crew-specific input parameters.
                Must conform to the crew's input_schema if defined.
                
        Returns:
            Dict[str, Any]: Crew execution results. Format depends on
                the crew's output_schema if defined.
                
        Raises:
            CrewError: If crew execution fails.
            ValidationError: If input validation fails.
            
        Example:
            result = crew.execute({
                "query": "Latest AI trends",
                "depth": "standard",
                "sources_required": 5
            })
        """
        logger.info(
            "Executing crew",
            crew_name=self.name,
            input_keys=list(input_data.keys())
        )
        
        # Build crew if not already built
        if self._crew is None:
            self._crew = self.build_crew()
            logger.debug("Crew built successfully", crew_name=self.name)
        
        # Execute the crew
        try:
            result = self._crew.kickoff(inputs=input_data)
            logger.info("Crew execution completed", crew_name=self.name)
            
            # Convert result to dict
            if hasattr(result, 'model_dump'):
                return result.model_dump()
            elif hasattr(result, 'dict'):
                return result.dict()
            elif isinstance(result, dict):
                return result
            else:
                return {"raw_output": str(result)}
                
        except Exception as e:
            logger.error(
                "Crew execution failed",
                crew_name=self.name,
                error=str(e)
            )
            raise CrewExecutionError(
                f"Crew '{self.name}' execution failed: {str(e)}"
            ) from e
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about this crew for registration.
        
        Returns:
            Dict containing crew metadata:
                - name: Crew identifier
                - description: Human-readable description
                - input_schema: Name of input schema class (if any)
                - output_schema: Name of output schema class (if any)
                - agent_count: Number of agents in the crew
        """
        agents = self.get_agents()
        
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema.__name__ if self.input_schema else None,
            "output_schema": self.output_schema.__name__ if self.output_schema else None,
            "agent_count": len(agents),
        }
    
    def reset(self) -> None:
        """Reset the crew, forcing rebuild on next execution.
        
        This is useful for testing or when crew configuration changes.
        """
        self._crew = None
        self._agents = None
        logger.debug("Crew reset", crew_name=self.name)


class CrewExecutionError(Exception):
    """Exception raised when crew execution fails."""
    pass


def register_crew(crew_class: Type[BaseCrew]) -> Type[BaseCrew]:
    """Decorator to register a crew class with the registry.
    
    This decorator can be used to explicitly mark a class for
    registration, though auto-discovery via BaseCrew inheritance
    is the preferred method.
    
    Args:
        crew_class: The crew class to register.
        
    Returns:
        Type[BaseCrew]: The decorated class (unchanged).
        
    Example:
        @register_crew
        class MyCrew(BaseCrew):
            name = "my_crew"
            ...
    """
    # Registration happens in CrewRegistry.discover()
    # This decorator just marks the class for easy identification
    crew_class._registered = True  # type: ignore
    return crew_class
