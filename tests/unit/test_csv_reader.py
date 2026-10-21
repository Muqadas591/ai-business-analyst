"""Tests for CSV ingestion."""

import pytest

from business_analyst.exceptions import (
    DuplicateHeaderError,
    EmptyDatasetError,
    EmptyFileError,
    InvalidFileError,
    RowLimitError,
)
from business_analyst.ingestion.csv_reader import read_csv_bytes


def test_reads_valid_csv(csv_bytes, test_settings) -> None:
    dataframe, encoding, delimiter = read_csv_bytes(
        csv_bytes,
        test_settings,
    )

    assert dataframe.shape == (2, 3)
    assert list(dataframe.columns) == ["order_id", "region", "revenue"]
    assert encoding in {"utf-8-sig", "utf-8", "cp1252", "latin-1"}
    assert delimiter == ","


def test_reads_semicolon_delimited_csv(test_settings) -> None:
    payload = b"name;revenue\nA;100\nB;200\n"

    dataframe, _, delimiter = read_csv_bytes(payload, test_settings)

    assert delimiter == ";"
    assert dataframe.shape == (2, 2)


def test_reads_utf8_bom(test_settings) -> None:
    payload = "\ufeffname,revenue\nA,100\n".encode("utf-8")

    dataframe, encoding, _ = read_csv_bytes(payload, test_settings)

    assert dataframe.columns[0] == "name"
    assert encoding == "utf-8-sig"


def test_rejects_empty_csv(test_settings) -> None:
    with pytest.raises(EmptyFileError):
        read_csv_bytes(b"", test_settings)


def test_rejects_header_only_csv(test_settings) -> None:
    with pytest.raises(EmptyDatasetError):
        read_csv_bytes(b"name,revenue\n", test_settings)


def test_rejects_duplicate_headers(test_settings) -> None:
    payload = b"revenue,revenue\n100,200\n"

    with pytest.raises(DuplicateHeaderError):
        read_csv_bytes(payload, test_settings)


def test_rejects_malformed_csv(test_settings) -> None:
    payload = b'name,revenue\n"A,100\n"B,200\n'

    with pytest.raises(InvalidFileError):
        read_csv_bytes(payload, test_settings)


def test_rejects_excess_rows(test_settings) -> None:
    payload = b"name,value\nA,1\nB,2\nC,3\nD,4\nE,5\nF,6\n"

    with pytest.raises(RowLimitError):
        read_csv_bytes(payload, test_settings)
