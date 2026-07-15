"""Data section of the sidebar: upload widget, sheet picker, preview.

Static skeleton only - the dynamic parts (sheet options, file summary,
preview table) are filled in by ``callbacks/data_callbacks.py``.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table, dcc, html

from plotforge import config


def build_data_controls() -> html.Div:
    """Return the static content of the Data accordion section."""
    upload = dcc.Upload(
        id="data-upload",
        children=html.Div(
            [
                "Drag & drop or ",
                html.A("select a file", className="text-primary"),
                html.Div(
                    "CSV, TSV, or Excel (.xlsx / .xls)",
                    className="text-muted small",
                ),
            ]
        ),
        multiple=False,
        className="border border-2 border-dashed rounded text-center p-4 mb-2",
        style={"cursor": "pointer"},
    )

    sheet_picker = html.Div(
        [
            dbc.Label("Excel sheet", html_for="sheet-picker", className="small mb-1"),
            dcc.Dropdown(id="sheet-picker", clearable=False, placeholder="Sheet"),
        ],
        id="sheet-picker-wrapper",
        style={"display": "none"},  # only shown for multi-sheet Excel files
        className="mb-2",
    )

    sample_button = dbc.Button(
        [html.I(className="bi bi-stars me-1"), "Load example data"],
        id="load-sample",
        color="secondary",
        outline=True,
        size="sm",
        className="w-100 mb-2",
        title="A small built-in dose-response dataset to explore the tool",
    )

    return html.Div(
        [
            upload,
            sample_button,
            dbc.Alert(
                id="data-error",
                color="danger",
                dismissable=True,
                is_open=False,
                className="py-2 small",
            ),
            sheet_picker,
            html.Div(id="data-summary", className="small mb-2"),
            html.Div(id="data-preview"),
            # Token pointing at the server-side dataset cache. Everything
            # downstream (mapping, plotting, export) keys off this store.
            dcc.Store(id="dataset-token"),
        ]
    )


def make_summary(filename: str, rows: int, cols: int, sheet: str | None) -> html.Div:
    """One-line file summary shown above the preview table."""
    parts = [html.Strong(filename)]
    if sheet:
        parts.append(html.Span(f" - sheet '{sheet}'"))
    parts.append(html.Span(f" - {rows:,} rows x {cols} columns"))
    return html.Div(parts, className="text-muted")


#: Short badges rendered next to column names in the preview header.
_TYPE_BADGE = {"numeric": "#", "categorical": "abc", "datetime": "date"}


def make_preview_table(df: pd.DataFrame, types: dict[str, str]) -> dash_table.DataTable:
    """Preview table of the first rows, with inferred dtype in the header."""
    head = df.head(config.PREVIEW_ROWS)
    columns = [
        {"name": [f"{col}", f"({_TYPE_BADGE.get(types.get(col, ''), '?')})"], "id": col}
        for col in head.columns
    ]
    # DataTable needs JSON-serializable cells; render everything as text.
    records = head.astype(str).to_dict("records")
    return dash_table.DataTable(
        data=records,
        columns=columns,
        merge_duplicate_headers=False,
        style_table={"overflowX": "auto", "maxHeight": "320px", "overflowY": "auto"},
        style_cell={
            "fontSize": "12px",
            "fontFamily": "monospace",
            "maxWidth": "160px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "padding": "4px 8px",
        },
        style_header={"fontWeight": "bold", "backgroundColor": "#f5f5f5"},
        page_action="none",
    )
