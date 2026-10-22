import pandas as pd
import pytest

from business_analyst.analysis.correlations import calculate_correlations
from business_analyst.analysis.engine import AnalysisEngine
from business_analyst.analysis.kpis import calculate_kpis
from business_analyst.analysis.profiles import (
    categorical_profiles,
    numeric_profiles,
)
from business_analyst.analysis.trends import calculate_trend


def sample_data():
    return pd.DataFrame(
        {
            "order_id": [1, 2, 3, 4],
            "date": pd.to_datetime(
                [
                    "2026-01-05",
                    "2026-01-20",
                    "2026-02-05",
                    "2026-02-20",
                ]
            ),
            "revenue": [100.0, 200.0, 150.0, 250.0],
            "profit": [20.0, 40.0, 30.0, 50.0],
            "region": ["North", "South", "North", "South"],
        }
    )


def test_numeric_profiles_include_missing_counts():
    dataframe = pd.DataFrame({"amount": [10.0, None, 30.0]})

    result = numeric_profiles(dataframe)

    assert result["amount"]["count"] == 2
    assert result["amount"]["missing_count"] == 1
    assert result["amount"]["median"] == 20.0


def test_categorical_profiles_are_ranked_by_frequency():
    dataframe = pd.DataFrame({"region": ["North", "South", "North"]})

    result = categorical_profiles(dataframe)

    assert result["region"][0]["category"] == "North"
    assert result["region"][0]["count"] == 2


def test_revenue_profit_margin_and_average_order_value():
    result = calculate_kpis(
        sample_data(),
        revenue_column="revenue",
        profit_column="profit",
        order_id_column="order_id",
    )

    values = {item.name: item for item in result}

    assert values["Total revenue"].value == 700.0
    assert values["Total profit"].value == 140.0
    assert values["Profit margin"].value == pytest.approx(20.0)
    assert values["Average order value"].value == pytest.approx(175.0)


def test_profit_margin_is_undefined_when_revenue_is_zero():
    dataframe = pd.DataFrame(
        {
            "revenue": [0.0, 0.0],
            "profit": [10.0, -10.0],
        }
    )

    result = calculate_kpis(
        dataframe,
        revenue_column="revenue",
        profit_column="profit",
    )

    margin = next(item for item in result if item.name == "Profit margin")

    assert margin.value is None
    assert margin.status == "undefined"


def test_monthly_trend_has_period_changes():
    result = calculate_trend(sample_data(), "date", "revenue", frequency="M")

    assert len(result) == 2
    assert result[0]["value"] == 300.0
    assert result[1]["value"] == 400.0
    assert result[1]["change"] == 100.0
    assert result[1]["change_pct"] == pytest.approx(100 / 3)


def test_correlation_is_association_not_causation():
    result = calculate_correlations(sample_data())

    revenue_profit = next(
        row
        for row in result
        if {row["column_a"], row["column_b"]} == {"revenue", "profit"}
    )

    assert revenue_profit["correlation"] == pytest.approx(1.0)
    assert "does not establish causation" in revenue_profit["interpretation"]


def test_analysis_does_not_mutate_source_dataframe():
    dataframe = sample_data()
    original = dataframe.copy(deep=True)

    AnalysisEngine().run(
        dataframe,
        revenue_column="revenue",
        profit_column="profit",
    )

    pd.testing.assert_frame_equal(dataframe, original)


def test_empty_dataset_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        AnalysisEngine().run(pd.DataFrame({"revenue": []}))
