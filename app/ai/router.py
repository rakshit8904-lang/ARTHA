"""Provider selection. No silent cross-provider fallback: data-sharing is explicit."""

from flask import current_app

from app.ai.providers.base import ProviderError
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.openai import OpenAIProvider


def get_provider(name=None):
    selected = "gemini"  # Single-provider deployment; ignore client model selection.
    if selected == "openai":
        return OpenAIProvider(current_app.config.get("OPENAI_API_KEY", ""),
                              current_app.config.get("OPENAI_MODEL", "gpt-4.1-mini"))
    if selected == "gemini":
        return GeminiProvider(current_app.config.get("GEMINI_API_KEY", ""),
                              current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash"))
    raise ProviderError("Choose a supported AI provider: OpenAI or Gemini.")
