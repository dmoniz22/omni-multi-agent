"""Dashboard configuration and utilities."""

import os
from pathlib import Path

import httpx
import yaml

from omni.core.logging import get_logger

logger = get_logger(__name__)

MODELS_CONFIG_PATH = (
    Path(__file__).parent.parent.parent.parent / "config" / "models.yaml"
)

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

CLOUD_MODELS = {
    "openrouter": [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-opus",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/o1",
        "openai/o1-mini",
        "google/gemini-2.0-flash",
        "google/gemini-pro-1.5",
        "meta-llama/llama-3-70b-instruct",
        "mistralai/mistral-7b-instruct",
        "deepseek/deepseek-chat-v3",
    ],
    "openai-compatible": [],
}


def get_available_models() -> list[str]:
    """Get available Ollama models."""
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return ["qwen3:14b", "llama3.1:8b", "gemma3:12b"]


def get_all_available_models() -> list[str]:
    """Get all available models including cloud providers.

    Returns models with provider prefixes for display in dropdowns.
    """
    models = []

    ollama_models = get_available_models()
    for m in ollama_models:
        models.append(f"ollama:{m}")

    config = load_model_config()
    providers = config.get("providers", {})

    if providers.get("openrouter"):
        models.extend([f"openrouter:{m}" for m in CLOUD_MODELS["openrouter"]])

    if providers.get("openai_compatible"):
        models.extend(
            [f"openai-compatible:{m}" for m in CLOUD_MODELS["openai-compatible"]]
        )

    return models


def get_model_choices_for_dropdown() -> list[tuple[str, str]]:
    """Get model choices formatted for Gradio dropdown.

    Returns list of (label, value) tuples.
    """
    models = get_all_available_models()
    choices = []
    for m in models:
        if m.startswith("ollama:"):
            label = f"🖥️ {m.replace('ollama:', '')}"
        elif m.startswith("openrouter:"):
            label = f"☁️ {m.replace('openrouter:', '')}"
        elif m.startswith("openai-compatible:"):
            label = f"🔗 {m.replace('openai-compatible:', '')}"
        else:
            label = m
        choices.append((label, m))
    return choices


def is_cloud_model(model_name: str) -> bool:
    """Check if a model is a cloud model."""
    return model_name.startswith(("openrouter:", "openai-compatible:"))


def strip_provider_prefix(model_name: str) -> str:
    """Strip the provider prefix from a model name.

    Args:
        model_name: Model name with optional prefix (e.g., "ollama:qwen3:14b")

    Returns:
        Bare model name (e.g., "qwen3:14b")
    """
    if model_name.startswith(("ollama:", "openrouter:", "openai-compatible:")):
        return model_name.split(":", 1)[1]
    return model_name


def add_provider_prefix(model_name: str, provider: str = "ollama") -> str:
    """Add provider prefix to a model name if not already present.

    Args:
        model_name: Bare model name (e.g., "qwen3:14b")
        provider: Provider to use (default: "ollama")

    Returns:
        Prefixed model name (e.g., "ollama:qwen3:14b")
    """
    if model_name.startswith(("ollama:", "openrouter:", "openai-compatible:")):
        return model_name
    return f"{provider}:{model_name}"


def get_provider_for_model(model_name: str) -> str:
    """Get the provider name for a model."""
    if model_name.startswith("openrouter:"):
        return "openrouter"
    elif model_name.startswith("openai-compatible:"):
        return "openai_compatible"
    elif model_name.startswith("ollama:"):
        return "ollama"
    return "unknown"


def load_model_config() -> dict:
    """Load model configuration from YAML file."""
    try:
        if MODELS_CONFIG_PATH.exists():
            with open(MODELS_CONFIG_PATH, "r") as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load model config: {e}")
    return {}


def save_model_config(config: dict) -> bool:
    """Save model configuration to YAML file."""
    try:
        MODELS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODELS_CONFIG_PATH, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        logger.warning(f"Failed to save model config: {e}")
        return False


def get_crew_agents(crew_name: str) -> list[str]:
    """Get agents for a specific crew."""
    agents_map = {
        "Research": ["web_researcher", "content_analyzer", "fact_checker"],
        "GitHub": ["researcher", "code_analyst", "gist_creator"],
        "Social": ["content_creator", "engagement_optimizer", "analytics_monitor"],
        "Analysis": ["data_analyst", "insight_generator", "report_creator"],
        "Writing": ["editorial", "longform", "social_media"],
        "Coding": ["generator", "refactorer", "architect"],
    }
    return agents_map.get(crew_name, [])
