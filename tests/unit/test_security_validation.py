import pytest

from business_analyst.security.validation import (
    InputValidationError,
    validate_dataset_id,
    validate_filename,
    validate_workspace_name,
)


def test_workspace_name_is_trimmed():
    assert validate_workspace_name("  Retail Analytics  ") == ("Retail Analytics")


@pytest.mark.parametrize("value", ["", "   ", None])
def test_invalid_workspace_names_are_rejected(value):
    with pytest.raises(InputValidationError):
        validate_workspace_name(value)


def test_workspace_name_length_is_limited():
    with pytest.raises(InputValidationError):
        validate_workspace_name("x" * 121)


def test_dataset_id_is_normalized():
    dataset_id = "550E8400-E29B-41D4-A716-446655440000"
    assert validate_dataset_id(dataset_id) == dataset_id.lower()


@pytest.mark.parametrize(
    "value",
    [
        "../secret.csv",
        "..\\secret.csv",
        "/etc/passwd",
        "",
        "data.txt",
        "report.csv\n",
    ],
)
def test_unsafe_filenames_are_rejected(value):
    with pytest.raises(InputValidationError):
        validate_filename(value)


@pytest.mark.parametrize(
    "value",
    [
        "retail.csv",
        "retail.xlsx",
        "retail.xls",
    ],
)
def test_supported_filenames_are_accepted(value):
    assert validate_filename(value) == value
