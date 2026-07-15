"""Pie / donut chart."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from plotforge import config
from plotforge.plots.base import (
    BasePlot,
    MappingSpec,
    OptionSpec,
    PlotError,
    clean_mapping,
)
from plotforge.plots.registry import register_plot

#: Internal name for the derived count column; guaranteed not to collide
#: with a real column (px shows it as 'count' via labels=).
_COUNT_COL = "__plotforge_count__"


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
        names = m["names"]
        labels = {}
        # px.pie does not aggregate on its own: duplicate category rows
        # become duplicate slices (and slice colors misalign once
        # plotly.js merges them), so aggregate to one row per category.
        if "values" in m:
            plot_df = df.groupby(names, as_index=False, observed=True)[
                m["values"]
            ].sum()
        else:
            plot_df = df[names].value_counts().reset_index(name=_COUNT_COL)
            m = {"names": names, "values": _COUNT_COL}
            labels = {_COUNT_COL: "count"}
        if len(plot_df) > config.MAX_CATEGORIES:
            raise PlotError(
                f"'{names}' has {len(plot_df)} categories - a pie with more "
                f"than {config.MAX_CATEGORIES} slices is unreadable. Pick a "
                "column with fewer categories."
            )
        fig = px.pie(
            plot_df,
            **m,
            labels=labels,
            hole=float(options.get("hole") or 0.0),
        )
        fig.update_traces(
            textinfo=options.get("textinfo", "percent"),
            sort=bool(options.get("sort_slices", True)),
        )
        return fig
