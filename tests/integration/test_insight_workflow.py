import json

import pandas as pd

from business_analyst.analysis.engine import AnalysisEngine
from business_analyst.insights.config import InsightSettings
from business_analyst.insights.engine import InsightEngine


class EvidenceAwareFakeProvider:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        evidence = json.loads(user_prompt)["evidence"]
        kpi = next(item for item in evidence if item["kind"] == "kpi")

        return json.dumps(
            {
                "executive_summary": (
                    "The report describes the available retail evidence."
                ),
                "insights": [
                    {
                        "title": "Review revenue and profit",
                        "observation": (
                            "The revenue and profit KPIs are calculated by Python."
                        ),
                        "business_implication": (
                            "A manager can review these metrics with relevant context."
                        ),
                        "evidence_refs": [kpi["evidence_id"]],
                        "recommendation": (
                            "Compare these metrics with the organization's targets."
                        ),
                        "priority": "medium",
                        "confidence": "medium",
                        "validation_notes": [],
                        "success_metric": "Monitor the selected KPI.",
                        "human_review_required": True,
                    }
                ],
                "overall_limitations": ["The report does not establish causation."],
            }
        )


def test_phase4_results_can_feed_phase5():
    retail = pd.DataFrame(
        {
            "order_id": [1, 2, 3],
            "revenue": [100.0, 200.0, 300.0],
            "profit": [20.0, 40.0, 60.0],
            "region": ["North", "South", "North"],
        }
    )

    analysis = AnalysisEngine().run(
        retail,
        dataset_id="synthetic-retail-test",
        revenue_column="revenue",
        profit_column="profit",
        order_id_column="order_id",
        group_column="region",
        group_metric_column="revenue",
    )

    settings = InsightSettings(
        provider="openai_compatible",
        base_url="https://provider.example/v1",
        api_key="test-key",
        model="test-model",
    )

    report = InsightEngine(
        provider=EvidenceAwareFakeProvider(),
        settings=settings,
    ).generate(analysis)

    assert report.insights[0].evidence_refs
    assert report.insights[0].human_review_required
