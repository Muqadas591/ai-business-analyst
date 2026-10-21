
"""Generate reproducible synthetic retail data for development and demos."""

from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd


def generate_retail_sales(
    rows: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate deterministic synthetic retail transactions."""
    if rows < 1:
        raise ValueError("rows must be at least 1")

    rng = np.random.default_rng(seed)

    products = np.array(
        ["Laptop", "Monitor", "Keyboard", "Mouse", "Headphones"]
    )
    regions = np.array(
        ["North", "South", "East", "West", "Central"]
    )

    product_prices = {
        "Laptop": 850.0,
        "Monitor": 240.0,
        "Keyboard": 45.0,
        "Mouse": 25.0,
        "Headphones": 80.0,
    }

    product_cost_ratios = {
        "Laptop": 0.76,
        "Monitor": 0.70,
        "Keyboard": 0.55,
        "Mouse": 0.45,
        "Headphones": 0.60,
    }

    product = rng.choice(products, size=rows)
    quantity = rng.integers(1, 11, size=rows)
    region = rng.choice(regions, size=rows)
    unit_price = np.array([product_prices[p] for p in product])
    cost_ratio = np.array([product_cost_ratios[p] for p in product])

    discount = rng.choice(
        [0.0, 0.05, 0.10, 0.15],
        size=rows,
        p=[0.55, 0.20, 0.20, 0.05],
    )

    revenue = quantity * unit_price * (1.0 - discount)
    cost = quantity * unit_price * cost_ratio
    profit = revenue - cost

    dates = (
        pd.Timestamp("2025-01-01")
        + pd.to_timedelta(
            rng.integers(0, 365, size=rows),
            unit="D",
        )
    )

    return pd.DataFrame(
        {
            "order_id": [f"ORD-{i:06d}" for i in range(1, rows + 1)],
            "order_date": dates,
            "region": region,
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price.round(2),
            "discount_rate": discount,
            "revenue": revenue.round(2),
            "cost": cost.round(2),
            "profit": profit.round(2),
        }
    )


def retail_sales_csv_bytes(
    rows: int = 500,
    seed: int = 42,
) -> bytes:
    """Return synthetic retail data encoded as UTF-8 CSV bytes."""
    dataframe = generate_retail_sales(rows=rows, seed=seed)
    return dataframe.to_csv(index=False).encode("utf-8")


def retail_sales_excel_bytes(
    rows: int = 500,
    seed: int = 42,
) -> bytes:
    """Return synthetic retail data as an in-memory XLSX workbook."""
    dataframe = generate_retail_sales(rows=rows, seed=seed)
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(
            writer,
            sheet_name="Sales",
            index=False,
        )
        dataframe.head(20).to_excel(
            writer,
            sheet_name="Preview",
            index=False,
        )

    return buffer.getvalue()


def retail_sales_csv_text(
    rows: int = 500,
    seed: int = 42,
) -> str:
    """Return a text representation for quick inspection."""
    dataframe = generate_retail_sales(rows=rows, seed=seed)
    return dataframe.to_csv(index=False)


if __name__ == "__main__":
    print(generate_retail_sales(rows=5).to_string(index=False))
