"""Regression tests for safe AI-provider failure handling."""

from types import SimpleNamespace

import pytest

from business_analyst.insights import dashboard
from business_analyst.insights.providers import ProviderError


def test_provider_failure_does_not_expose_raw_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider details must not be copied into the UI error message."""
    sensitive_marker = "test-secret-provider-detail"

    shown_errors: list[str] = []

    fake_streamlit = SimpleNamespace(
        header=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        text_area=lambda *args, **kwargs: "",
        button=lambda *args, **kwargs: True,
        error=lambda message: shown_errors.append(str(message)),
    )

    class FakeSettings:
        @classmethod
        def from_env(cls):
            return cls()

        def validate(self):
            return None

    class FailingInsightEngine:
        def __init__(self, *, settings):
            self.settings = settings

        def generate(self, analysis, *, business_context):
            raise ProviderError(
                f"Provider request failed: {sensitive_marker}"
            )

    monkeypatch.setattr(dashboard, "st", fake_streamlit)
    monkeypatch.setattr(dashboard, "InsightSettings", FakeSettings)
    monkeypatch.setattr(dashboard, "InsightEngine", FailingInsightEngine)

    dashboard.render_insight_dashboard(
        analysis=object(),
        workspace_key="phase_7_4_test",
    )

    assert shown_errors
    assert sensitive_marker not in " ".join(shown_errors)
    assert any("Please try again" in message for message in shown_errors)