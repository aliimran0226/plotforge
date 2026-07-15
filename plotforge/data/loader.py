"""File parsing for uploaded data.

Turns the base64 payload from ``dcc.Upload`` into a pandas DataFrame:
CSV, TSV, and Excel (``.xlsx``/``.xls``) are supported, including
multi-sheet workbooks. Also infers a coarse per-column type
(numeric / categorical / datetime) used by the mapping UI to label
column dropdowns.

All failures raise ``LoaderError`` with a message written for the end
user - callbacks display it verbatim in an alert.
"""

from __future__ import annotations

import base64
import csv
import io

import pandas as pd

from plotforge import config

#: Extensions we accept, mapped to a human-readable family name.
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".csv": "csv",
    ".tsv": "tsv",
    ".txt": "csv",  # treated as delimited text; separator is sniffed
    ".xlsx": "excel",
    ".xls": "excel",
}


class LoaderError(Exception):
    """A parsing problem with a message suitable for showing to the user."""


def _extension(filename: str) -> str:
    """Return the lowercased extension of ``filename`` (with the dot)."""
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot != -1 else ""


def file_family(filename: str) -> str:
    """Classify a filename as 'csv', 'tsv', or 'excel'.

    Raises:
        LoaderError: If the extension is not supported.
    """
    ext = _extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise LoaderError(
            f"Unsupported file type {ext or '(no extension)'!r} for "
            f"'{filename}'. Supported formats: {supported}."
        )
    return SUPPORTED_EXTENSIONS[ext]


def decode_upload(contents: str) -> bytes:
    """Decode the ``dcc.Upload`` payload ('data:<mime>;base64,<data>') to bytes.

    Raises:
        LoaderError: If the payload is not valid base64.
    """
    try:
        _, b64 = contents.split(",", 1)
        return base64.b64decode(b64)
    except (ValueError, base64.binascii.Error) as exc:
        raise LoaderError(
            "Could not decode the uploaded file. Please try uploading again."
        ) from exc


def list_sheets(raw: bytes, filename: str) -> list[str] | None:
    """Return sheet names for Excel files, or ``None`` for flat text files.

    Raises:
        LoaderError: If the workbook cannot be opened.
    """
    if file_family(filename) != "excel":
        return None
    try:
        with pd.ExcelFile(io.BytesIO(raw)) as xls:
            return [str(s) for s in xls.sheet_names]
    except Exception as exc:
        raise LoaderError(
            f"Could not open '{filename}' as an Excel workbook. "
            "Make sure the file is not corrupted or password-protected."
        ) from exc


def _sniff_separator(raw: bytes) -> str:
    """Detect the delimiter of a text file, restricted to sane candidates.

    ``pd.read_csv(sep=None)`` sniffs over *any* character, which mangles
    single-column files (it can pick a letter as the delimiter). Sniff
    over the usual suspects only and fall back to ',' - a comma is
    harmless for a single-column file.
    """
    sample = raw[:8192].decode("utf-8", errors="replace")
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def load_dataframe(raw: bytes, filename: str, sheet: str | None = None) -> pd.DataFrame:
    """Parse raw file bytes into a DataFrame.

    Args:
        raw: The decoded file contents.
        filename: Original filename (used to pick the parser).
        sheet: Sheet name for Excel files; ignored for text files.
               Defaults to the first sheet.

    Returns:
        The parsed DataFrame with a plain RangeIndex.

    Raises:
        LoaderError: On any parse failure or an empty table.
    """
    family = file_family(filename)
    try:
        if family == "excel":
            df = pd.read_excel(io.BytesIO(raw), sheet_name=sheet if sheet else 0)
        elif family == "tsv":
            df = pd.read_csv(io.BytesIO(raw), sep="\t")
        else:  # csv / txt: sniff the separator (handles ';', '\t', '|')
            df = pd.read_csv(io.BytesIO(raw), sep=_sniff_separator(raw))
    except LoaderError:
        raise
    except UnicodeDecodeError as exc:
        raise LoaderError(
            f"Could not read '{filename}': the file is not valid text "
            "(UTF-8). If it is an Excel file, make sure it has an .xlsx "
            "or .xls extension."
        ) from exc
    except Exception as exc:
        raise LoaderError(
            f"Could not parse '{filename}': {exc}. Check that the file has "
            "a header row and consistent columns."
        ) from exc

    if df.empty or df.shape[1] == 0:
        raise LoaderError(
            f"'{filename}' parsed successfully but contains no data. "
            "Make sure the file (or selected sheet) has a header row and "
            "at least one row of values."
        )

    # Column names must be strings for Dash dropdowns / dash_table.
    df.columns = [str(c) for c in df.columns]
    return df.reset_index(drop=True)


def parse_upload(
    contents: str, filename: str, sheet: str | None = None
) -> tuple[pd.DataFrame, list[str] | None]:
    """Convenience wrapper: decode + parse an upload in one call.

    Returns:
        ``(dataframe, sheet_names)`` where ``sheet_names`` is ``None``
        for non-Excel files.
    """
    raw = decode_upload(contents)
    sheets = list_sheets(raw, filename)
    df = load_dataframe(raw, filename, sheet=sheet)
    return df, sheets


# ---------------------------------------------------------------------------
# Column type inference
# ---------------------------------------------------------------------------


def infer_column_types(df: pd.DataFrame) -> dict[str, str]:
    """Classify each column as 'numeric', 'datetime', or 'categorical'.

    The mapping UI uses these labels to annotate column dropdowns and
    plots use them to pick sensible defaults. Rules:

    - numeric dtypes -> 'numeric'
    - datetime dtypes -> 'datetime'
    - string columns where >90% of non-null values parse as dates
      -> 'datetime' (common for CSV, which has no date type)
    - everything else (strings, booleans, categoricals) -> 'categorical'
    """
    types: dict[str, str] = {}
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            types[col] = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(s):
            types[col] = "datetime"
        elif _looks_like_datetime(s):
            types[col] = "datetime"
        else:
            types[col] = "categorical"
    return types


def _looks_like_datetime(s: pd.Series) -> bool:
    """True if a string column is mostly parseable as dates.

    Checks at most 200 non-null values to stay fast on large files and
    requires >90% of them to parse, so ID-like or free-text columns
    aren't misclassified.
    """
    sample = s.dropna()
    if sample.empty:
        return False
    sample = sample.head(200).astype(str)
    # Purely numeric strings ('2023', '15') parse as dates but almost
    # never are; treat them as not-datetime.
    if sample.str.fullmatch(r"[\d.]+").all():
        return False
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return parsed.notna().mean() > 0.9


def coerce_datetime_columns(df: pd.DataFrame, types: dict[str, str]) -> pd.DataFrame:
    """Convert columns inferred as datetime to real datetime dtype.

    Returns a copy only when a conversion happens. Values that fail to
    parse become NaT rather than raising - by this point the column is
    known to be >90% parseable.
    """
    converted = df
    for col, kind in types.items():
        if kind == "datetime" and not pd.api.types.is_datetime64_any_dtype(df[col]):
            if converted is df:
                converted = df.copy()
            converted[col] = pd.to_datetime(
                converted[col], errors="coerce", format="mixed"
            )
    return converted


def summarize(df: pd.DataFrame, types: dict[str, str]) -> dict[str, object]:
    """Small summary dict used by the UI (row/column counts, dtypes)."""
    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "columns": [{"name": c, "type": types[c]} for c in df.columns],
        "preview_rows": min(config.PREVIEW_ROWS, int(df.shape[0])),
    }
