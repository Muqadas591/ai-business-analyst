import json

import pandas as pd

from business_analyst.analysis.engine import AnalysisEngine
from business_analyst.insights.config import InsightSettings
from business_analyst.insights.engine import InsightEngine


class FakeProvider:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = json.loads(user_prompt)
        evidence = payload["evidence"]
        assert evidence

        return json.dumps(
            {
                "executive_summary": (
                    "The report explains the supplied calculated evidence."
                ),
                "insights": [
                    {
                        "title": "Review calculated revenue",
                        "observation": (
                            "The revenue KPI is available in the supplied evidence."
                        ),
                        "business_implication": (
                            "The KPI may help prioritize a closer business review."
                        ),
                        "evidence_refs": [evidence[0]["evidence_id"]],
                        "recommendation": (
                            "Review this KPI alongside operational and business context."
                        ),
                        "priority": "medium",
                        "confidence": "medium",
                        "validation_notes": ["Interpretation requires human review."],
                        "success_metric": "Monitor the same calculated KPI.",
                        "human_review_required": True,
                    }
                ],
                "overall_limitations": [
                    "Descriptive metrics do not prove business causation."
                ],
            }
        )


def test_engine_uses_provider_and_validates_response():
    dataframe = pd.DataFrame({"revenue": [100.0, 200.0]})
    analysis = AnalysisEngine().run(
        dataframe,
        revenue_column="revenue",
    )
    settings = InsightSettings(
        provider="openai_compatible",
        base_url="https://provider.example/v1",
        api_key="test-key",
        model="test-model",
    )

    report = InsightEngine(
        provider=FakeProvider(),
        settings=settings,
    ).generate(analysis)

    assert report.insights
    assert report.insights[0].human_review_required is True
