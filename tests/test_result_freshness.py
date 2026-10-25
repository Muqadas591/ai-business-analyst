"""Tests for source-version tracking and stale result invalidation."""

import pandas as pd

from business_analyst.workflow.result_freshness import (
    clear_stale_results,
    dataframe_fingerprint,
)


def test_identical_data_does_not_clear_results() -> None:
    dataframe = pd.DataFrame(
        {"Order ID": ["O-1", "O-2"], "Revenue": [100.0, 200.0]}
    )
    fingerprint = dataframe_fingerprint(dataframe)

    state = {
        "dataset_fingerprint": fingerprint,
        "analysis_result": {"revenue": 300.0},
        "insight_report": {"summary": "Synthetic summary"},
    }

    cleared = clear_stale_results(
        state,
        current_fingerprint=dataframe_fingerprint(dataframe.copy()),
        fingerprint_key="dataset_fingerprint",
    )

    assert cleared is False
    assert "analysis_result" in state
    assert "insight_report" in state


def test_changed_data_clears_downstream_results() -> None:
    original = pd.DataFrame(
        {"Order ID": ["O-1", "O-2"], "Revenue": [100.0, 200.0]}
    )
    changed = original.copy()
    changed.loc[0, "Revenue"] = 150.0

    state = {
        "dataset_fingerprint": dataframe_fingerprint(original),
        "analysis_result": {"revenue": 300.0},
        "insight_report": {"summary": "Old summary"},
        "report_artifacts": {"pdf_bytes": b"old report"},
    }

    cleared = clear_stale_results(
        state,
        current_fingerprint=dataframe_fingerprint(changed),
        fingerprint_key="dataset_fingerprint",
    )

    assert cleared is True
    assert "analysis_result" not in state
    assert "insight_report" not in state
    assert "report_artifacts" not in state


def test_first_fingerprint_does_not_clear_unrelated_state() -> None:
    dataframe = pd.DataFrame({"Revenue": [10.0, 20.0]})
    state = {"unrelated_setting": "preserved"}

    cleared = clear_stale_results(
        state,
        current_fingerprint=dataframe_fingerprint(dataframe),
        fingerprint_key="dataset_fingerprint",
    )

    assert cleared is False
    assert state["unrelated_setting"] == "preserved"
    assert "dataset_fingerprint" in state