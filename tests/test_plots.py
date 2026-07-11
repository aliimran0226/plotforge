"""Every registered plot builds a valid figure on the fixture data.

Parametrized over the registry, so new chart types are covered the
moment they register - each just needs an entry in ``SMOKE_MAPPINGS``.
"""

from __future__ import annotations

import plotly.graph_objects as go
import pytest

import plotforge.plots  # noqa: F401  (registers the built-in chart types)
from plotforge.plots.base import merged_options
from plotforge.plots.registry import all_plots, get_plot

#: Chart name -> a sensible mapping for the sample fixture frame
#: (columns: dose, response, response_err, group, batch, measured_on).
SMOKE_MAPPINGS: dict[str, dict[str, str]] = {
    "scatter": {"x": "dose", "y": "response", "color": "group"},
    "line": {"x": "measured_on", "y": "response", "color": "group"},
    "bar": {"x": "group", "y": "response", "color": "batch"},
    "histogram": {"x": "response", "color": "group"},
}


def test_all_registered_plots_have_smoke_mapping():
    """Force a test entry for every new chart type."""
    missing = set(all_plots()) - set(SMOKE_MAPPINGS)
    assert not missing, f"Add SMOKE_MAPPINGS entries for: {sorted(missing)}"


@pytest.mark.parametrize("name", sorted(SMOKE_MAPPINGS))
def test_plot_builds_figure(name, sample_df):
    plot_cls = get_plot(name)
    mapping = SMOKE_MAPPINGS[name]
    fig = plot_cls.build(sample_df, mapping, merged_options(plot_cls, {}))
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


@pytest.mark.parametrize("name", sorted(SMOKE_MAPPINGS))
def test_plot_builds_without_optional_mappings(name, sample_df):
    """Required mappings alone must be enough to build."""
    plot_cls = get_plot(name)
    mapping = {
        spec.name: SMOKE_MAPPINGS[name][spec.name]
        for spec in plot_cls.required_mappings
    }
    fig = plot_cls.build(sample_df, mapping, merged_options(plot_cls, {}))
    assert isinstance(fig, go.Figure)


def test_bar_counts_when_no_y(sample_df):
    bar = get_plot("bar")
    fig = bar.build(sample_df, {"x": "group"}, merged_options(bar, {}))
    total = sum(sum(trace.y) for trace in fig.data)
    assert total == len(sample_df)


def test_bar_aggregates_mean(sample_df):
    bar = get_plot("bar")
    fig = bar.build(
        sample_df,
        {"x": "group"},
        merged_options(bar, {"aggfunc": "mean"}) | {"aggfunc": "mean"},
    )
    assert isinstance(fig, go.Figure)


def test_histogram_options(sample_df):
    hist = get_plot("histogram")
    fig = hist.build(
        sample_df,
        {"x": "response"},
        {"nbins": 12, "histnorm": "percent", "barmode": "overlay", "cumulative": True},
    )
    assert isinstance(fig, go.Figure)


def test_scatter_facets(sample_df):
    scatter = get_plot("scatter")
    fig = scatter.build(
        sample_df,
        {"x": "dose", "y": "response", "facet_col": "batch"},
        merged_options(scatter, {}),
    )
    # Faceting produces one x-axis per facet column value.
    assert len(fig.layout.annotations) >= 2
