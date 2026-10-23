"""Provider interface for hosted language models."""

from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model's raw textual response."""
        ...
