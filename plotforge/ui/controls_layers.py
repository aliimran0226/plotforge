"""Overlay-layer cards inside the Chart section.

Each layer card carries a chart-type dropdown, mapping dropdowns
generated from that chart's specs (facet slots excluded), and a
secondary-y checkbox. Ids follow the dynamic-entry pattern:
``{"type": "layer-field", "layer": i, "field": "chart"|"secondary_y"}``
and ``{"type": "layer-map", "layer": i, "name": <slot>}``; the id list
lives in ``layers-store`` (see ``callbacks/layer_callbacks.py``).
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from plotforge.plots.overlay import layer_mapping_specs, overlay_plot_choices
from plotforge.plots.registry import get_plot
from plotforge.ui.controls_mapping import _column_options


def layer_field_id(layer: int, field: str) -> dict:
    """Pattern id for a layer-level setting (chart type, secondary y)."""
    return {"type": "layer-field", "layer": layer, "field": field}


def layer_map_id(layer: int, name: str) -> dict:
    """Pattern id for one mapping dropdown of one layer."""
    return {"type": "layer-map", "layer": layer, "name": name}


def layer_del_id(layer: int) -> dict:
    """Pattern id for a layer's remove button."""
    return {"type": "layer-del", "layer": layer}


def build_layer_section() -> html.Div:
    """Static skeleton of the layers block (below the chart options)."""
    return html.Div(
        [
            html.Hr(className="my-2"),
            dbc.Label("Overlay layers", className="small mb-1 fw-bold"),
            html.Div(
                html.Small(
                    "Draw extra charts on the same axes (e.g. a line over "
                    "bars). Not available with facets.",
                    className="text-muted",
                ),
                id="layer-controls",
            ),
            dbc.Button(
                "+ Add layer",
                id="add-layer",
                color="secondary",
                outline=True,
                size="sm",
                className="mt-1",
            ),
            dcc.Store(id="layers-store", data={"layers": [], "next": 0}),
        ]
    )


def make_layer_card(
    idx: int,
    number: int,
    chart: str,
    columns: list[str],
    column_types: dict[str, str],
    current_mapping: dict[str, str],
    secondary_y: bool,
) -> dbc.Card:
    """One overlay-layer card, mapping dropdowns matching ``chart``."""
    plot_cls = get_plot(chart)
    header = html.Div(
        [
            html.Small(f"Layer {number}", className="fw-bold"),
            dbc.Button(
                "Remove",
                id=layer_del_id(idx),
                color="link",
                size="sm",
                className="p-0 text-danger small",
            ),
        ],
        className="d-flex justify-content-between align-items-center mb-1",
    )
    rows: list = [
        header,
        html.Div(
            [
                dbc.Label("Chart type", className="small mb-0"),
                dcc.Dropdown(
                    id=layer_field_id(idx, "chart"),
                    options=[
                        {"label": lbl, "value": val}
                        for lbl, val in overlay_plot_choices()
                    ],
                    value=chart,
                    clearable=False,
                ),
            ],
            className="mb-1",
        ),
    ]
    used: set[str] = set()
    for spec in layer_mapping_specs(plot_cls):
        required = spec in plot_cls.required_mappings
        value = current_mapping.get(spec.name)
        if value and (
            value not in column_types or column_types[value] not in spec.kinds
        ):
            value = None
        if not value and required:
            # Default like the base mapping UI: first not-yet-used column
            # of an accepted kind, so a fresh layer renders immediately
            # instead of erroring until columns are picked.
            value = next(
                (
                    c
                    for c in columns
                    if column_types.get(c) in spec.kinds and c not in used
                ),
                None,
            )
        if value:
            used.add(value)
        label = spec.label + ("" if required else " (optional)")
        rows.append(
            html.Div(
                [
                    dbc.Label(label, className="small mb-0"),
                    dcc.Dropdown(
                        id=layer_map_id(idx, spec.name),
                        options=_column_options(columns, column_types, spec.kinds),
                        value=value,
                        clearable=not required,
                        placeholder="Select column...",
                    ),
                ],
                className="mb-1",
            )
        )
    rows.append(
        html.Div(
            [
                dbc.Checkbox(
                    id=layer_field_id(idx, "secondary_y"), value=bool(secondary_y)
                ),
                dbc.Label("Secondary Y axis (right)", className="small mb-0 ms-1"),
            ],
            className="d-flex align-items-center",
        )
    )
    return dbc.Card(dbc.CardBody(rows, className="p-2"), className="mb-2")


def make_layer_cards(
    store: dict,
    columns: list[str],
    column_types: dict[str, str],
    current: dict[int, dict],
) -> list:
    """All layer cards from the store's id list.

    ``current`` maps layer idx -> {"chart": ..., "secondary_y": ...,
    "mapping": {...}} and preserves selections across rebuilds.
    """
    ids = store.get("layers", [])
    if not ids:
        return [
            html.Small(
                "Draw extra charts on the same axes (e.g. a line over "
                "bars). Not available with facets.",
                className="text-muted",
            )
        ]
    cards = []
    for number, idx in enumerate(ids, start=1):
        state = current.get(idx, {})
        chart = state.get("chart") or "line"
        cards.append(
            make_layer_card(
                idx,
                number,
                chart,
                columns,
                column_types,
                state.get("mapping") or {},
                bool(state.get("secondary_y")),
            )
        )
    return cards
