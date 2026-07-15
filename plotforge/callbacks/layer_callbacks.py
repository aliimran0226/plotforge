"""Callback managing the overlay-layer cards.

Adds/removes layer cards and rebuilds them when the dataset or a
layer's chart type changes, preserving current selections (same
dynamic-entry pattern as the style decorations). Rebuilding recreates
components that are Inputs of this very callback, which re-fires it; a
fingerprint of everything that affects the cards' *structure* stored in
``layers-store`` turns that echo into a PreventUpdate instead of a loop.
"""

from __future__ import annotations

import dash
from dash import ALL, Input, Output, State, ctx

from plotforge.data import store
from plotforge.ui import controls_layers


def register_callbacks(app: dash.Dash) -> None:
    """Attach the layer-management callback to ``app``."""

    @app.callback(
        Output("layers-store", "data"),
        Output("layer-controls", "children"),
        Input("add-layer", "n_clicks"),
        Input({"type": "layer-del", "layer": ALL}, "n_clicks"),
        Input({"type": "layer-field", "layer": ALL, "field": "chart"}, "value"),
        Input("dataset-token", "data"),
        State("layers-store", "data"),
        State({"type": "layer-field", "layer": ALL, "field": ALL}, "value"),
        State({"type": "layer-map", "layer": ALL, "name": ALL}, "value"),
        prevent_initial_call=True,
    )
    def manage_layers(*_args):
        """Add/remove/rebuild overlay-layer cards."""
        trigger = ctx.triggered_id
        token = ctx.inputs_list[3].get("value")
        dataset = store.get(token)

        data = ctx.states_list[0]["value"] or {}
        layers = {
            "layers": list(data.get("layers", [])),
            "next": int(data.get("next", 0)),
        }
        current = _current_layers(ctx.states_list[1], ctx.states_list[2])

        if trigger == "add-layer" and ctx.triggered[0]["value"]:
            idx = layers["next"]
            layers["layers"].append(idx)
            layers["next"] = idx + 1
            current[idx] = {"chart": "line", "secondary_y": False, "mapping": {}}
        elif (
            isinstance(trigger, dict)
            and trigger.get("type") == "layer-del"
            and ctx.triggered[0]["value"]
        ):
            if trigger["layer"] in layers["layers"]:
                layers["layers"].remove(trigger["layer"])
        else:
            # Chart switch, dataset change, or the echo fired by our own
            # rebuild: only proceed when the card structure would change.
            if data.get("fp") == _fingerprint(token, layers, current):
                raise dash.exceptions.PreventUpdate

        layers["fp"] = _fingerprint(token, layers, current)
        if dataset is None:
            children = controls_layers.make_layer_cards({}, [], {}, {})
        else:
            children = controls_layers.make_layer_cards(
                layers, list(dataset.df.columns), dataset.column_types, current
            )
        return layers, children


def _fingerprint(token: str | None, layers: dict, current: dict[int, dict]) -> list:
    """JSON-stable digest of everything that shapes the cards."""
    return [
        token,
        [[idx, (current.get(idx) or {}).get("chart")] for idx in layers["layers"]],
    ]


def _current_layers(field_items: list[dict], map_items: list[dict]) -> dict[int, dict]:
    """Current per-layer state, ``idx -> {chart, secondary_y, mapping}``."""
    layers: dict[int, dict] = {}

    def entry(idx: int) -> dict:
        return layers.setdefault(idx, {"mapping": {}})

    for item in field_items:
        ident = item.get("id") or {}
        entry(ident.get("layer"))[ident.get("field")] = item.get("value")
    for item in map_items:
        ident = item.get("id") or {}
        entry(ident.get("layer"))["mapping"][ident.get("name")] = item.get("value")
    return layers
