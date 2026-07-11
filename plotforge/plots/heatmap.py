"""Heatmap, from long (x/y/z) or wide (matrix) data."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from plotforge.plots.base import (
    ANY_KIND,
    BasePlot,
    MappingSpec,
    OptionSpec,
    PlotError,
    clean_mapping,
)
from plotforge.plots.registry import register_plot


@register_plot
class HeatmapPlot(BasePlot):
    """Matrix heatmap.

    Two data shapes:

    - **Long** (default): pick X, Y, and a numeric Z; duplicate (x, y)
      pairs are aggregated. Z left empty counts co-occurrences.
    - **Wide**: enable 'Wide matrix' to use every numeric column as the
      matrix, with an optional label column for the rows.
    """

    name = "heatmap"
    label = "Heatmap"
    # All slots optional: long mode needs x+y (checked in validate),
    # wide mode ignores x/y entirely.
    required_mappings = ()
    optional_mappings = (
        MappingSpec("x", "X (long data)", ANY_KIND),
        MappingSpec("y", "Y (long data)", ANY_KIND),
        MappingSpec(
            "z", "Values (long data)", ("numeric",), help="Empty = count pairs"
        ),
        MappingSpec("row_label", "Row labels (wide data)", ("categorical",)),
    )
    extra_options = (
        OptionSpec(
            "wide", "Wide matrix (all numeric columns)", "checkbox", default=False
        ),
        OptionSpec(
            "aggfunc",
            "Aggregate duplicates by",
            "dropdown",
            default="mean",
            choices=[("Mean", "mean"), ("Median", "median"), ("Sum", "sum")],
        ),
        OptionSpec("show_values", "Show cell values", "checkbox", default=False),
    )

    @classmethod
    def validate(cls, mapping, column_types, options=None) -> None:
        super().validate(mapping, column_types, options)
        if not (options or {}).get("wide"):
            if not mapping.get("x") or not mapping.get("y"):
                raise PlotError(
                    "Heatmap needs X and Y columns (long data), or enable "
                    "'Wide matrix' to use all numeric columns."
                )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        m = clean_mapping(mapping)
        text_auto = ".3g" if options.get("show_values") else False

        if options.get("wide"):
            matrix = df.select_dtypes("number")
            if matrix.empty:
                raise PlotError(
                    "Wide-matrix heatmap needs at least one numeric column."
                )
            if m.get("row_label"):
                matrix = matrix.set_axis(df[m["row_label"]].astype(str), axis=0)
            return px.imshow(matrix, text_auto=text_auto, aspect="auto")

        x, y, z = m["x"], m["y"], m.get("z")
        if z:
            pivot = df.pivot_table(
                index=y,
                columns=x,
                values=z,
                aggfunc=options.get("aggfunc", "mean"),
                observed=True,
            )
        else:
            pivot = pd.crosstab(df[y], df[x])
        return px.imshow(pivot, text_auto=text_auto, aspect="auto")
