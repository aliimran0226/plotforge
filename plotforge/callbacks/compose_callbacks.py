"""Callbacks for the Compose section: save panels, preview/export grids.

Saving a panel snapshots the same control values the export callback
reads, so a panel re-renders exactly like the live figure. The panel
store is server-side (``plotforge.compose``); the list UI is rebuilt
after every action.
"""

from __future__ import annotations

import dash
from dash import ALL, Input, Output, State, dcc

from plotforge import compose
from plotforge.callbacks.export_callbacks import sanitize_filename
from plotforge.callbacks.plot_callbacks import _entry_list
from plotforge.data import store
from plotforge.plots import overlay
from plotforge.plots.base import PlotError
from plotforge.plots.registry import get_plot
from plotforge.ui import controls_compose


def _int(value: object, default: int, lo: int, hi: int) -> int:
    try:
        return min(max(int(value), lo), hi)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        return default


def register_callbacks(app: dash.Dash) -> None:
    """Attach compose-section callbacks to ``app``."""

    @app.callback(
        Output("panel-list", "children"),
        Output("compose-error", "children", allow_duplicate=True),
        Output("compose-error", "is_open", allow_duplicate=True),
        Input("save-panel", "n_clicks"),
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
        prevent_initial_call=True,
    )
    def save_panel(n_clicks, token, chart_type, *_patterns):
        """Snapshot the current figure's control values as a panel."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        dataset = store.get(token)
        if dataset is None or not chart_type:
            return dash.no_update, "Build a figure first, then save it.", True

        ctx = dash.ctx
        # states_list mirrors the export callback: 0 token, 1 chart,
        # 2 mapping, 3 options, 4 style, 5 group colors, 6-8 decorations,
        # 9-10 layers.
        spec = compose.PanelSpec(
            chart_type=chart_type,
            mapping={i["id"]["name"]: i.get("value") for i in ctx.states_list[2]},
            options={i["id"]["name"]: i.get("value") for i in ctx.states_list[3]},
            style_values={i["id"]["field"]: i.get("value") for i in ctx.states_list[4]},
            group_colors={
                i["id"]["group"]: i.get("value")
                for i in ctx.states_list[5]
                if i.get("value")
            },
            decorations={
                "ref_lines": _entry_list(ctx.states_list[6]),
                "ref_bands": _entry_list(ctx.states_list[7]),
                "annotations": _entry_list(ctx.states_list[8]),
            },
            layers=overlay.layers_from_pattern(ctx.states_list[9], ctx.states_list[10]),
            dataset=dataset,
            title=f"{get_plot(chart_type).label} - {dataset.filename}",
        )
        compose.save_panel(spec)
        return controls_compose.make_panel_list(), "", False

    @app.callback(
        Output("panel-list", "children", allow_duplicate=True),
        Input({"type": "panel-remove", "pid": ALL}, "n_clicks"),
        Input({"type": "panel-up", "pid": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def manage_panels(*_clicks):
        """Remove or reorder saved panels."""
        trigger = dash.ctx.triggered_id
        # Ignore the firing caused by the buttons being (re)created.
        if not isinstance(trigger, dict) or not dash.ctx.triggered[0]["value"]:
            raise dash.exceptions.PreventUpdate
        if trigger["type"] == "panel-remove":
            compose.remove_panel(trigger["pid"])
        else:
            compose.move_panel_up(trigger["pid"])
        return controls_compose.make_panel_list()

    def _grid_settings(states: list) -> tuple[int, int, int, int, bool]:
        """(columns, cell_w, cell_h, scale, labels) from the State list."""
        columns, cell_w, cell_h, scale, labels = (s.get("value") for s in states)
        return (
            _int(columns, 2, 1, 6),
            _int(cell_w, compose.CELL_WIDTH, 200, 2000),
            _int(cell_h, compose.CELL_HEIGHT, 200, 2000),
            _int(scale, 2, 1, 5),
            bool(labels),
        )

    _GRID_STATES = [
        State("compose-columns", "value"),
        State("compose-cell-width", "value"),
        State("compose-cell-height", "value"),
        State("compose-scale", "value"),
        State("compose-labels", "value"),
    ]

    @app.callback(
        Output("figure-container", "children", allow_duplicate=True),
        Output("compose-error", "children", allow_duplicate=True),
        Output("compose-error", "is_open", allow_duplicate=True),
        Input("compose-preview", "n_clicks"),
        *_GRID_STATES,
        prevent_initial_call=True,
    )
    def preview_composition(n_clicks, *_settings):
        """Show the stitched grid (scale 1) in the figure area."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        columns, cell_w, cell_h, _scale, labels = _grid_settings(dash.ctx.states_list)
        panels = [spec for _, spec in compose.list_panels()]
        try:
            png = compose.compose_grid(
                panels, columns, cell_w, cell_h, scale=1, labels=labels, fmt="png"
            )
        except (PlotError, ValueError) as exc:
            return dash.no_update, str(exc), True
        except Exception as exc:  # kaleido issues land here
            return dash.no_update, f"Preview failed: {exc}", True
        return controls_compose.make_preview_image(png), "", False

    @app.callback(
        Output("compose-download", "data"),
        Output("compose-error", "children", allow_duplicate=True),
        Output("compose-error", "is_open", allow_duplicate=True),
        Input("compose-export", "n_clicks"),
        *_GRID_STATES,
        State("compose-format", "value"),
        State("compose-filename", "value"),
        prevent_initial_call=True,
    )
    def export_composition(n_clicks, *_settings):
        """Render the grid at full scale and download it."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        states = dash.ctx.states_list
        columns, cell_w, cell_h, scale, labels = _grid_settings(states[:5])
        fmt = states[5].get("value")
        fmt = fmt if fmt in ("png", "jpg") else "png"
        filename = states[6].get("value")
        panels = [spec for _, spec in compose.list_panels()]
        try:
            img = compose.compose_grid(
                panels, columns, cell_w, cell_h, scale=scale, labels=labels, fmt=fmt
            )
        except (PlotError, ValueError) as exc:
            return dash.no_update, str(exc), True
        except Exception as exc:
            return dash.no_update, f"Export failed: {exc}", True
        return (
            dcc.send_bytes(img, sanitize_filename(filename, fmt)),
            "",
            False,
        )
