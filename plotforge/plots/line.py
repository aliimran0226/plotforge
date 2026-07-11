"""Line plot."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from plotforge.plots.base import (
    COLOR,
    FACET_COL,
    FACET_ROW,
    BasePlot,
    MappingSpec,
    OptionSpec,
    clean_mapping,
)
from plotforge.plots.registry import register_plot


@register_plot
class LinePlot(BasePlot):
    """Line chart; rows are sorted by x so lines never zig-zag backwards."""

    name = "line"
    label = "Line"
    required_mappings = (
        MappingSpec("x", "X", ("numeric", "datetime", "categorical")),
        MappingSpec("y", "Y", ("numeric",)),
    )
    optional_mappings = (COLOR, FACET_ROW, FACET_COL)
    extra_options = (
        OptionSpec("markers", "Show markers", "checkbox", default=False),
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
        OptionSpec(
            "line_width", "Line width", "slider", default=2, min=1, max=8, step=0.5
        ),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        m = clean_mapping(mapping)
        plot_df = df.sort_values(m["x"], kind="stable")
        fig = px.line(
            plot_df,
            **m,
            markers=bool(options.get("markers", False)),
            line_shape=options.get("line_shape", "linear"),
        )
        fig.update_traces(line_width=options.get("line_width", 2))
        return fig
