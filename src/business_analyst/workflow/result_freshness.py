"""Helpers for associating workflow results with the data that produced them."""

from __future__ import annotations

from collections.abc import MutableMapping

import pandas as pd
from pandas.util import hash_pandas_object


RESULT_KEYS = (
    "analysis_result",
    "insight_report",
    "report_artifacts",
)


def dataframe_fingerprint(dataframe: pd.DataFrame) -> str:
    """Create a stable fingerprint for the current in-memory dataframe."""
    digest = hash_pandas_object(dataframe, index=True).values.tobytes()

    import hashlib
    import json

    hasher = hashlib.sha256()
    hasher.update(
        json.dumps(
            [str(column) for column in dataframe.columns],
            ensure_ascii=False,
        ).encode("utf-8")
    )
    hasher.update(digest)

    return hasher.hexdigest()


def clear_stale_results(
    state: MutableMapping[str, object],
    *,
    current_fingerprint: str,
    fingerprint_key: str,
    result_keys: tuple[str, ...] = RESULT_KEYS,
) -> bool:
    """Clear downstream results when the source dataframe changes.

    Returns True when stale results were cleared.
    """
    previous_fingerprint = state.get(fingerprint_key)

    if previous_fingerprint is None:
        state[fingerprint_key] = current_fingerprint
        return False

    if previous_fingerprint == current_fingerprint:
        return False

    for key in result_keys:
        state.pop(key, None)

    state[fingerprint_key] = current_fingerprint
    return True