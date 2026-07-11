"""Tests for plotforge.data.loader: parsing, sheets, inference, errors."""

from __future__ import annotations

import pandas as pd
import pytest

from plotforge.data import loader
from tests.conftest import as_upload_payload

# ---------------------------------------------------------------------------
# Happy paths: csv / tsv / xlsx
# ---------------------------------------------------------------------------


def test_load_csv(fixtures_dir):
    raw = (fixtures_dir / "sample.csv").read_bytes()
    df = loader.load_dataframe(raw, "sample.csv")
    assert df.shape == (40, 6)
    assert list(df.columns)[:2] == ["dose", "response"]


def test_load_tsv(fixtures_dir):
    raw = (fixtures_dir / "sample.tsv").read_bytes()
    df = loader.load_dataframe(raw, "sample.tsv")
    assert df.shape == (40, 6)


def test_load_xlsx_default_sheet(fixtures_dir):
    raw = (fixtures_dir / "sample.xlsx").read_bytes()
    df = loader.load_dataframe(raw, "sample.xlsx")
    assert "dose" in df.columns  # first sheet is 'measurements'


def test_load_xlsx_named_sheet(fixtures_dir):
    raw = (fixtures_dir / "sample.xlsx").read_bytes()
    df = loader.load_dataframe(raw, "sample.xlsx", sheet="matrix")
    assert "row_label" in df.columns


def test_list_sheets(fixtures_dir):
    raw = (fixtures_dir / "sample.xlsx").read_bytes()
    assert loader.list_sheets(raw, "sample.xlsx") == ["measurements", "matrix"]


def test_list_sheets_none_for_csv(fixtures_dir):
    raw = (fixtures_dir / "sample.csv").read_bytes()
    assert loader.list_sheets(raw, "sample.csv") is None


def test_parse_upload_roundtrip(fixtures_dir):
    payload = as_upload_payload(fixtures_dir / "sample.csv")
    df, sheets = loader.parse_upload(payload, "sample.csv")
    assert df.shape == (40, 6)
    assert sheets is None


# ---------------------------------------------------------------------------
# Failure modes: friendly LoaderError, never a raw traceback type
# ---------------------------------------------------------------------------


def test_unsupported_extension():
    with pytest.raises(loader.LoaderError, match="Unsupported file type"):
        loader.file_family("data.parquet")


def test_malformed_binary_file(fixtures_dir):
    raw = (fixtures_dir / "malformed.csv").read_bytes()
    with pytest.raises(loader.LoaderError):
        loader.load_dataframe(raw, "malformed.csv")


def test_empty_table(fixtures_dir):
    raw = (fixtures_dir / "empty.csv").read_bytes()
    with pytest.raises(loader.LoaderError, match="contains no data"):
        loader.load_dataframe(raw, "empty.csv")


def test_bad_base64_payload():
    with pytest.raises(loader.LoaderError, match="decode"):
        loader.decode_upload("this-is-not-a-payload")


def test_excel_junk_bytes():
    with pytest.raises(loader.LoaderError):
        loader.list_sheets(b"\x00\x01junk", "fake.xlsx")


# ---------------------------------------------------------------------------
# Column type inference
# ---------------------------------------------------------------------------


def test_infer_column_types(fixtures_dir):
    raw = (fixtures_dir / "sample.csv").read_bytes()
    df = loader.load_dataframe(raw, "sample.csv")
    types = loader.infer_column_types(df)
    assert types["dose"] == "numeric"
    assert types["response"] == "numeric"
    assert types["group"] == "categorical"
    assert types["measured_on"] == "datetime"  # string column of ISO dates


def test_numeric_strings_are_not_datetime():
    s = pd.Series(["2021", "2022", "1999", "15"])
    assert not loader._looks_like_datetime(s)


def test_coerce_datetime_columns(fixtures_dir):
    raw = (fixtures_dir / "sample.csv").read_bytes()
    df = loader.load_dataframe(raw, "sample.csv")
    types = loader.infer_column_types(df)
    out = loader.coerce_datetime_columns(df, types)
    assert pd.api.types.is_datetime64_any_dtype(out["measured_on"])
    # Original frame is untouched (copy-on-write semantics).
    assert not pd.api.types.is_datetime64_any_dtype(df["measured_on"])


def test_summarize(fixtures_dir):
    raw = (fixtures_dir / "sample.csv").read_bytes()
    df = loader.load_dataframe(raw, "sample.csv")
    types = loader.infer_column_types(df)
    info = loader.summarize(df, types)
    assert info["rows"] == 40
    assert info["cols"] == 6
    assert {c["name"] for c in info["columns"]} == set(df.columns)
