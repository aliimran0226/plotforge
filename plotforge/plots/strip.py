"""Strip / jitter plot."""

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
class StripPlot(BasePlot):
    """Individual points jittered within each category."""

    name = "strip"
    label = "Strip / Jitter"
    required_mappings = (MappingSpec("y", "Values", ("numeric",)),)
    optional_mappings = (
        MappingSpec("x", "Categories", ("categorical", "datetime")),
        COLOR_CAT,
        FACET_ROW,
        FACET_COL,
    )
    extra_options = (
        OptionSpec(
            "stripmode",
            "Grouped strip layout",
            "dropdown",
            default="group",
            choices=[("Side by side", "group"), ("Overlaid", "overlay")],
        ),
        OptionSpec(
            "marker_size", "Marker size", "slider", default=6, min=2, max=20, step=1
        ),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        fig = px.strip(
            df,
            **clean_mapping(mapping),
            stripmode=options.get("stripmode", "group"),
        )
        fig.update_traces(marker_size=options.get("marker_size", 6))
        return fig
