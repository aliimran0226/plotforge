"""Density contour / 2D histogram."""

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
class DensityPlot(BasePlot):
    """Joint distribution of two numeric columns."""

    name = "density"
    label = "Density (2D)"
    required_mappings = (
        MappingSpec("x", "X", ("numeric", "datetime")),
        MappingSpec("y", "Y", ("numeric",)),
    )
    optional_mappings = (COLOR_CAT, FACET_ROW, FACET_COL)
    extra_options = (
        OptionSpec(
            "kind",
            "Representation",
            "dropdown",
            default="contour",
            choices=[
                ("Contour lines", "contour"),
                ("Filled contours", "filled"),
                ("2D histogram", "histogram"),
            ],
        ),
        OptionSpec("nbinsx", "X bins", "number", default=None, min=2, max=200),
        OptionSpec("nbinsy", "Y bins", "number", default=None, min=2, max=200),
    )

    @classmethod
    def validate(cls, mapping, column_types, options=None) -> None:
        super().validate(mapping, column_types, options)
        # px forbids filled contours with a discrete color mapping (the
        # groups' fills would hide each other), so refuse it up front.
        if (options or {}).get("kind") == "filled" and mapping.get("color"):
            raise PlotError(
                "Filled contours cannot be split by 'Color / group' - the "
                "filled regions would hide each other. Switch the "
                "representation to contour lines, or clear the Color mapping."
            )

    @classmethod
    def build(cls, df: pd.DataFrame, mapping: dict, options: dict) -> go.Figure:
        m = clean_mapping(mapping)
        nbinsx = options.get("nbinsx")
        nbinsy = options.get("nbinsy")
        bins = dict(
            nbinsx=int(nbinsx) if nbinsx else None,
            nbinsy=int(nbinsy) if nbinsy else None,
        )
        kind = options.get("kind", "contour")
        if kind == "histogram":
            return px.density_heatmap(df, **m, **bins)
        fig = px.density_contour(df, **m, **bins)
        if kind == "filled":
            # Filled contours use the continuous colorscale; a discrete
            # color mapping would fight it, so px only allows this
            # combination without 'color'.
            fig.update_traces(contours_coloring="fill", contours_showlabels=False)
        return fig
