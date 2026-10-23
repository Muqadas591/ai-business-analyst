"""Generate and validate evidence-grounded business insights."""

from __future__ import annotations

from business_analyst.analysis.models import AnalysisResult
from business_analyst.insights.config import InsightSettings
from business_analyst.insights.evidence import build_evidence_packet
from business_analyst.insights.models import InsightReport
from business_analyst.insights.prompts import SYSTEM_PROMPT, build_user_prompt
from business_analyst.insights.providers import (
    OpenAICompatibleProvider,
    ProviderError,
)
from business_analyst.insights.validation import (
    InsightValidationError,
    validate_report,
)


class InsightEngine:
    def __init__(
        self,
        provider: object | None = None,
        settings: InsightSettings | None = None,
    ) -> None:
        self._settings = settings or InsightSettings.from_env()
        self._provider = provider

    def generate(
        self,
        analysis: AnalysisResult,
        *,
        business_context: str = "",
    ) -> InsightReport:
        evidence = build_evidence_packet(
            analysis,
            max_chars=self._settings.max_evidence_chars,
        )
        if not evidence:
            raise InsightValidationError(
                "There is not enough analytical evidence to generate insights."
            )

        provider = self._provider
        if provider is None:
            provider = OpenAICompatibleProvider(self._settings)

        user_prompt = build_user_prompt(
            evidence,
            business_context=business_context,
        )

        try:
            raw_response = provider.generate(
                SYSTEM_PROMPT,
                user_prompt,
            )
        except ProviderError:
            raise
        except Exception as exc:
            # Do not expose credentials, prompts, or raw provider internals.
            raise ProviderError(
                "Insight generation failed. Check provider configuration "
                "and service availability."
            ) from exc

        return validate_report(raw_response, evidence)
