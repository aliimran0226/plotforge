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
    "box": {"y": "response", "x": "group", "color": "batch"},
    "violin": {"y": "response", "x": "group", "color": "batch"},
    "strip": {"y": "response", "x": "group", "color": "batch"},
    "heatmap": {"x": "group", "y": "batch", "z": "response"},
    "density": {"x": "dose", "y": "response"},
    "ecdf": {"x": "response", "color": "group"},
    "area": {"x": "measured_on", "y": "response", "color": "group"},
    "pie": {"names": "group", "values": "dose"},
    "errorbar": {"x": "dose", "y": "response", "error_y": "response_err"},
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
    if not plot_cls.required_mappings:
        pytest.skip(f"{name} has mode-dependent requirements")
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


# ---------------------------------------------------------------------------
# Type-specific behaviors added with the full chart set
# ---------------------------------------------------------------------------


def test_heatmap_long_counts_when_no_z(sample_df):
    heat = get_plot("heatmap")
    fig = heat.build(sample_df, {"x": "group", "y": "batch"}, merged_options(heat, {}))
    assert fig.data[0].type == "heatmap"


def test_heatmap_wide_matrix(sample_df):
    heat = get_plot("heatmap")
    opts = merged_options(heat, {"wide": True})
    fig = heat.build(sample_df, {"row_label": "group"}, opts)
    assert fig.data[0].type == "heatmap"


def test_heatmap_validate_long_needs_xy(sample_df):
    from plotforge.plots.base import PlotError

    heat = get_plot("heatmap")
    types = {"group": "categorical", "batch": "categorical"}
    with pytest.raises(PlotError, match="Wide matrix"):
        heat.validate({}, types, merged_options(heat, {}))
    # Wide mode is fine without x/y.
    heat.validate({}, types, merged_options(heat, {"wide": True}))


def test_pie_counts_when_no_values(sample_df):
    pie = get_plot("pie")
    fig = pie.build(sample_df, {"names": "group"}, merged_options(pie, {}))
    assert sum(fig.data[0].values) == len(sample_df)


def test_pie_donut_hole(sample_df):
    pie = get_plot("pie")
    fig = pie.build(sample_df, {"names": "group"}, merged_options(pie, {"hole": 0.4}))
    assert fig.data[0].hole == 0.4


def test_errorbar_carries_error_column(sample_df):
    eb = get_plot("errorbar")
    fig = eb.build(
        sample_df,
        {"x": "dose", "y": "response", "error_y": "response_err"},
        merged_options(eb, {}),
    )
    assert fig.data[0].error_y.array is not None


def test_density_kinds(sample_df):
    dens = get_plot("density")
    for kind, trace_type in [
        ("contour", "histogram2dcontour"),
        ("filled", "histogram2dcontour"),
        ("histogram", "histogram2d"),
    ]:
        fig = dens.build(
            sample_df,
            {"x": "dose", "y": "response"},
            merged_options(dens, {"kind": kind}),
        )
        assert fig.data[0].type == trace_type


def test_box_points_none_maps_to_false(sample_df):
    box = get_plot("box")
    fig = box.build(
        sample_df,
        {"y": "response", "x": "group"},
        merged_options(box, {"points": "none"}),
    )
    assert fig.data[0].boxpoints is False
