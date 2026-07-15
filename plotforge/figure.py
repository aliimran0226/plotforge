"""The one figure-building path shared by render, export, and compose.

Kept outside ``callbacks/`` so non-callback code (tests, the compose
module) can build figures without touching Dash.
"""

from __future__ import annotations

from plotforge.data import store
from plotforge.plots import overlay
from plotforge.plots.base import clean_mapping, merged_options
from plotforge.plots.registry import get_plot
from plotforge.styling import style_model
from plotforge.styling.apply import apply_style


def build_figure(
    chart_type: str,
    dataset: store.Dataset,
    mapping: dict,
    options: dict,
    style: style_model.StyleModel | None = None,
    layers: list[dict] | None = None,
):
    """Validate, build, overlay, and style one figure.

    Returns a fully styled plotly Figure. Raises PlotError for
    user-fixable issues.
    """
    plot_cls = get_plot(chart_type)
    mapping = clean_mapping(mapping)
    options = merged_options(plot_cls, options)
    plot_cls.validate(mapping, dataset.column_types, options)
    fig = plot_cls.build(dataset.df, mapping, options)
    if layers:
        overlay.add_layers(fig, dataset.df, dataset.column_types, mapping, layers)
    return apply_style(fig, style or style_model.StyleModel())
