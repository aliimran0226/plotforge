"""Stacked / normalized area chart."""

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
class AreaPlot(BasePlot):
    """Filled line chart; groups stack (or normalize to shares)."""

    name = "area"
    label = "Area"
    required_mappings = (
        MappingSpec("x", "X", ("numeric", "datetime", "categorical")),
        MappingSpec("y", "Y", ("numeric",)),
    )
    optional_mappings = (COLOR_CAT, FACET_ROW, FACET_COL)
    extra_options = (
        OptionSpec(
            "groupnorm",
            "Stacking",
            "dropdown",
            default="",
            choices=[
                ("Stacked values", ""),
                ("Fraction of total", "fraction"),
                ("Percent of total", "percent"),
            ],
        ),
        OptionSpec(
            "line_shape",
            "Line shape",
            "dropdown",
            default="linear",
            choices=[
                ("Straight", "linear"),
                ("Smooth (spline)", "spline"),
                ("Steps", "hv"),
            ],
        ),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        m = clean_mapping(mapping)
        plot_df = df.sort_values(m["x"], kind="stable")
        return px.area(
            plot_df,
            **m,
            groupnorm=options.get("groupnorm") or None,
            line_shape=options.get("line_shape", "linear"),
        )
