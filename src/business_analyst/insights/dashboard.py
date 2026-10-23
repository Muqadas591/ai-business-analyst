"""Streamlit interface for AI-generated business insights."""

from __future__ import annotations

import json

import streamlit as st

from business_analyst.analysis.models import AnalysisResult
from business_analyst.insights.config import InsightSettings
from business_analyst.insights.engine import InsightEngine
from business_analyst.insights.providers import ProviderError
from business_analyst.insights.validation import InsightValidationError


def render_insight_dashboard(
    analysis: AnalysisResult | None,
    *,
    workspace_key: str = "insights",
) -> None:
    st.header("AI-Powered Business Insights")

    if analysis is None:
        st.info(
            "Run Phase 4 analysis first. AI insights will use its "
            "calculated KPIs, trends, grouped summaries and findings."
        )
        return

    st.warning(
        "AI-generated interpretations are suggestions, not verified "
        "business facts or automatic decisions. Review each cited item."
    )

    business_context = st.text_area(
        "Optional business context",
        placeholder=(
            "Example: Analyze regional retail performance and identify "
            "areas that deserve further investigation."
        ),
        max_chars=1500,
        key=f"{workspace_key}_business_context",
    )

    if not st.button(
        "Generate AI insights",
        type="primary",
        key=f"{workspace_key}_generate",
    ):
        return

    try:
        settings = InsightSettings.from_env()
        settings.validate()
        report = InsightEngine(settings=settings).generate(
            analysis,
            business_context=business_context,
        )
    except (ValueError, ProviderError, InsightValidationError) as exc:
        st.error(f"Insights could not be generated: {exc}")
        return

    report_data = report.model_dump(mode="json")
    st.session_state[f"{workspace_key}_report"] = report_data

    st.subheader("Executive summary")
    st.write(report.executive_summary)

    st.subheader("Insights and recommendations")
    if not report.insights:
        st.info("The model did not return any validated insights.")

    for index, insight in enumerate(report.insights, start=1):
        with st.expander(f"{index}. {insight.title}", expanded=index == 1):
            st.markdown("**What the evidence shows**")
            st.write(insight.observation)

            st.markdown("**Potential business implication**")
            st.write(insight.business_implication)

            st.markdown("**Recommended next step**")
            st.write(insight.recommendation)

            st.markdown("**Evidence references**")
            st.write(", ".join(insight.evidence_refs))

            st.markdown("**Success metric**")
            st.write(insight.success_metric)

            st.caption(
                f"Priority: {insight.priority} · "
                f"Confidence: {insight.confidence} · "
                "Human review required"
            )

            if insight.validation_notes:
                st.markdown("**Validation notes**")
                for note in insight.validation_notes:
                    st.write(f"- {note}")

    if report.overall_limitations:
        st.subheader("Limitations")
        for limitation in report.overall_limitations:
            st.write(f"- {limitation}")

    st.download_button(
        "Download validated insights (JSON)",
        data=json.dumps(report_data, indent=2, ensure_ascii=False),
        file_name="ai_business_insights.json",
        mime="application/json",
        key=f"{workspace_key}_download",
    )
