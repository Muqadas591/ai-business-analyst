"""Hosted LLM provider adapters."""

from business_analyst.insights.providers.openai_compatible import (
    OpenAICompatibleProvider,
    ProviderError,
)

__all__ = ["OpenAICompatibleProvider", "ProviderError"]
