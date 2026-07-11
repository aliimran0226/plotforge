"""Box plot."""

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

#: Dropdown choices shared with the violin plot.
POINT_CHOICES = [
    ("Outliers only", "outliers"),
    ("Suspected outliers", "suspectedoutliers"),
    ("All points", "all"),
    ("None", "none"),
]


@register_plot
class BoxPlot(BasePlot):
    """Distribution summary per category, with optional notches/points."""

    name = "box"
    label = "Box"
    required_mappings = (MappingSpec("y", "Values", ("numeric",)),)
    optional_mappings = (
        MappingSpec("x", "Categories", ("categorical", "datetime")),
        COLOR_CAT,
        FACET_ROW,
        FACET_COL,
    )
    extra_options = (
        OptionSpec(
            "points",
            "Show points",
            "dropdown",
            default="outliers",
            choices=POINT_CHOICES,
        ),
        OptionSpec("notched", "Notched boxes", "checkbox", default=False),
        OptionSpec(
            "boxmode",
            "Grouped box layout",
            "dropdown",
            default="group",
            choices=[("Side by side", "group"), ("Overlaid", "overlay")],
        ),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        points = options.get("points", "outliers")
        return px.box(
            df,
            **clean_mapping(mapping),
            # px expects points=False (not a string) to hide them.
            points=False if points == "none" else points,
            notched=bool(options.get("notched", False)),
            boxmode=options.get("boxmode", "group"),
        )
