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
    "openai": ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini"],
    "anthropic": ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
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
    """Get all available models including cloud providers."""
    models = []

    ollama_models = get_available_models()
    for m in ollama_models:
        models.append(f"ollama:{m}")

    config = load_model_config()
    providers = config.get("providers", {})

    if providers.get("openai"):
        models.extend([f"openai:{m}" for m in CLOUD_MODELS["openai"]])

    if providers.get("anthropic"):
        models.extend([f"anthropic:{m}" for m in CLOUD_MODELS["anthropic"]])

    return models


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
