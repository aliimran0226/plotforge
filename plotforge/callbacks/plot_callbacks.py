"""Callbacks for the Chart section and the live figure.

Two callbacks:

1. ``rebuild_mapping_ui`` - regenerates the mapping dropdowns and
   chart-specific option widgets whenever the chart type or the dataset
   changes, carrying over compatible selections.
2. ``render_figure`` - the single live-update callback: reads the
   current mapping + options, asks the registry to build the figure,
   and renders it. (Phase 4 adds style inputs here.)
"""

from __future__ import annotations

import dash
from dash import ALL, Input, Output, State, dcc, html

from plotforge import config
from plotforge.data import store
from plotforge.plots.base import PlotError, clean_mapping, merged_options
from plotforge.plots.registry import all_plots, get_plot
from plotforge.ui import controls_mapping

#: dcc.Graph config: keep the modebar's PNG download as a quick fallback
#: to the Export section (which does proper high-DPI export).
GRAPH_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "filename": "plotforge_figure"},
}


def _values_by_name(pattern_list: list[dict]) -> dict[str, object]:
    """Turn ctx.inputs_list/states_list pattern entries into name->value."""
    return {item["id"]["name"]: item.get("value") for item in pattern_list}


def _no_data_placeholder() -> html.P:
    return html.P(
        "Upload a data file to get started.",
        className="text-muted text-center mt-5",
    )


def build_figure(chart_type: str, dataset: store.Dataset, mapping: dict, options: dict):
    """Pure figure-building path shared by render and (later) export.

    Returns a plotly Figure. Raises PlotError for user-fixable issues.
    """
    plot_cls = get_plot(chart_type)
    mapping = clean_mapping(mapping)
    plot_cls.validate(mapping, dataset.column_types)
    options = merged_options(plot_cls, options)
    fig = plot_cls.build(dataset.df, mapping, options)
    # Baseline geometry/template; the full style pass replaces this in
    # the styling phase.
    fig.update_layout(
        template=config.TEMPLATE,
        width=config.FIGURE_WIDTH,
        height=config.FIGURE_HEIGHT,
        margin=config.MARGIN,
    )
    return fig


def register_callbacks(app: dash.Dash) -> None:
    """Attach chart-section callbacks to ``app``."""

    @app.callback(
        Output("mapping-controls", "children"),
        Output("plot-options-controls", "children"),
        Input("chart-type", "value"),
        Input("dataset-token", "data"),
        State({"type": "mapping", "name": ALL}, "value"),
        State({"type": "plot-opt", "name": ALL}, "value"),
    )
    def rebuild_mapping_ui(chart_type, token, _mapping_values, _option_values):
        """Regenerate mapping/option widgets for the active chart type."""
        dataset = store.get(token)
        if not chart_type or dataset is None:
            return (
                html.Em("Upload data first.", className="text-muted small"),
                [],
            )
        plot_cls = get_plot(chart_type)
        previous_mapping = _values_by_name(dash.ctx.states_list[0])
        previous_options = _values_by_name(dash.ctx.states_list[1])
        mapping_ui = controls_mapping.build_mapping_controls(
            plot_cls,
            list(dataset.df.columns),
            dataset.column_types,
            previous=previous_mapping,
        )
        options_ui = controls_mapping.build_option_controls(
            plot_cls, previous=previous_options
        )
        return mapping_ui, options_ui

    @app.callback(
        Output("figure-container", "children"),
        Output("plot-error", "children"),
        Output("plot-error", "is_open"),
        Input("dataset-token", "data"),
        Input("chart-type", "value"),
        Input({"type": "mapping", "name": ALL}, "value"),
        Input({"type": "plot-opt", "name": ALL}, "value"),
    )
    def render_figure(token, chart_type, _mapping_values, _option_values):
        """Rebuild the figure from the current control values."""
        dataset = store.get(token)
        if dataset is None or not chart_type or chart_type not in all_plots():
            return _no_data_placeholder(), "", False

        mapping = _values_by_name(dash.ctx.inputs_list[2])
        options = _values_by_name(dash.ctx.inputs_list[3])
        # The mapping widgets rebuild right after a chart-type or dataset
        # change; skip the render until they exist to avoid a flash of
        # 'missing column' errors.
        if not mapping:
            raise dash.exceptions.PreventUpdate

        try:
            fig = build_figure(chart_type, dataset, mapping, options)
        except PlotError as exc:
            return dash.no_update, str(exc), True
        except Exception as exc:  # never leak a traceback to the UI
            return (
                dash.no_update,
                f"Could not build the figure: {exc}",
                True,
            )
        graph = dcc.Graph(id="main-graph", figure=fig, config=GRAPH_CONFIG)
        return graph, "", False
