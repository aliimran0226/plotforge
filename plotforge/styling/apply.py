"""apply_style(fig, style): apply a StyleModel to any figure.

Works on whatever ``BasePlot.build()`` returns - including faceted
figures (``update_xaxes``/``update_yaxes`` hit every subplot axis) and
mixed trace types.

Color-control philosophy: most controls are authoritative (what the
control says is what the figure gets). The exceptions are the
background and gridline *colors*: those are only applied when the user
moved them off the PlotForge default, so picking a template like
'seaborn' keeps its signature backgrounds until the user explicitly
overrides them. (A color input has no way to say "auto", hence this
compromise - see tool_structure.md.)
"""

from __future__ import annotations

import math

import plotly.express as px
import plotly.graph_objects as go

from plotforge import config
from plotforge.styling.style_model import StyleModel

#: Legend position name -> plotly legend layout fragment.
_LEGEND_POSITIONS: dict[str, dict] = {
    "outside-right": dict(x=1.02, y=1.0, xanchor="left", yanchor="top"),
    "below": dict(x=0.5, y=-0.15, xanchor="center", yanchor="top"),
    "inside-top-left": dict(x=0.02, y=0.98, xanchor="left", yanchor="top"),
    "inside-top-right": dict(x=0.98, y=0.98, xanchor="right", yanchor="top"),
    "inside-bottom-left": dict(x=0.02, y=0.02, xanchor="left", yanchor="bottom"),
    "inside-bottom-right": dict(x=0.98, y=0.02, xanchor="right", yanchor="bottom"),
}

#: Title alignment -> title.x / xanchor.
_TITLE_ALIGN: dict[str, dict] = {
    "left": dict(x=0.02, xanchor="left"),
    "center": dict(x=0.5, xanchor="center"),
    "right": dict(x=0.98, xanchor="right"),
}

#: Trace types whose own colorscale should follow the continuous picker.
_CONTINUOUS_TRACES = {"heatmap", "histogram2d", "histogram2dcontour", "contour"}

_DEFAULTS = StyleModel()


def palette_colors(palette_label: str) -> list[str]:
    """Resolve a palette label from config to its list of colors."""
    attr = config.QUALITATIVE_PALETTES.get(
        palette_label, config.DEFAULT_QUALITATIVE_PALETTE
    )
    return list(getattr(px.colors.qualitative, attr, px.colors.qualitative.Plotly))


def apply_style(fig: go.Figure, style: StyleModel) -> go.Figure:
    """Apply every StyleModel field to ``fig`` (mutates and returns it)."""
    # Template first so all explicit settings below win over it.
    fig.update_layout(template=style.template)

    fig.update_layout(
        width=style.width,
        height=style.height,
        margin=dict(
            l=style.margin_l, r=style.margin_r, t=style.margin_t, b=style.margin_b
        ),
        font_family=style.font_family,
    )
    # Background colors: only when moved off the default (see module doc).
    if style.paper_bgcolor.lower() != _DEFAULTS.paper_bgcolor:
        fig.update_layout(paper_bgcolor=style.paper_bgcolor)
    if style.plot_bgcolor.lower() != _DEFAULTS.plot_bgcolor:
        fig.update_layout(plot_bgcolor=style.plot_bgcolor)

    _apply_title(fig, style)
    _apply_axis(fig, style, "x")
    _apply_axis(fig, style, "y")
    _apply_colors(fig, style)
    _apply_legend(fig, style)
    return fig


def _apply_title(fig: go.Figure, style: StyleModel) -> None:
    """Figure title text, size, color, and alignment."""
    if not style.title_text:
        fig.update_layout(title_text="")
        return
    align = _TITLE_ALIGN.get(style.title_align, _TITLE_ALIGN["center"])
    fig.update_layout(
        title=dict(
            text=style.title_text,
            font=dict(size=style.title_size, color=style.title_color),
            **align,
        )
    )


def _axis_range(
    lo: float | None, hi: float | None, log: bool, reverse: bool
) -> list[float] | None:
    """Explicit axis range, converted to log10 units for log axes."""
    if lo is None or hi is None:
        return None
    if log:
        # Plotly expects log-axis ranges as exponents; guard against
        # non-positive bounds which have no log.
        if lo <= 0 or hi <= 0:
            return None
        lo, hi = math.log10(lo), math.log10(hi)
    return [hi, lo] if reverse else [lo, hi]


def _apply_axis(fig: go.Figure, style: StyleModel, which: str) -> None:
    """Apply the x_* or y_* fields to every matching axis (incl. facets)."""
    s = {k[2:]: v for k, v in vars(style).items() if k.startswith(which + "_")}

    kwargs: dict = dict(
        type="log" if s["log"] else "linear",
        tickfont_size=s["tick_size"],
        showgrid=s["grid"],
        zeroline=s["zeroline"],
        showline=s["line"],
        mirror=s["mirror"],
        title_font_size=style.axis_title_size,
    )
    if s["title"]:
        # Only the outer/first axis gets the title override; px already
        # titles facet axes sensibly, and update_*axes would title all.
        pass  # handled below via explicit layout access
    if s["tick_angle"] is not None:
        kwargs["tickangle"] = s["tick_angle"]
    if s["tick_format"]:
        kwargs["tickformat"] = s["tick_format"]
    if s["grid_color"].lower() != getattr(_DEFAULTS, f"{which}_grid_color"):
        kwargs["gridcolor"] = s["grid_color"]

    rng = _axis_range(s["min"], s["max"], s["log"], s["reversed"])
    if rng is not None:
        kwargs["range"] = rng
        kwargs["autorange"] = False
    elif s["reversed"]:
        kwargs["autorange"] = "reversed"

    updater = fig.update_xaxes if which == "x" else fig.update_yaxes
    updater(**kwargs)

    if s["title"]:
        # Rename every axis that px gave a title (facets title the outer
        # axes only); fall back to the primary axis for bare figures.
        select = fig.select_xaxes if which == "x" else fig.select_yaxes
        titled = [axis for axis in select() if axis.title.text]
        if not titled:
            titled = [fig.layout.xaxis if which == "x" else fig.layout.yaxis]
        for axis in titled:
            axis.title.text = s["title"]


def _iter_group_traces(fig: go.Figure):
    """Yield (group name, trace) for traces that carry one discrete color.

    Skips traces colored by an array (continuous color mapping) and
    types with their own color semantics (pie, heatmap-family).
    """
    for trace in fig.data:
        if trace.type in _CONTINUOUS_TRACES or trace.type == "pie":
            continue
        marker_color = getattr(getattr(trace, "marker", None), "color", None)
        if marker_color is not None and not isinstance(marker_color, str):
            continue  # array -> continuous coloring, leave alone
        yield (trace.name or "", trace)


def _is_transparent(color: object) -> bool:
    """True for rgba colors with zero alpha (px uses them to hide parts)."""
    if not isinstance(color, str):
        return False
    c = color.replace(" ", "").lower()
    return c.startswith("rgba(") and c.endswith(",0)")


def _current_color(trace) -> str | None:
    """The discrete color px assigned to a trace (marker first, then line)."""
    for attr in ("marker", "line"):
        color = getattr(getattr(trace, attr, None), "color", None)
        if isinstance(color, str) and not _is_transparent(color):
            return color
    return None


def _recolor_trace(trace, color: str) -> None:
    """Set every discrete-color property a trace type may use."""
    if hasattr(trace, "marker") and trace.marker is not None:
        trace.marker.color = color
    if hasattr(trace, "line") and trace.line is not None:
        # Box/violin use 'line' for their outline; scatter for the line.
        # A transparent line is deliberate (px hides strip-plot boxes
        # this way) - leave it hidden.
        if not _is_transparent(trace.line.color):
            trace.line.color = color
    if trace.type in ("scatter", "scattergl") and trace.fill:
        trace.fillcolor = None  # let plotly derive it from the new color


def _apply_colors(fig: go.Figure, style: StyleModel) -> None:
    """Qualitative palette, per-group overrides, colorscale, opacity."""
    palette = palette_colors(style.palette)
    fig.update_layout(colorway=palette)

    # plotly.express bakes concrete colors into traces, so setting the
    # colorway is not enough: reassign trace colors from the palette.
    # Palette slots are keyed by the color px assigned (not the trace
    # name), so traces px deliberately colored alike - e.g. symbol-only
    # grouping - stay alike.
    seen: dict[str, int] = {}
    for name, trace in _iter_group_traces(fig):
        key = (_current_color(trace) or f"\x00name:{name}").lower()
        if key not in seen:
            seen[key] = len(seen)
        color = palette[seen[key] % len(palette)]
        if style.group_colors_on and name in style.group_colors:
            color = style.group_colors[name]
        _recolor_trace(trace, color)

    # Pie charts: one trace, one color per slice label.
    for trace in fig.data:
        if trace.type == "pie":
            labels = [
                str(v) for v in (trace.labels if trace.labels is not None else [])
            ]
            colors = [palette[i % len(palette)] for i in range(len(labels))]
            if style.group_colors_on:
                colors = [
                    style.group_colors.get(lbl, c)
                    for lbl, c in zip(labels, colors, strict=True)
                ]
            trace.marker.colors = colors

    # Continuous colorscale: shared coloraxis (px) and standalone traces.
    fig.update_layout(coloraxis_colorscale=style.colorscale)
    for trace in fig.data:
        if trace.type in _CONTINUOUS_TRACES and trace.coloraxis is None:
            trace.colorscale = style.colorscale

    if style.opacity < 1.0:
        fig.update_traces(opacity=style.opacity)


def _apply_legend(fig: go.Figure, style: StyleModel) -> None:
    """Legend visibility, title, placement, orientation, font size."""
    if not style.legend_show:
        fig.update_layout(showlegend=False)
        return
    position = _LEGEND_POSITIONS.get(
        style.legend_position, _LEGEND_POSITIONS["outside-right"]
    )
    legend = dict(
        orientation=style.legend_orientation,
        font_size=style.legend_font_size,
        **position,
    )
    fig.update_layout(showlegend=True, legend=legend)
    if style.legend_title:
        fig.update_layout(legend_title_text=style.legend_title)
