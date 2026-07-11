"""Violin plot."""

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
from plotforge.plots.box import POINT_CHOICES
from plotforge.plots.registry import register_plot


@register_plot
class ViolinPlot(BasePlot):
    """Density-shaped distribution per category."""

    name = "violin"
    label = "Violin"
    required_mappings = (MappingSpec("y", "Values", ("numeric",)),)
    optional_mappings = (
        MappingSpec("x", "Categories", ("categorical", "datetime")),
        COLOR_CAT,
        FACET_ROW,
        FACET_COL,
    )
    extra_options = (
        OptionSpec("box", "Box overlay", "checkbox", default=True),
        OptionSpec(
            "points",
            "Show points",
            "dropdown",
            default="outliers",
            choices=POINT_CHOICES,
        ),
        OptionSpec(
            "violinmode",
            "Grouped violin layout",
            "dropdown",
            default="group",
            choices=[("Side by side", "group"), ("Overlaid", "overlay")],
        ),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        points = options.get("points", "outliers")
        return px.violin(
            df,
            **clean_mapping(mapping),
            box=bool(options.get("box", True)),
            points=False if points == "none" else points,
            violinmode=options.get("violinmode", "group"),
        )
