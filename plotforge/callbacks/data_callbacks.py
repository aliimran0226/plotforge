"""Callbacks for the Data section: upload handling and sheet switching.

Thin wrappers around ``data.loader`` / ``data.store``; all parsing
logic lives there so it can be unit-tested without Dash.
"""

from __future__ import annotations

import dash
from dash import Input, Output, State

from plotforge.data import loader, store
from plotforge.ui import controls_data

#: Number of outputs shared by the two callbacks below (see _outputs()).
_N_OUTPUTS = 8


def _outputs(duplicate: bool) -> list[Output]:
    """The output list shared by upload and sheet-switch callbacks.

    Dash requires ``allow_duplicate=True`` on every output that a second
    callback also writes, hence the flag.
    """
    return [
        Output("dataset-token", "data", allow_duplicate=duplicate),
        Output("data-summary", "children", allow_duplicate=duplicate),
        Output("data-preview", "children", allow_duplicate=duplicate),
        Output("sheet-picker", "options", allow_duplicate=duplicate),
        Output("sheet-picker", "value", allow_duplicate=duplicate),
        Output("sheet-picker-wrapper", "style", allow_duplicate=duplicate),
        Output("data-error", "children", allow_duplicate=duplicate),
        Output("data-error", "is_open", allow_duplicate=duplicate),
    ]


def _error_tuple(message: str) -> tuple:
    """Output tuple that shows an error and leaves everything else as-is."""
    return (dash.no_update,) * (_N_OUTPUTS - 2) + (message, True)


def _ingest(raw: bytes, filename: str, sheet: str | None, token: str | None) -> tuple:
    """Parse file bytes (upload or sheet switch) and refresh the cache.

    Returns the tuple of output values in the order of ``_outputs()``.
    """
    sheets = loader.list_sheets(raw, filename)
    active_sheet = (
        sheet
        if (sheet and sheets and sheet in sheets)
        else (sheets[0] if sheets else None)
    )
    df = loader.load_dataframe(raw, filename, sheet=active_sheet)
    types = loader.infer_column_types(df)
    df = loader.coerce_datetime_columns(df, types)

    dataset = store.Dataset(
        filename=filename,
        raw=raw,
        df=df,
        sheets=sheets,
        active_sheet=active_sheet,
        column_types=types,
    )
    # Reuse the token on sheet switches so downstream state stays valid.
    if token and store.get(token):
        store.update(token, dataset)
        new_token = token
    else:
        new_token = store.put(dataset)

    summary = controls_data.make_summary(
        filename, df.shape[0], df.shape[1], active_sheet
    )
    preview = controls_data.make_preview_table(df, types)
    show_picker = bool(sheets and len(sheets) > 1)
    sheet_options = [{"label": s, "value": s} for s in (sheets or [])]
    picker_style = {"display": "block"} if show_picker else {"display": "none"}

    return (
        new_token,
        summary,
        preview,
        sheet_options,
        active_sheet,
        picker_style,
        "",
        False,
    )


def register_callbacks(app: dash.Dash) -> None:
    """Attach the data-section callbacks to ``app``."""

    @app.callback(
        # The extra output resets contents so the same file can be
        # uploaded twice in a row (dcc.Upload only fires when contents
        # *change*); the reset's echo is absorbed by the guard below.
        _outputs(duplicate=False) + [Output("data-upload", "contents")],
        Input("data-upload", "contents"),
        State("data-upload", "filename"),
        prevent_initial_call=True,
    )
    def handle_upload(contents: str | None, filename: str | None):
        """Parse a newly uploaded file and populate summary + preview."""
        if not contents or not filename:
            raise dash.exceptions.PreventUpdate
        try:
            raw = loader.decode_upload(contents)
            # A fresh upload always gets a fresh token.
            return _ingest(raw, filename, sheet=None, token=None) + (None,)
        except loader.LoaderError as exc:
            return _error_tuple(str(exc)) + (None,)

    @app.callback(
        _outputs(duplicate=True),
        Input("sheet-picker", "value"),
        State("dataset-token", "data"),
        prevent_initial_call=True,
    )
    def handle_sheet_switch(sheet: str | None, token: str | None):
        """Re-parse the cached workbook when the user picks another sheet."""
        dataset = store.get(token)
        # Ignore programmatic value changes (e.g. right after upload).
        if not sheet or dataset is None or dataset.active_sheet == sheet:
            raise dash.exceptions.PreventUpdate
        try:
            # The raw bytes are cached, so no re-upload is needed.
            return _ingest(dataset.raw, dataset.filename, sheet=sheet, token=token)
        except loader.LoaderError as exc:
            return _error_tuple(str(exc))
