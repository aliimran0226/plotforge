"""Scatter / line with error bars mapped from data columns."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from plotforge.plots.base import (
    COLOR_CAT,
    FACET_COL,
    FACET_ROW,
    BasePlot,
    MappingSpec,
    OptionSpec,
    clean_mapping,
)
from plotforge.plots.registry import register_plot


@register_plot
class ErrorBarPlot(BasePlot):
    """x/y points (or lines) with symmetric error bars from columns."""

    name = "errorbar"
    label = "Error bars"
    required_mappings = (
        MappingSpec("x", "X", ("numeric", "datetime")),
        MappingSpec("y", "Y", ("numeric",)),
    )
    optional_mappings = (
        MappingSpec("error_y", "Y error (±)", ("numeric",)),
        MappingSpec("error_x", "X error (±)", ("numeric",)),
        COLOR_CAT,
        FACET_ROW,
        FACET_COL,
    )
    extra_options = (
        OptionSpec(
            "mode",
            "Draw as",
            "dropdown",
            default="markers",
            choices=[
                ("Points", "markers"),
                ("Lines", "lines"),
                ("Lines + points", "lines+markers"),
            ],
        ),
        OptionSpec(
            "marker_size", "Marker size", "slider", default=8, min=2, max=24, step=1
        ),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        m = clean_mapping(mapping)
        mode = options.get("mode", "markers")
        # Sort so connecting lines run left to right.
        plot_df = df.sort_values(m["x"], kind="stable") if "lines" in mode else df
        fig = px.scatter(plot_df, **m)
        fig.update_traces(mode=mode, marker_size=options.get("marker_size", 8))
        return fig
