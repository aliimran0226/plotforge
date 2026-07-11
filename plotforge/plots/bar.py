"""Bar chart (grouped/stacked) with optional aggregation."""

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
    PlotError,
    clean_mapping,
)
from plotforge.plots.registry import register_plot


@register_plot
class BarPlot(BasePlot):
    """Bar chart of a value column (aggregated) or of row counts.

    If no Y column is chosen, bars show row counts per category.
    Otherwise the chosen aggregation is applied per category/group.
    """

    name = "bar"
    label = "Bar"
    required_mappings = (
        MappingSpec("x", "X (categories)", ("categorical", "datetime", "numeric")),
    )
    optional_mappings = (
        MappingSpec("y", "Y (values)", ("numeric",), help="Empty = count rows"),
        COLOR_CAT,
        FACET_ROW,
        FACET_COL,
    )
    extra_options = (
        OptionSpec(
            "barmode",
            "Bar mode",
            "dropdown",
            default="group",
            choices=[
                ("Grouped", "group"),
                ("Stacked", "stack"),
                ("Overlaid", "overlay"),
                ("Relative", "relative"),
            ],
        ),
        OptionSpec(
            "aggfunc",
            "Aggregate values by",
            "dropdown",
            default="mean",
            choices=[
                ("Mean", "mean"),
                ("Median", "median"),
                ("Sum", "sum"),
                ("Min", "min"),
                ("Max", "max"),
            ],
        ),
    )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        m = clean_mapping(mapping)
        group_cols = [m[k] for k in ("x", "color", "facet_row", "facet_col") if k in m]
        # De-duplicate while preserving order (same column may fill two slots).
        group_cols = list(dict.fromkeys(group_cols))

        y = m.get("y")
        if y:
            aggfunc = options.get("aggfunc", "mean")
            try:
                plot_df = df.groupby(group_cols, as_index=False, observed=True)[y].agg(
                    aggfunc
                )
            except (TypeError, ValueError) as exc:
                raise PlotError(
                    f"Could not aggregate '{y}' with {aggfunc}: {exc}"
                ) from exc
        else:
            # No value column: bar height = number of rows per category.
            y = "count"
            plot_df = df.groupby(group_cols, as_index=False, observed=True).size()
            plot_df = plot_df.rename(columns={"size": y})

        fig = px.bar(
            plot_df,
            y=y,
            **{k: v for k, v in m.items() if k != "y"},
            barmode=options.get("barmode", "group"),
        )
        return fig
