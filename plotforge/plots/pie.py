"""Pie / donut chart."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from plotforge.plots.base import BasePlot, MappingSpec, OptionSpec, clean_mapping
from plotforge.plots.registry import register_plot


@register_plot
class PiePlot(BasePlot):
    """Share of each category; values column optional (empty = counts)."""

    name = "pie"
    label = "Pie"
    required_mappings = (MappingSpec("names", "Categories", ("categorical",)),)
    optional_mappings = (
        MappingSpec("values", "Values", ("numeric",), help="Empty = count rows"),
    )
    extra_options = (
        OptionSpec(
            "hole",
            "Donut hole size",
            "slider",
            default=0.0,
            min=0.0,
            max=0.9,
            step=0.05,
        ),
        OptionSpec(
            "textinfo",
            "Slice labels",
            "dropdown",
            default="percent",
            choices=[
                ("Percent", "percent"),
                ("Label", "label"),
                ("Label + percent", "label+percent"),
                ("Value", "value"),
                ("None", "none"),
            ],
        ),
        OptionSpec("sort_slices", "Sort slices by size", "checkbox", default=True),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        m = clean_mapping(mapping)
        plot_df = df
        if "values" not in m:
            # px.pie does not aggregate on its own: with no values column
            # every row becomes a slice, so count rows per category here.
            plot_df = df[m["names"]].value_counts().reset_index(name="count")
            m = {"names": m["names"], "values": "count"}
        fig = px.pie(
            plot_df,
            **m,
            hole=float(options.get("hole") or 0.0),
        )
        fig.update_traces(
            textinfo=options.get("textinfo", "percent"),
            sort=bool(options.get("sort_slices", True)),
        )
        return fig
