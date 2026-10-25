"""Tests for product overview data extraction."""

from types import SimpleNamespace

from business_analyst.product_dashboard import _get_insights, _get_kpis


def test_kpi_extraction_returns_existing_kpis() -> None:
    expected = [SimpleNamespace(name="Revenue"), SimpleNamespace(name="Profit")]
    analysis_result = SimpleNamespace(kpis=expected)

    assert _get_kpis(analysis_result) == expected


def test_missing_analysis_returns_empty_kpi_list() -> None:
    assert _get_kpis(None) == []


def test_insight_extraction_returns_existing_insights() -> None:
    expected = [SimpleNamespace(title="Revenue increased")]
    report = SimpleNamespace(insights=expected)

    assert _get_insights(report) == expected


def test_missing_insight_report_returns_empty_list() -> None:
    assert _get_insights(None) == []