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

from plotforge.callbacks.plot_callbacks import _style_from_pattern_lists, build_figure
from plotforge.data import store
from plotforge.plots import overlay
from plotforge.plots.base import PlotError

#: Characters allowed in a download filename; everything else becomes '_'.
_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._-]+")

#: Export formats kaleido can render; svg/pdf are vector (scale-free).
EXPORT_FORMATS = ("png", "jpg", "svg", "pdf")


def sanitize_filename(name: str | None, fmt: str) -> str:
    """Turn user input into a safe '<name>.<fmt>' download filename."""
    base = _FILENAME_SAFE.sub("_", (name or "").strip()).strip("._")
    if not base:
        base = "figure"
    # Drop a typed extension; the format dropdown decides it.
    for ext in (".png", ".jpg", ".jpeg", ".svg", ".pdf"):
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
        State({"type": "decor-line", "idx": ALL, "prop": ALL}, "value"),
        State({"type": "decor-band", "idx": ALL, "prop": ALL}, "value"),
        State({"type": "decor-annot", "idx": ALL, "prop": ALL}, "value"),
        State({"type": "layer-field", "layer": ALL, "field": ALL}, "value"),
        State({"type": "layer-map", "layer": ALL, "name": ALL}, "value"),
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
        *_pattern_and_settings,
    ):
        """Build the current figure at export size and send it for download."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        dataset = store.get(token)
        if dataset is None or not chart_type:
            return dash.no_update, "Upload data and build a figure first.", True

        ctx = dash.ctx
        # states_list: 0 token, 1 chart type, 2 mapping, 3 options,
        # 4-8 style/group/decoration patterns, 9-10 layer patterns,
        # 11-15 export settings.
        mapping = {i["id"]["name"]: i.get("value") for i in ctx.states_list[2]}
        options = {i["id"]["name"]: i.get("value") for i in ctx.states_list[3]}
        style = _style_from_pattern_lists(ctx.states_list)
        layers = overlay.layers_from_pattern(ctx.states_list[9], ctx.states_list[10])
        width, height, scale, fmt, filename = (
            ctx.states_list[i].get("value") for i in range(11, 16)
        )

        fmt = fmt if fmt in EXPORT_FORMATS else "png"
        width = int(width or style.width)
        height = int(height or style.height)
        scale = min(max(int(scale or 1), 1), 5)
        # Bake the export size into the style so size-dependent styling
        # (the outer border offsets) is computed for the exported canvas.
        style.width, style.height = width, height

        try:
            fig = build_figure(chart_type, dataset, mapping, options, style, layers)
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
