"""Export callback: rebuild the current figure and download it as an image.

The figure is rebuilt server-side from the same control values the live
render uses (mapping + options + style), so the export always matches
what is on screen - but rendered at the requested export dimensions
instead of the on-screen size.
"""

from __future__ import annotations

import re

import dash
from dash import ALL, Input, Output, State, dcc

from plotforge.callbacks.plot_callbacks import build_figure
from plotforge.data import store
from plotforge.plots.base import PlotError
from plotforge.styling import style_model

#: Characters allowed in a download filename; everything else becomes '_'.
_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str | None, fmt: str) -> str:
    """Turn user input into a safe '<name>.<fmt>' download filename."""
    base = _FILENAME_SAFE.sub("_", (name or "").strip()).strip("._")
    if not base:
        base = "figure"
    # Drop a typed extension; the format dropdown decides it.
    for ext in (".png", ".jpg", ".jpeg"):
        if base.lower().endswith(ext):
            base = base[: -len(ext)]
    return f"{base}.{fmt}"


def export_figure_bytes(fig, fmt: str, width: int, height: int, scale: int) -> bytes:
    """Render a figure to PNG/JPG bytes via kaleido."""
    return fig.to_image(format=fmt, width=width, height=height, scale=scale)


def register_callbacks(app: dash.Dash) -> None:
    """Attach the export callback to ``app``."""

    @app.callback(
        Output("export-download", "data"),
        Output("export-error", "children"),
        Output("export-error", "is_open"),
        Input("export-button", "n_clicks"),
        State("dataset-token", "data"),
        State("chart-type", "value"),
        State({"type": "mapping", "name": ALL}, "value"),
        State({"type": "plot-opt", "name": ALL}, "value"),
        State({"type": "style", "field": ALL}, "value"),
        State({"type": "group-color", "group": ALL}, "value"),
        State("export-width", "value"),
        State("export-height", "value"),
        State("export-scale", "value"),
        State("export-format", "value"),
        State("export-filename", "value"),
        prevent_initial_call=True,
    )
    def export_figure(
        n_clicks,
        token,
        chart_type,
        _mapping_values,
        _option_values,
        _style_values,
        _group_colors,
        width,
        height,
        scale,
        fmt,
        filename,
    ):
        """Build the current figure at export size and send it for download."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        dataset = store.get(token)
        if dataset is None or not chart_type:
            return dash.no_update, "Upload data and build a figure first.", True

        ctx = dash.ctx
        mapping = {i["id"]["name"]: i.get("value") for i in ctx.states_list[2]}
        options = {i["id"]["name"]: i.get("value") for i in ctx.states_list[3]}
        style_values = {i["id"]["field"]: i.get("value") for i in ctx.states_list[4]}
        group_colors = {
            i["id"]["group"]: i.get("value")
            for i in ctx.states_list[5]
            if i.get("value")
        }
        style = style_model.from_values(style_values, group_colors)

        fmt = fmt if fmt in ("png", "jpg") else "png"
        width = int(width or style.width)
        height = int(height or style.height)
        scale = min(max(int(scale or 1), 1), 5)

        try:
            fig = build_figure(chart_type, dataset, mapping, options, style)
            img = export_figure_bytes(fig, fmt, width, height, scale)
        except PlotError as exc:
            return dash.no_update, str(exc), True
        except Exception as exc:  # kaleido/chrome issues land here
            return (
                dash.no_update,
                f"Export failed: {exc}. See the troubleshooting section "
                "of the README (kaleido needs a Chromium-based browser).",
                True,
            )

        return (
            dcc.send_bytes(img, sanitize_filename(filename, fmt)),
            "",
            False,
        )
