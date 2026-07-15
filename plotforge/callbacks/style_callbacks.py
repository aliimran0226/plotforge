"""Callbacks owned by the Style section.

- Regenerate the per-group color pickers when the grouping column (or
  its categories) changes.
- Reset every style control to its StyleModel default.
"""

from __future__ import annotations

import dash
from dash import ALL, Input, Output, State, ctx

from plotforge.data import store
from plotforge.styling.apply import palette_colors
from plotforge.styling.style_model import defaults_by_field
from plotforge.ui import controls_style

#: Mapping slots that define legend groups, in priority order. 'names'
#: is used by pie charts.
_GROUPING_SLOTS = ("color", "names")


def detect_groups(dataset: store.Dataset, mapping: dict[str, str]) -> list[str]:
    """Category values of the active grouping column ('' if none).

    Numeric grouping columns mean continuous coloring - no discrete
    groups to pick colors for.
    """
    for slot in _GROUPING_SLOTS:
        col = mapping.get(slot)
        if col and dataset.column_types.get(col) == "categorical":
            values = dataset.df[col].dropna().unique()
            return [str(v) for v in values]
    return []


def register_callbacks(app: dash.Dash) -> None:
    """Attach style-section callbacks to ``app``."""

    @app.callback(
        Output("group-color-controls", "children"),
        Input("dataset-token", "data"),
        Input({"type": "mapping", "name": ALL}, "value"),
        State({"type": "style", "field": "palette"}, "value"),
        State({"type": "group-color", "group": ALL}, "value"),
    )
    def rebuild_group_pickers(token, _mapping_values, palette_label, _picker_values):
        """One color picker per group of the active color/names column."""
        dataset = store.get(token)
        if dataset is None:
            return controls_style.make_group_color_pickers([], [])
        mapping = {item["id"]["name"]: item.get("value") for item in ctx.inputs_list[1]}
        groups = detect_groups(dataset, mapping)
        # Keep the user's picks for groups that still exist.
        current = {
            item["id"]["group"]: item.get("value")
            for item in ctx.states_list[1]
            if item.get("value")
        }
        palette = palette_colors(palette_label or "")
        return controls_style.make_group_color_pickers(groups, palette, current)

    @app.callback(
        Output({"type": "style", "field": ALL}, "value"),
        Output({"type": "group-color", "group": ALL}, "value"),
        Input("reset-style", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_style(n_clicks):
        """Snap every style control (and group picker) back to defaults."""
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        defaults = defaults_by_field()
        style_values = [
            defaults.get(item["id"]["field"]) for item in ctx.outputs_list[0]
        ]
        palette = palette_colors(str(defaults["palette"]))
        group_values = [
            controls_style._to_hex(palette[i % len(palette)])
            for i in range(len(ctx.outputs_list[1]))
        ]
        return style_values, group_values
