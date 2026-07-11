"""Empirical cumulative distribution (ECDF)."""

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
class EcdfPlot(BasePlot):
    """Cumulative fraction of observations at or below each value."""

    name = "ecdf"
    label = "ECDF"
    required_mappings = (MappingSpec("x", "Values", ("numeric", "datetime")),)
    optional_mappings = (COLOR_CAT, FACET_ROW, FACET_COL)
    extra_options = (
        OptionSpec(
            "ecdfnorm",
            "Y axis shows",
            "dropdown",
            default="probability",
            choices=[
                ("Probability (0-1)", "probability"),
                ("Percent (0-100)", "percent"),
                ("Count", "none"),
            ],
        ),
        OptionSpec(
            "complementary", "Complementary (1 - ECDF)", "checkbox", default=False
        ),
        OptionSpec("markers", "Show markers", "checkbox", default=False),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        norm = options.get("ecdfnorm", "probability")
        return px.ecdf(
            df,
            **clean_mapping(mapping),
            ecdfnorm=None if norm == "none" else norm,
            ecdfmode=("complementary" if options.get("complementary") else "standard"),
            markers=bool(options.get("markers", False)),
        )
