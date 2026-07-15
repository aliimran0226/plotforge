"""Callbacks for the Chart section and the live figure.

Two callbacks:

1. ``rebuild_mapping_ui`` - regenerates the mapping dropdowns and
   chart-specific option widgets whenever the chart type or the dataset
   changes, carrying over compatible selections.
2. ``render_figure`` - the single live-update callback: reads the
   current mapping + options + style controls, asks the registry to
   build the figure, passes it through ``apply_style``, and renders it.
"""

from __future__ import annotations

import dash
from dash import ALL, Input, Output, State, dcc, html

from plotforge.data import store
from plotforge.plots.base import PlotError, clean_mapping, merged_options
from plotforge.plots.registry import all_plots, get_plot
from plotforge.styling import style_model
from plotforge.styling.apply import apply_style
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


def _entry_list(pattern_list: list[dict]) -> list[dict]:
    """Decoration pattern entries -> ordered list of {prop: value} dicts."""
    grouped = style_model.entries_by_index(pattern_list)
    return [grouped[i] for i in sorted(grouped)]


def _style_from_pattern_lists(pattern_lists: list) -> style_model.StyleModel:
    """Build the StyleModel from ctx inputs/states lists.

    Render and export declare their pattern dependencies in the same
    order, so indices 4-8 are: style fields, group colors, reference
    lines, bands, annotations.
    """
    style_values = {item["id"]["field"]: item.get("value") for item in pattern_lists[4]}
    group_colors = {
        item["id"]["group"]: item.get("value")
        for item in pattern_lists[5]
        if item.get("value")
    }
    decorations = {
        "ref_lines": _entry_list(pattern_lists[6]),
        "ref_bands": _entry_list(pattern_lists[7]),
        "annotations": _entry_list(pattern_lists[8]),
    }
    return style_model.from_values(style_values, group_colors, decorations)


def _no_data_placeholder() -> html.P:
    return html.P(
        "Upload a data file to get started.",
        className="text-muted text-center mt-5",
    )


def build_figure(
    chart_type: str,
    dataset: store.Dataset,
    mapping: dict,
    options: dict,
    style: style_model.StyleModel | None = None,
):
    """Pure figure-building path shared by render and export.

    Returns a fully styled plotly Figure. Raises PlotError for
    user-fixable issues.
    """
    plot_cls = get_plot(chart_type)
    mapping = clean_mapping(mapping)
    options = merged_options(plot_cls, options)
    plot_cls.validate(mapping, dataset.column_types, options)
    fig = plot_cls.build(dataset.df, mapping, options)
    return apply_style(fig, style or style_model.StyleModel())


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
        Input({"type": "style", "field": ALL}, "value"),
        Input({"type": "group-color", "group": ALL}, "value"),
        Input({"type": "decor-line", "idx": ALL, "prop": ALL}, "value"),
        Input({"type": "decor-band", "idx": ALL, "prop": ALL}, "value"),
        Input({"type": "decor-annot", "idx": ALL, "prop": ALL}, "value"),
    )
    def render_figure(token, chart_type, *_pattern_values):
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

        style = _style_from_pattern_lists(dash.ctx.inputs_list)

        try:
            fig = build_figure(chart_type, dataset, mapping, options, style)
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
