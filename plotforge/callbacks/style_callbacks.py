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
from plotforge.styling.style_model import defaults_by_field, entries_by_index
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

    @app.callback(
        Output(
            {"type": "style", "field": "legend_orientation"},
            "value",
            allow_duplicate=True,
        ),
        Input({"type": "style", "field": "legend_position"}, "value"),
        State({"type": "style", "field": "legend_orientation"}, "value"),
        prevent_initial_call=True,
    )
    def legend_orientation_follows_position(position, orientation):
        """'Below' almost always wants a horizontal legend - preselect it."""
        if position == "below" and orientation != "h":
            return "h"
        raise dash.exceptions.PreventUpdate

    #: Add-button id -> (entry kind, seed values for the new card).
    _ADDERS = {
        "add-decor-hline": ("line", {"orient": "h"}),
        "add-decor-vline": ("line", {"orient": "v"}),
        "add-decor-band": ("band", {}),
        "add-decor-annot": ("annot", {}),
    }

    @app.callback(
        Output("decor-store", "data"),
        Output("decor-controls", "children"),
        Input("add-decor-hline", "n_clicks"),
        Input("add-decor-vline", "n_clicks"),
        Input("add-decor-band", "n_clicks"),
        Input("add-decor-annot", "n_clicks"),
        Input({"type": "decor-del-line", "idx": ALL}, "n_clicks"),
        Input({"type": "decor-del-band", "idx": ALL}, "n_clicks"),
        Input({"type": "decor-del-annot", "idx": ALL}, "n_clicks"),
        State("decor-store", "data"),
        State({"type": "decor-line", "idx": ALL, "prop": ALL}, "value"),
        State({"type": "decor-band", "idx": ALL, "prop": ALL}, "value"),
        State({"type": "decor-annot", "idx": ALL, "prop": ALL}, "value"),
        prevent_initial_call=True,
    )
    def manage_decorations(*_args):
        """Add/remove reference-line, band, and annotation cards."""
        trigger = ctx.triggered_id
        # Newly created remove buttons fire this callback with
        # n_clicks=None; only act on real clicks.
        if trigger is None or not ctx.triggered[0]["value"]:
            raise dash.exceptions.PreventUpdate

        data = ctx.states_list[0]["value"] or {}
        decor = {
            "line": list(data.get("line", [])),
            "band": list(data.get("band", [])),
            "annot": list(data.get("annot", [])),
            "next": int(data.get("next", 0)),
        }
        # Current card values, so regenerating the list keeps user input.
        current = {
            "line": entries_by_index(ctx.states_list[1]),
            "band": entries_by_index(ctx.states_list[2]),
            "annot": entries_by_index(ctx.states_list[3]),
        }

        # NB: for pattern ids, ctx.triggered_id is an *unhashable*
        # AttributeDict - it must never be used in a dict-membership
        # test directly (that raises TypeError, not False).
        if isinstance(trigger, str) and trigger in _ADDERS:
            kind, seed = _ADDERS[trigger]
            idx = decor["next"]
            decor[kind].append(idx)
            decor["next"] = idx + 1
            current[kind][idx] = dict(seed)
        elif isinstance(trigger, dict):  # a remove button
            kind = trigger["type"].removeprefix("decor-del-")
            if trigger["idx"] in decor.get(kind, []):
                decor[kind].remove(trigger["idx"])

        children = controls_style.make_decoration_controls(decor, current)
        return decor, children
