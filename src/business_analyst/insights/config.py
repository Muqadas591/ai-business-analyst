"""Environment-based configuration for hosted insight generation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# config.py is inside:
# project_root/src/business_analyst/insights/config.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=False)


@dataclass(frozen=True)
class InsightSettings:
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 45.0
    max_output_tokens: int = 2500
    max_evidence_chars: int = 24000

    @classmethod
    def from_env(cls) -> "InsightSettings":
        return cls(
            provider=os.getenv("INSIGHT_PROVIDER", "openai_compatible"),
            base_url=os.getenv("INSIGHT_BASE_URL", "").rstrip("/"),
            api_key=os.getenv("INSIGHT_API_KEY", ""),
            model=os.getenv("INSIGHT_MODEL", ""),
            timeout_seconds=float(os.getenv("INSIGHT_TIMEOUT_SECONDS", "45")),
            max_output_tokens=int(os.getenv("INSIGHT_MAX_OUTPUT_TOKENS", "2500")),
            max_evidence_chars=int(os.getenv("INSIGHT_MAX_EVIDENCE_CHARS", "24000")),
        )

    def validate(self) -> None:
        if self.provider != "openai_compatible":
            raise ValueError(f"Unsupported provider: {self.provider!r}")
        if not self.base_url:
            raise ValueError("INSIGHT_BASE_URL is required.")
        if not self.api_key:
            raise ValueError("INSIGHT_API_KEY is required.")
        if not self.model:
            raise ValueError("INSIGHT_MODEL is required.")
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be greater than zero.")
        if self.max_output_tokens < 1:
            raise ValueError("Max output tokens must be positive.")
        if self.max_evidence_chars < 1000:
            raise ValueError("Evidence limit must be at least 1000.")
