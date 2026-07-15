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
    _apply_decorations(fig, style)
    _apply_outer_border(fig, style)
    return fig


def _coord(value: object) -> object | None:
    """Coerce a decoration coordinate: number if possible, else the raw
    string (datetime/categorical axes take strings), None if empty."""
    if value is None or value == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return value


def _num(value: object, default: float) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _apply_decorations(fig: go.Figure, style: StyleModel) -> None:
    """Reference lines, shaded bands, and text annotations.

    Safe to run every render: apply_style always receives a freshly
    built figure, so decorations never accumulate.
    """
    for entry in style.ref_lines:
        value = _coord(entry.get("value"))
        if value is None:
            continue
        adder = fig.add_hline if entry.get("orient") == "h" else fig.add_vline
        kwargs = dict(
            line_color=entry.get("color") or "#444444",
            line_dash=entry.get("dash") or "dash",
            line_width=_num(entry.get("width"), 1.5),
        )
        if entry.get("label"):
            kwargs["annotation_text"] = entry["label"]
        adder(value, **kwargs)

    for entry in style.ref_bands:
        start, end = _coord(entry.get("start")), _coord(entry.get("end"))
        if start is None or end is None:
            continue
        adder = fig.add_hrect if entry.get("orient") == "h" else fig.add_vrect
        adder(
            start,
            end,
            fillcolor=entry.get("color") or "#fdae61",
            opacity=_num(entry.get("opacity"), 0.2),
            line_width=0,
            layer="below",
        )

    for entry in style.annotations:
        x, y = _coord(entry.get("x")), _coord(entry.get("y"))
        if not entry.get("text") or x is None or y is None:
            continue
        fig.add_annotation(
            x=x,
            y=y,
            text=entry["text"],
            showarrow=bool(entry.get("arrow")),
            font=dict(
                size=int(_num(entry.get("size"), 12)),
                color=entry.get("color") or "#000000",
            ),
        )


def _apply_outer_border(fig: go.Figure, style: StyleModel) -> None:
    """Rectangle around the whole figure canvas (margins included).

    Paper coordinates (0..1) span only the plot region, so the canvas
    edges are reached by extending past them by margin/plot-size - which
    needs a concrete figure size. Auto-sized figures fall back to
    framing the plot region. The half-line-width inset keeps the border
    fully inside the canvas instead of clipped on the edge.
    """
    if not style.outer_border_on:
        return
    half = style.outer_border_width / 2
    if style.width and style.height:
        pw = max(style.width - style.margin_l - style.margin_r, 1)
        ph = max(style.height - style.margin_t - style.margin_b, 1)
        x0 = (-style.margin_l + half) / pw
        x1 = 1 + (style.margin_r - half) / pw
        y0 = (-style.margin_b + half) / ph
        y1 = 1 + (style.margin_t - half) / ph
    else:
        x0 = y0 = 0.0
        x1 = y1 = 1.0
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
        line=dict(color=style.outer_border_color, width=style.outer_border_width),
        fillcolor="rgba(0,0,0,0)",
        layer="above",
    )


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


def _axis_bounds(
    lo: float | None, hi: float | None, log: bool, reverse: bool
) -> tuple[list[float | None] | None, object]:
    """(range, autorange) for the axis, honoring partially fixed bounds.

    Plotly expects log-axis ranges as log10 exponents (non-positive
    bounds have no log and are dropped). A single fixed bound uses
    plotly's autorange 'min'/'max' modes, which compute only the
    missing end. Returns autorange=None when the axis default should
    be left alone (px.imshow, for one, relies on its own 'reversed').
    """
    if log:
        lo = math.log10(lo) if lo is not None and lo > 0 else None
        hi = math.log10(hi) if hi is not None and hi > 0 else None
    if lo is None and hi is None:
        return None, ("reversed" if reverse else None)
    if lo is not None and hi is not None:
        return ([hi, lo] if reverse else [lo, hi]), False
    if reverse:  # reversed axes store their range as [high, low]
        rng = [None, lo] if hi is None else [hi, None]
        auto = "max reversed" if hi is None else "min reversed"
    else:
        rng = [lo, None] if hi is None else [None, hi]
        auto = "max" if hi is None else "min"
    return rng, auto


def _apply_axis(fig: go.Figure, style: StyleModel, which: str) -> None:
    """Apply the x_* or y_* fields to every matching axis (incl. facets)."""
    s = {k[2:]: v for k, v in vars(style).items() if k.startswith(which + "_")}

    kwargs: dict = dict(
        type="log" if s["log"] else "linear",
        tickfont_size=s["tick_size"],
        showgrid=s["grid"],
        zeroline=s["zeroline"],
        showline=s["line"],
        linewidth=style.axis_line_width,
        mirror=s["mirror"],
        ticklen=s["tick_len"],
        tickwidth=s["tick_width"],
        title_font_size=style.axis_title_size,
    )
    if s["ticks"]:  # "" = leave the template's tick style alone
        kwargs["ticks"] = "" if s["ticks"] == "none" else s["ticks"]
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

    rng, autorange = _axis_bounds(s["min"], s["max"], s["log"], s["reversed"])
    if rng is not None:
        kwargs["range"] = rng
    if autorange is not None:
        kwargs["autorange"] = autorange

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
