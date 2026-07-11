"""Scatter plot."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from plotforge.plots.base import (
    COLOR,
    FACET_COL,
    FACET_ROW,
    SIZE,
    SYMBOL,
    BasePlot,
    MappingSpec,
    OptionSpec,
    clean_mapping,
)
from plotforge.plots.registry import register_plot


@register_plot
class ScatterPlot(BasePlot):
    """Classic x/y scatter with optional grouping, sizing, and faceting."""

    name = "scatter"
    label = "Scatter"
    required_mappings = (
        MappingSpec("x", "X", ("numeric", "datetime")),
        MappingSpec("y", "Y", ("numeric",)),
    )
    optional_mappings = (COLOR, SIZE, SYMBOL, FACET_ROW, FACET_COL)
    extra_options = (
        OptionSpec(
            "marker_size",
            "Marker size",
            "slider",
            default=8,
            min=2,
            max=24,
            step=1,
        ),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        fig = px.scatter(df, **clean_mapping(mapping))
        # A 'size' column drives marker size per-point; the slider only
        # applies when no size mapping is set.
        if not mapping.get("size"):
            fig.update_traces(marker_size=options.get("marker_size", 8))
        return fig
