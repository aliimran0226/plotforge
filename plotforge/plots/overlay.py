"""Overlay layers: extra chart layers drawn on the base figure's axes.

A layer is a dict ``{"chart": <plot name>, "secondary_y": bool,
"mapping": {slot: column}}``. Layers are built by the same plot classes
as base charts (with default options) and their traces are appended to
the base figure - optionally against a right-hand y axis. Faceted base
charts cannot take layers (there is no single target axis).

Pure functions, no Dash: the layer UI lives in ``ui/controls_layers.py``
and the collection from pattern ids in ``callbacks/plot_callbacks.py``.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from plotforge.plots.base import PlotError, clean_mapping, merged_options
from plotforge.plots.registry import all_plots, get_plot

#: Chart types that can be drawn as overlay layers (cartesian, no
#: subplot-generating mappings).
OVERLAYABLE = ("scatter", "line", "bar", "area", "errorbar")

#: Mapping slots that would create subplots - never offered on layers.
_EXCLUDED_SLOTS = ("facet_row", "facet_col")


def overlay_plot_choices() -> list[tuple[str, str]]:
    """(label, name) pairs for the layer chart-type dropdown."""
    plots = all_plots()
    return [(plots[n].label, n) for n in OVERLAYABLE if n in plots]


def layer_mapping_specs(plot_cls) -> list:
    """The mapping specs a layer exposes (facet slots removed)."""
    return [s for s in plot_cls.all_mappings() if s.name not in _EXCLUDED_SLOTS]


def layers_from_pattern(field_items: list[dict], map_items: list[dict]) -> list[dict]:
    """Group layer pattern-control entries into ordered layer dicts.

    ``field_items`` carry ids ``{"layer": i, "field": ...}`` (chart,
    secondary_y); ``map_items`` carry ``{"layer": i, "name": <slot>}``.
    """
    layers: dict[int, dict] = {}

    def entry(idx: int) -> dict:
        return layers.setdefault(
            idx, {"chart": None, "secondary_y": False, "mapping": {}}
        )

    for item in field_items:
        ident = item.get("id") or {}
        entry(ident.get("layer"))[ident.get("field")] = item.get("value")
    for item in map_items:
        ident = item.get("id") or {}
        entry(ident.get("layer"))["mapping"][ident.get("name")] = item.get("value")
    return [layers[i] for i in sorted(layers)]


def add_layers(
    fig: go.Figure,
    df: pd.DataFrame,
    column_types: dict[str, str],
    base_mapping: dict[str, str],
    layers: list[dict],
) -> go.Figure:
    """Validate, build, and merge every layer into ``fig`` (mutates it).

    Raises:
        PlotError: For faceted base charts or an invalid layer, with the
            layer number in the message.
    """
    base = clean_mapping(base_mapping)
    if any(base.get(slot) for slot in _EXCLUDED_SLOTS):
        raise PlotError(
            "Overlay layers cannot be combined with facets - clear the "
            "facet mappings or remove the layers."
        )

    any_secondary = False
    for number, layer in enumerate(layers, start=1):
        chart = layer.get("chart")
        if not chart:
            continue
        if chart not in OVERLAYABLE:
            raise PlotError(f"Layer {number}: '{chart}' cannot be overlaid.")
        plot_cls = get_plot(chart)
        mapping = clean_mapping(layer.get("mapping") or {})
        options = merged_options(plot_cls, {})
        try:
            plot_cls.validate(mapping, column_types, options)
            layer_fig = plot_cls.build(df, mapping, options)
        except PlotError as exc:
            raise PlotError(f"Layer {number}: {exc}") from exc

        secondary = bool(layer.get("secondary_y"))
        any_secondary = any_secondary or secondary
        _merge(fig, layer_fig, number, mapping, secondary)

    if any_secondary:
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False))
    return fig


def _merge(
    fig: go.Figure,
    layer_fig: go.Figure,
    number: int,
    mapping: dict[str, str],
    secondary: bool,
) -> None:
    """Append a built layer's traces to the base figure."""
    for trace in layer_fig.data:
        # Nameless single traces would be invisible in the legend; name
        # them after the layer's y column so overlays stay identifiable.
        if not trace.name:
            trace.name = mapping.get("y") or mapping.get("x") or f"layer {number}"
            trace.showlegend = True
        # The layer tag gives apply_style separate palette slots per
        # layer (px starts every figure at the same first color).
        trace.meta = {"plotforge_layer": number}
        if secondary:
            trace.update(yaxis="y2")
        fig.add_trace(trace)
