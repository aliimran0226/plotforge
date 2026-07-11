"""Histogram."""

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
class HistogramPlot(BasePlot):
    """Distribution of one column, with bin and normalization control."""

    name = "histogram"
    label = "Histogram"
    required_mappings = (
        MappingSpec("x", "Values", ("numeric", "datetime", "categorical")),
    )
    optional_mappings = (COLOR_CAT, FACET_ROW, FACET_COL)
    extra_options = (
        OptionSpec(
            "nbins", "Number of bins", "number", default=None, min=1, max=500, step=1
        ),
        OptionSpec(
            "histnorm",
            "Normalization",
            "dropdown",
            default="",
            choices=[
                ("Count", ""),
                ("Percent", "percent"),
                ("Probability", "probability"),
                ("Density", "density"),
                ("Probability density", "probability density"),
            ],
        ),
        OptionSpec(
            "barmode",
            "Overlap mode (grouped)",
            "dropdown",
            default="overlay",
            choices=[
                ("Overlaid", "overlay"),
                ("Stacked", "stack"),
                ("Side by side", "group"),
            ],
        ),
        OptionSpec("cumulative", "Cumulative", "checkbox", default=False),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        nbins = options.get("nbins")
        fig = px.histogram(
            df,
            **clean_mapping(mapping),
            nbins=int(nbins) if nbins else None,
            histnorm=options.get("histnorm") or None,
            barmode=options.get("barmode", "overlay"),
            cumulative=bool(options.get("cumulative", False)),
        )
        # Overlaid histograms need transparency to stay readable.
        if mapping.get("color") and options.get("barmode", "overlay") == "overlay":
            fig.update_traces(opacity=0.7)
        return fig
