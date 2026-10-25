import pandas as pd
import pytest

from business_analyst.security.limits import (
    ResourceLimitError,
    ResourceLimits,
    validate_dataframe_size,
    validate_upload_size,
)


def test_upload_within_limit_is_accepted():
    limits = ResourceLimits(max_upload_bytes=100)
    validate_upload_size(100, limits)


def test_oversized_upload_is_rejected():
    limits = ResourceLimits(max_upload_bytes=100)

    with pytest.raises(ResourceLimitError):
        validate_upload_size(101, limits)


def test_negative_upload_size_is_rejected():
    with pytest.raises(ResourceLimitError):
        validate_upload_size(-1)


def test_dataframe_within_limits_is_accepted():
    dataframe = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    limits = ResourceLimits(
        max_rows=10,
        max_columns=5,
        max_cells=50,
    )

    validate_dataframe_size(dataframe, limits)


def test_dataframe_row_limit_is_enforced():
    dataframe = pd.DataFrame({"a": range(11)})
    limits = ResourceLimits(max_rows=10)

    with pytest.raises(ResourceLimitError):
        validate_dataframe_size(dataframe, limits)


def test_dataframe_cell_limit_is_enforced():
    dataframe = pd.DataFrame([[1, 2, 3], [4, 5, 6]])
    limits = ResourceLimits(
        max_rows=10,
        max_columns=10,
        max_cells=5,
    )

    with pytest.raises(ResourceLimitError):
        validate_dataframe_size(dataframe, limits)


def test_invalid_resource_configuration_is_rejected():
    with pytest.raises(ValueError):
        ResourceLimits(max_rows=0)
