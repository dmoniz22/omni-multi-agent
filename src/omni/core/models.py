"""LLM client factory for OMNI.

Provides a factory for creating LangChain-compatible ChatModel instances
for different LLM providers, with caching and health checking.
"""
from functools import lru_cache
from typing import Dict, Optional

from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel

from omni.core.config import get_settings
from omni.core.exceptions import ModelError, ModelNotFoundError, ModelConnectionError


class ModelFactory:
    """Factory for creating and caching LLM clients."""
    
    def __init__(self):
        self._clients: Dict[str, BaseChatModel] = {}
        self._settings = get_settings()
    
    def get(
        self,
        model_name: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseChatModel:
        """Get or create a model client.
        
        Args:
            model_name: Name of the model (e.g., "qwen3:14b")
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters
            
        Returns:
            BaseChatModel: Configured chat model instance
            
        Raises:
            ModelNotFoundError: If model configuration not found
            ModelConnectionError: If connection to provider fails
        """
        # Create cache key from all parameters
        cache_key = f"{model_name}:{temperature}:{max_tokens}:{hash(str(sorted(kwargs.items())))}"
        
        if cache_key in self._clients:
            return self._clients[cache_key]
        
        # Get base configuration
        base_url = self._settings.ollama.base_url
        default_timeout = self._settings.ollama.default_timeout
        
        # Create the model
        try:
            model = ChatOllama(
                model=model_name,
                base_url=base_url,
                timeout=default_timeout,
                temperature=temperature or 0.7,
                num_predict=max_tokens or 4096,
                **kwargs
            )
            
            self._clients[cache_key] = model
            return model
            
        except Exception as e:
            raise ModelConnectionError(
                f"Failed to create model client for {model_name}",
                details={"error": str(e)}
            )
    
    def get_for_role(
        self,
        layer: str,
        component: str,
        role: Optional[str] = None,
        **kwargs
    ) -> BaseChatModel:
        """Get a model client based on role assignment from config.
        
        Args:
            layer: Layer name (e.g., "orchestrator", "departments", "validators")
            component: Component name (e.g., "github", "research")
            role: Optional specific role (e.g., "manager", "researcher")
            **kwargs: Additional model parameters
            
        Returns:
            BaseChatModel: Configured chat model instance
        """
        # This will be implemented to read from models.yaml
        # For now, use defaults based on the layer
        model_assignments = {
            "orchestrator": "qwen3:14b",
            "departments": "gemma3:12b",
            "validators": "phi3.5:3.8b",
        }
        
        model_name = model_assignments.get(layer, "qwen3:14b")
        
        # Get temperature based on layer
        if layer == "validators":
            temperature = 0.1  # Low for deterministic validation
        elif layer == "departments" and component == "coding":
            temperature = 0.3  # Lower for code
        else:
            temperature = 0.7  # Default
        
        return self.get(model_name, temperature=temperature, **kwargs)
    
    def get_embedding_model(self) -> str:
        """Get the configured embedding model name.
        
        Returns:
            str: Embedding model name
        """
        return self._settings.memory.embedding_model
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of configured models.
        
        Returns:
            Dict[str, bool]: Model names mapped to health status
        """
        import httpx
        
        base_url = self._settings.ollama.base_url
        results = {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/tags", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    available_models = {m["name"] for m in data.get("models", [])}
                    
                    # Check key models
                    for model in ["qwen3:14b", "gemma3:12b", "phi3.5:3.8b"]:
                        results[model] = model in available_models
                else:
                    results["error"] = False
        except Exception as e:
            results["error"] = False
            results["details"] = str(e)
        
        return results
    
    def clear_cache(self):
        """Clear the model client cache.
        
        Useful when configuration changes or for memory management.
        """
        self._clients.clear()


# Global factory instance
_model_factory: Optional[ModelFactory] = None


def get_model_factory() -> ModelFactory:
    """Get the global model factory instance.
    
    Returns:
        ModelFactory: The model factory singleton
    """
    global _model_factory
    if _model_factory is None:
        _model_factory = ModelFactory()
    return _model_factory


def get_model(
    model_name: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> BaseChatModel:
    """Convenience function to get a model client.
    
    Args:
        model_name: Name of the model
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters
        
    Returns:
        BaseChatModel: Configured chat model instance
    """
    factory = get_model_factory()
    return factory.get(model_name, temperature, max_tokens, **kwargs)
