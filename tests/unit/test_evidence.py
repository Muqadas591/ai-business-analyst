import pandas as pd

from business_analyst.analysis.engine import AnalysisEngine
from business_analyst.insights.evidence import build_evidence_packet


def test_evidence_packet_has_stable_ids_for_identical_results():
    dataframe = pd.DataFrame(
        {
            "revenue": [100.0, 200.0],
            "profit": [20.0, 40.0],
        }
    )
    analysis = AnalysisEngine().run(
        dataframe,
        revenue_column="revenue",
        profit_column="profit",
    )

    first = build_evidence_packet(analysis)
    second = build_evidence_packet(analysis)

    assert [item.evidence_id for item in first] == [item.evidence_id for item in second]
    assert first


def test_evidence_packet_does_not_include_raw_rows():
    dataframe = pd.DataFrame(
        {
            "revenue": [100.0, 200.0],
            "customer_email": ["private1@example.test", "private2@example.test"],
        }
    )
    analysis = AnalysisEngine().run(
        dataframe,
        revenue_column="revenue",
    )

    evidence = build_evidence_packet(analysis)
    serialized = " ".join(item.model_dump_json() for item in evidence)

    assert "private1@example.test" not in serialized
    assert "private2@example.test" not in serialized
