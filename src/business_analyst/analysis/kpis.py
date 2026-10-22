"""Configurable business KPI calculations."""

from __future__ import annotations

import pandas as pd

from business_analyst.analysis.models import KPIResult


def _sum_numeric(dataframe: pd.DataFrame, column: str) -> float | None:
    if column not in dataframe.columns:
        return None
    if not pd.api.types.is_numeric_dtype(dataframe[column]):
        return None

    values = dataframe[column].dropna()
    return float(values.sum()) if not values.empty else None


def calculate_kpis(
    dataframe: pd.DataFrame,
    *,
    revenue_column: str | None = None,
    profit_column: str | None = None,
    order_id_column: str | None = None,
    quantity_column: str | None = None,
) -> list[KPIResult]:
    results: list[KPIResult] = []

    revenue = _sum_numeric(dataframe, revenue_column) if revenue_column else None
    profit = _sum_numeric(dataframe, profit_column) if profit_column else None

    if revenue_column:
        results.append(
            KPIResult(
                name="Total revenue",
                value=revenue,
                description=f"Sum of {revenue_column}.",
                format="currency",
                status="ok" if revenue is not None else "unavailable",
            )
        )

    if profit_column:
        results.append(
            KPIResult(
                name="Total profit",
                value=profit,
                description=f"Sum of {profit_column}.",
                format="currency",
                status="ok" if profit is not None else "unavailable",
            )
        )

    if revenue_column and profit_column:
        if revenue is None or profit is None:
            results.append(
                KPIResult(
                    name="Profit margin",
                    value=None,
                    description="Total profit divided by total revenue.",
                    format="percentage",
                    status="unavailable",
                )
            )
        elif revenue == 0:
            results.append(
                KPIResult(
                    name="Profit margin",
                    value=None,
                    description="Total profit divided by total revenue.",
                    format="percentage",
                    numerator=profit,
                    denominator=revenue,
                    status="undefined",
                )
            )
        else:
            results.append(
                KPIResult(
                    name="Profit margin",
                    value=profit / revenue * 100,
                    description="Total profit divided by total revenue.",
                    format="percentage",
                    numerator=profit,
                    denominator=revenue,
                )
            )

    if order_id_column:
        if order_id_column in dataframe.columns:
            results.append(
                KPIResult(
                    name="Distinct orders",
                    value=int(dataframe[order_id_column].nunique(dropna=True)),
                    description=f"Unique non-missing values in {order_id_column}.",
                )
            )
        else:
            results.append(
                KPIResult(
                    name="Distinct orders",
                    value=None,
                    description=f"Column {order_id_column} was not found.",
                    status="unavailable",
                )
            )

    if quantity_column:
        quantity = _sum_numeric(dataframe, quantity_column)
        results.append(
            KPIResult(
                name="Total quantity",
                value=quantity,
                description=f"Sum of {quantity_column}.",
                status="ok" if quantity is not None else "unavailable",
            )
        )

    if revenue_column and order_id_column:
        orders = (
            dataframe[order_id_column].nunique(dropna=True)
            if order_id_column in dataframe.columns
            else 0
        )
        average_order_value = (
            revenue / orders if revenue is not None and orders > 0 else None
        )
        results.append(
            KPIResult(
                name="Average order value",
                value=average_order_value,
                description="Total revenue divided by distinct orders.",
                format="currency",
                numerator=revenue,
                denominator=float(orders),
                status=(
                    "ok"
                    if average_order_value is not None
                    else "undefined"
                    if revenue is not None
                    else "unavailable"
                ),
            )
        )

    return results
