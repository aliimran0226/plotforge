"""Tests for StyleModel conversion and apply_style behavior."""

from __future__ import annotations

import plotly.express as px
import pytest

from plotforge.styling import style_model
from plotforge.styling.apply import apply_style, palette_colors


@pytest.fixture()
def grouped_fig(sample_df):
    return px.scatter(sample_df, x="dose", y="response", color="group")


# ---------------------------------------------------------------------------
# StyleModel.from_values
# ---------------------------------------------------------------------------


def test_from_values_coerces_types():
    style = style_model.from_values(
        {"width": "900", "x_log": 1, "opacity": "0.5", "x_min": "", "x_max": None}
    )
    assert style.width == 900 and isinstance(style.width, int)
    assert style.x_log is True
    assert style.opacity == 0.5
    assert style.x_min is None and style.x_max is None


def test_from_values_ignores_junk():
    style = style_model.from_values({"width": "not-a-number", "bogus_field": 3})
    assert style.width == style_model.StyleModel().width
    assert not hasattr(style, "bogus_field")


def test_from_values_group_colors():
    style = style_model.from_values({}, {"control": "#ff0000"})
    assert style.group_colors == {"control": "#ff0000"}


def test_defaults_by_field_covers_all_fields():
    from dataclasses import fields

    defaults = style_model.defaults_by_field()
    assert set(defaults) == {f.name for f in fields(style_model.StyleModel)}


# ---------------------------------------------------------------------------
# apply_style
# ---------------------------------------------------------------------------


def test_apply_geometry_and_title(grouped_fig):
    style = style_model.StyleModel(
        width=640, height=480, title_text="Hello", title_align="left"
    )
    fig = apply_style(grouped_fig, style)
    assert fig.layout.width == 640
    assert fig.layout.height == 480
    assert fig.layout.title.text == "Hello"
    assert fig.layout.title.xanchor == "left"


def test_apply_axis_range_and_log(grouped_fig):
    style = style_model.StyleModel(x_min=1.0, x_max=100.0, x_log=True)
    fig = apply_style(grouped_fig, style)
    assert fig.layout.xaxis.type == "log"
    assert fig.layout.xaxis.range == (0.0, 2.0)  # log10 units


def test_apply_reversed_axis(grouped_fig):
    fig = apply_style(grouped_fig, style_model.StyleModel(y_reversed=True))
    assert fig.layout.yaxis.autorange == "reversed"


def test_apply_palette_recolors_groups(grouped_fig):
    style = style_model.StyleModel(palette="Safe (colorblind)")
    fig = apply_style(grouped_fig, style)
    safe = palette_colors("Safe (colorblind)")
    trace_colors = {t.marker.color for t in fig.data}
    assert trace_colors <= set(safe)
    assert len(trace_colors) == len(fig.data)  # distinct color per group


def test_apply_group_color_override(grouped_fig):
    name = grouped_fig.data[0].name
    style = style_model.StyleModel(group_colors_on=True, group_colors={name: "#123456"})
    fig = apply_style(grouped_fig, style)
    assert fig.data[0].marker.color == "#123456"


def test_group_override_ignored_when_off(grouped_fig):
    name = grouped_fig.data[0].name
    style = style_model.StyleModel(
        group_colors_on=False, group_colors={name: "#123456"}
    )
    fig = apply_style(grouped_fig, style)
    assert fig.data[0].marker.color != "#123456"


def test_apply_legend_hidden(grouped_fig):
    fig = apply_style(grouped_fig, style_model.StyleModel(legend_show=False))
    assert fig.layout.showlegend is False


def test_apply_legend_position(grouped_fig):
    fig = apply_style(grouped_fig, style_model.StyleModel(legend_position="below"))
    assert fig.layout.legend.orientation == "v"  # orientation independent
    assert fig.layout.legend.xanchor == "center"


def test_apply_opacity(grouped_fig):
    fig = apply_style(grouped_fig, style_model.StyleModel(opacity=0.4))
    assert all(t.opacity == 0.4 for t in fig.data)


def test_apply_representative_everything(grouped_fig):
    """One pass with most options set - must not raise."""
    style = style_model.StyleModel(
        width=1000,
        height=700,
        template="simple_white",
        title_text="Everything",
        title_size=24,
        font_family="Georgia",
        x_title="Dose (mg)",
        x_tick_angle=45,
        x_tick_format=".1f",
        x_grid=False,
        x_mirror=True,
        y_min=0.0,
        y_max=100.0,
        y_zeroline=True,
        palette="D3",
        opacity=0.8,
        legend_position="inside-top-right",
        legend_orientation="h",
        legend_title="Groups",
    )
    fig = apply_style(grouped_fig, style)
    assert fig.layout.xaxis.title.text == "Dose (mg)"
    assert fig.layout.yaxis.range == (0.0, 100.0)
    assert fig.layout.legend.title.text == "Groups"
