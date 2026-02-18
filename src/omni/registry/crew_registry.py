"""Crew registry for OMNI.

Manages registration, discovery, and execution of CrewAI departments.
Provides auto-discovery from the crews directory and dynamic crew lookup.
"""
import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from omni.core.logging import get_logger
from omni.crews.base import BaseCrew

logger = get_logger(__name__)


class CrewRegistry:
    """Registry for managing CrewAI departments.
    
    The registry provides:
    - Auto-discovery of crews from the crews directory
    - Registration and lookup of crew classes
    - Execution of crews by name
    - Listing of available crews
    
    Usage:
        registry = CrewRegistry()
        registry.discover()  # Auto-discover all crews
        
        # Get crew info
        info = registry.get_info("research")
        
        # Execute a crew
        result = registry.execute("research", {"query": "AI trends"})
    """
    
    def __init__(self):
        """Initialize the crew registry."""
        self._crews: Dict[str, Type[BaseCrew]] = {}
        self._crew_info: Dict[str, Dict[str, Any]] = {}
        self._discovered = False
        
    def register(self, crew_class: Type[BaseCrew]) -> None:
        """Register a crew class with the registry.
        
        Args:
            crew_class: A class that inherits from BaseCrew.
            
        Raises:
            ValueError: If the crew class doesn't have a name or name is empty.
            ValueError: If a crew with the same name is already registered.
            TypeError: If crew_class doesn't inherit from BaseCrew.
            
        Example:
            registry.register(ResearchCrew)
        """
        if not inspect.isclass(crew_class):
            raise TypeError(f"Expected a class, got {type(crew_class)}")
            
        if not issubclass(crew_class, BaseCrew):
            raise TypeError(
                f"Crew class must inherit from BaseCrew: {crew_class.__name__}"
            )
            
        name = crew_class.name
        if not name:
            raise ValueError(
                f"Crew class must have a 'name' attribute: {crew_class.__name__}"
            )
            
        if name in self._crews:
            logger.warning(
                "Crew already registered, overwriting",
                crew_name=name,
                existing_class=self._crews[name].__name__,
                new_class=crew_class.__name__
            )
            
        self._crews[name] = crew_class
        
        # Store crew info from the class
        self._crew_info[name] = {
            "name": name,
            "description": crew_class.description or "",
            "input_schema": crew_class.input_schema.__name__ if crew_class.input_schema else None,
            "output_schema": crew_class.output_schema.__name__ if crew_class.output_schema else None,
            "class_name": crew_class.__name__,
        }
        
        logger.debug("Crew registered", crew_name=name, class_name=crew_class.__name__)
        
    def get(self, name: str) -> Optional[Type[BaseCrew]]:
        """Get a crew class by name.
        
        Args:
            name: The crew identifier (e.g., "research", "github").
            
        Returns:
            Type[BaseCrew] or None: The crew class if found, None otherwise.
            
        Example:
            CrewClass = registry.get("research")
            if CrewClass:
                crew = CrewClass()
        """
        crew_class = self._crews.get(name)
        if crew_class is None:
            logger.warning("Crew not found in registry", crew_name=name)
        return crew_class
        
    def get_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered crew.
        
        Args:
            name: The crew identifier.
            
        Returns:
            Dict or None: Crew metadata including name, description,
                input/output schemas, etc.
        """
        return self._crew_info.get(name)
        
    def list_available(self) -> List[Dict[str, Any]]:
        """List all available (registered) crews.
        
        Returns:
            List[Dict]: List of crew info dictionaries, one per registered crew.
            
        Example:
            crews = registry.list_available()
            for crew in crews:
                print(f"{crew['name']}: {crew['description']}")
        """
        return list(self._crew_info.values())
        
    def execute(self, name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a crew by name with the given input.
        
        This is a convenience method that instantiates the crew,
        builds it, and executes it with the provided input.
        
        Args:
            name: The crew identifier.
            input_data: Dictionary of input parameters for the crew.
            
        Returns:
            Dict: Crew execution results.
            
        Raises:
            ValueError: If the crew is not registered.
            CrewExecutionError: If crew execution fails.
            
        Example:
            result = registry.execute("research", {
                "query": "Latest AI trends",
                "depth": "standard"
            })
        """
        crew_class = self.get(name)
        if crew_class is None:
            raise ValueError(f"Crew '{name}' not found in registry")
            
        logger.info("Executing crew via registry", crew_name=name)
        
        # Instantiate and execute
        crew_instance = crew_class()
        return crew_instance.execute(input_data)
        
    def discover(self, package_path: Optional[str] = None) -> int:
        """Auto-discover crews from the crews directory.
        
        Scans all subdirectories in the crews package for modules
        that define classes inheriting from BaseCrew.
        
        Args:
            package_path: Optional path to scan. Defaults to omni.crews.
            
        Returns:
            int: Number of crews discovered and registered.
            
        Note:
            This method should be called once during application startup.
            It will not re-scan if already called (use force=True to override).
            
        Example:
            count = registry.discover()
            print(f"Discovered {count} crews")
        """
        if self._discovered and package_path is None:
            logger.debug("Crews already discovered, skipping")
            return len(self._crews)
            
        if package_path is None:
            # Default to the crews package
            from omni import crews as crews_package
            package_path = crews_package.__path__[0]  # type: ignore
            package_name = "omni.crews"
        else:
            package_name = package_path.replace("/", ".").replace("\\", ".")
            
        discovered_count = 0
        crews_dir = Path(package_path)
        
        logger.info("Discovering crews", crews_dir=str(crews_dir))
        
        # Iterate through subdirectories (department folders)
        for dept_dir in crews_dir.iterdir():
            if not dept_dir.is_dir() or dept_dir.name.startswith("_"):
                continue
                
            dept_name = dept_dir.name
            
            # Look for crew.py or similar files
            for py_file in dept_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                    
                module_name = f"{package_name}.{dept_name}.{py_file.stem}"
                
                try:
                    # Import the module
                    module = importlib.import_module(module_name)
                    
                    # Find BaseCrew subclasses
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseCrew) and 
                            obj is not BaseCrew and
                            obj.name):  # Has a name attribute
                            
                            self.register(obj)
                            discovered_count += 1
                            logger.debug(
                                "Discovered crew",
                                crew_name=obj.name,
                                module=module_name,
                                class_name=name
                            )
                            
                except ImportError as e:
                    logger.warning(
                        "Failed to import crew module",
                        module=module_name,
                        error=str(e)
                    )
                except Exception as e:
                    logger.error(
                        "Error discovering crew",
                        module=module_name,
                        error=str(e)
                    )
                    
        self._discovered = True
        
        logger.info(
            "Crew discovery complete",
            discovered_count=discovered_count,
            total_crews=len(self._crews)
        )
        
        return discovered_count
        
    def is_registered(self, name: str) -> bool:
        """Check if a crew is registered.
        
        Args:
            name: The crew identifier.
            
        Returns:
            bool: True if registered, False otherwise.
        """
        return name in self._crews
        
    def unregister(self, name: str) -> bool:
        """Unregister a crew.
        
        Args:
            name: The crew identifier.
            
        Returns:
            bool: True if crew was unregistered, False if not found.
        """
        if name in self._crews:
            del self._crews[name]
            del self._crew_info[name]
            logger.debug("Crew unregistered", crew_name=name)
            return True
        return False
        
    def clear(self) -> None:
        """Clear all registered crews.
        
        This is primarily useful for testing.
        """
        self._crews.clear()
        self._crew_info.clear()
        self._discovered = False
        logger.debug("Crew registry cleared")


# Global registry instance
_registry: Optional[CrewRegistry] = None


def get_crew_registry() -> CrewRegistry:
    """Get the global crew registry instance.
    
    Returns:
        CrewRegistry: The global registry instance.
        
    Note:
        The registry is lazily initialized. First call will create
        and discover crews.
    """
    global _registry
    if _registry is None:
        _registry = CrewRegistry()
        _registry.discover()
    return _registry


def reset_crew_registry() -> CrewRegistry:
    """Reset and recreate the global crew registry.
    
    Useful for testing or when crews need to be re-discovered.
    
    Returns:
        CrewRegistry: The new global registry instance.
    """
    global _registry
    _registry = CrewRegistry()
    _registry.discover()
    return _registry
