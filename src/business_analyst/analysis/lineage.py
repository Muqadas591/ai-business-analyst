"""Dataset preparation lineage for downstream analysis."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pandas as pd


def dataframe_fingerprint(dataframe: pd.DataFrame) -> str:
    """Return a deterministic fingerprint for the current DataFrame."""
    hashed_rows = pd.util.hash_pandas_object(dataframe, index=True).values.tobytes()

    metadata = json.dumps(
        {
            "columns": [str(column) for column in dataframe.columns],
            "dtypes": [str(dtype) for dtype in dataframe.dtypes],
            "shape": list(dataframe.shape),
        },
        sort_keys=True,
    ).encode("utf-8")

    digest = hashlib.sha256()
    digest.update(metadata)
    digest.update(hashed_rows)
    return digest.hexdigest()


def build_lineage(
    original: pd.DataFrame,
    analyzed: pd.DataFrame,
    *,
    audit_trail: list[dict[str, Any]] | None = None,
    quality_comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "original_fingerprint": dataframe_fingerprint(original),
        "analyzed_fingerprint": dataframe_fingerprint(analyzed),
        "original_shape": {
            "rows": int(original.shape[0]),
            "columns": int(original.shape[1]),
        },
        "analyzed_shape": {
            "rows": int(analyzed.shape[0]),
            "columns": int(analyzed.shape[1]),
        },
        "audit_trail": audit_trail or [],
        "quality_comparison": quality_comparison or {},
        "lineage_status": (
            "same_dataset"
            if dataframe_fingerprint(original) == dataframe_fingerprint(analyzed)
            else "transformed_dataset"
        ),
    }
