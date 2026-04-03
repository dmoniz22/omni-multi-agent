"""LLM client factory for OMNI.

Provides a factory for creating LangChain-compatible ChatModel instances
for different LLM providers, with caching and health checking.
"""

import threading
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from omni.core.config import get_settings
from omni.core.exceptions import ModelConnectionError

_model_factory_lock = threading.Lock()


class ModelFactory:
    """Factory for creating and caching LLM clients."""

    def __init__(self):
        self._clients: dict[str, BaseChatModel] = {}
        self._settings = get_settings()

    def _create_ollama_model(
        self,
        model_name: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        **kwargs,
    ) -> BaseChatModel:
        """Create an Ollama model client."""
        base_url = self._settings.ollama.base_url
        default_timeout = self._settings.ollama.default_timeout

        return ChatOllama(
            model=model_name,
            base_url=base_url,
            timeout=default_timeout,
            temperature=temperature if temperature is not None else 0.7,
            num_predict=max_tokens if max_tokens is not None else 4096,
            **kwargs,
        )

    def _create_openrouter_model(
        self,
        model_name: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        **kwargs,
    ) -> BaseChatModel:
        """Create an OpenRouter model client."""
        api_key = self._settings.openrouter.api_key
        if not api_key:
            raise ModelConnectionError(
                "OpenRouter API key not configured. Set OPENROUTER_API_KEY environment variable."
            )

        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=temperature if temperature is not None else 0.7,
            max_tokens=max_tokens if max_tokens is not None else 4096,
            **kwargs,
        )

    def _create_openai_compatible_model(
        self,
        model_name: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        **kwargs,
    ) -> BaseChatModel:
        """Create an OpenAI-compatible model client (for local proxies, Ollama with API key, etc.)."""
        api_key = self._settings.openai_compatible.api_key or "not-needed"
        base_url = self._settings.openai_compatible.base_url
        default_timeout = self._settings.openai_compatible.default_timeout

        if not base_url:
            raise ModelConnectionError(
                "OpenAI-compatible base URL not configured. Set OPENAI_BASE_URL environment variable."
            )

        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url,
            timeout=default_timeout,
            temperature=temperature if temperature is not None else 0.7,
            max_tokens=max_tokens if max_tokens is not None else 4096,
            **kwargs,
        )

    def get(
        self,
        model_name: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> BaseChatModel:
        """Get or create a model client.

        Args:
            model_name: Name of the model (e.g., "qwen3:14b" or "openrouter:anthropic/claude-3.5-sonnet")
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

        # Parse model prefix to determine provider
        if model_name.startswith("openrouter:"):
            actual_model = model_name.replace("openrouter:", "")
            model = self._create_openrouter_model(
                actual_model, temperature, max_tokens, **kwargs
            )
        elif model_name.startswith("openai-compatible:"):
            actual_model = model_name.replace("openai-compatible:", "")
            model = self._create_openai_compatible_model(
                actual_model, temperature, max_tokens, **kwargs
            )
        elif ":" in model_name and not model_name.startswith(
            ("ollama:", "anthropic:", "google:", "cohere:")
        ):
            # Assume OpenAI-compatible if it has a colon but no known prefix
            # This handles cases like "custom-model:version" from local proxies
            actual_model = model_name
            model = self._create_openai_compatible_model(
                actual_model, temperature, max_tokens, **kwargs
            )
        else:
            # Default to Ollama
            model = self._create_ollama_model(
                model_name, temperature, max_tokens, **kwargs
            )

        self._clients[cache_key] = model
        return model

    def get_for_role(
        self, layer: str, component: str, role: Optional[str] = None, **kwargs
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

    async def health_check(self) -> dict[str, bool]:
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
    """Get the global model factory instance (thread-safe).

    Returns:
        ModelFactory: The model factory singleton
    """
    global _model_factory
    if _model_factory is None:
        with _model_factory_lock:
            if _model_factory is None:
                _model_factory = ModelFactory()
    return _model_factory


def get_model(
    model_name: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs,
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
