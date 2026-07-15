"""Tests for overlay layers: merging, secondary axis, validation."""

from __future__ import annotations

import pytest

import plotforge.plots  # noqa: F401  (registers the built-in chart types)
from plotforge.plots import overlay
from plotforge.plots.base import PlotError, merged_options
from plotforge.plots.registry import get_plot
from plotforge.styling import style_model
from plotforge.styling.apply import apply_style

TYPES = {
    "dose": "numeric",
    "response": "numeric",
    "response_err": "numeric",
    "group": "categorical",
    "batch": "categorical",
    "measured_on": "datetime",
}


def _base_fig(sample_df, mapping=None):
    scatter = get_plot("scatter")
    mapping = mapping or {"x": "dose", "y": "response"}
    return scatter.build(sample_df, mapping, merged_options(scatter, {}))


def test_layer_traces_are_merged(sample_df):
    fig = _base_fig(sample_df)
    n_base = len(fig.data)
    layers = [
        {"chart": "line", "mapping": {"x": "dose", "y": "response_err"}},
    ]
    overlay.add_layers(fig, sample_df, TYPES, {"x": "dose", "y": "response"}, layers)
    assert len(fig.data) == n_base + 1
    added = fig.data[-1]
    assert added.meta == {"plotforge_layer": 1}
    assert added.name == "response_err" and added.showlegend is True


def test_layer_secondary_y(sample_df):
    fig = _base_fig(sample_df)
    layers = [
        {
            "chart": "line",
            "secondary_y": True,
            "mapping": {"x": "dose", "y": "response_err"},
        }
    ]
    overlay.add_layers(fig, sample_df, TYPES, {"x": "dose", "y": "response"}, layers)
    assert fig.data[-1].yaxis == "y2"
    assert fig.layout.yaxis2.overlaying == "y"
    assert fig.layout.yaxis2.side == "right"


def test_layers_rejected_with_facets(sample_df):
    fig = _base_fig(sample_df)
    base = {"x": "dose", "y": "response", "facet_col": "group"}
    layers = [{"chart": "line", "mapping": {"x": "dose", "y": "response"}}]
    with pytest.raises(PlotError, match="facet"):
        overlay.add_layers(fig, sample_df, TYPES, base, layers)


def test_layer_validation_error_names_the_layer(sample_df):
    fig = _base_fig(sample_df)
    layers = [{"chart": "line", "mapping": {"x": "dose"}}]  # missing y
    with pytest.raises(PlotError, match="Layer 1"):
        overlay.add_layers(fig, sample_df, TYPES, {"x": "dose"}, layers)


def test_incomplete_layer_is_skipped(sample_df):
    fig = _base_fig(sample_df)
    n_base = len(fig.data)
    overlay.add_layers(
        fig, sample_df, TYPES, {"x": "dose"}, [{"chart": None, "mapping": {}}]
    )
    assert len(fig.data) == n_base


def test_layers_from_pattern_groups_by_layer():
    fields = [
        {"id": {"layer": 0, "field": "chart"}, "value": "line"},
        {"id": {"layer": 0, "field": "secondary_y"}, "value": True},
        {"id": {"layer": 2, "field": "chart"}, "value": "bar"},
    ]
    maps = [
        {"id": {"layer": 0, "name": "x"}, "value": "dose"},
        {"id": {"layer": 0, "name": "y"}, "value": "response"},
        {"id": {"layer": 2, "name": "x"}, "value": "group"},
    ]
    layers = overlay.layers_from_pattern(fields, maps)
    assert layers == [
        {
            "chart": "line",
            "secondary_y": True,
            "mapping": {"x": "dose", "y": "response"},
        },
        {"chart": "bar", "secondary_y": False, "mapping": {"x": "group"}},
    ]


def test_overlay_choices_are_registered():
    names = [name for _, name in overlay.overlay_plot_choices()]
    assert names == list(overlay.OVERLAYABLE)


def test_layer_gets_its_own_palette_slot(sample_df):
    # Base (no grouping) and a one-trace layer both start at px's first
    # color; the layer tag must give them different palette slots.
    fig = _base_fig(sample_df)
    layers = [{"chart": "line", "mapping": {"x": "dose", "y": "response_err"}}]
    overlay.add_layers(fig, sample_df, TYPES, {"x": "dose", "y": "response"}, layers)
    apply_style(fig, style_model.StyleModel())
    base_color = fig.data[0].marker.color
    layer_color = fig.data[-1].line.color
    assert base_color != layer_color
