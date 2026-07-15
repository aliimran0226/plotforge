"""StyleModel: every style option of a PlotForge figure, in one dataclass.

Single source of truth for styling:

- the Style accordion controls carry pattern ids ``{"type": "style",
  "field": <field name>}``, so each control maps 1:1 to a field here;
- ``from_values()`` rebuilds a StyleModel from those control values;
- ``styling.apply.apply_style()`` reads the fields and styles the figure.

Adding a style option = add a field here (default in ``config.py`` if
user-facing), add a control entry in ``ui/controls_style.py``, and
handle the field in ``apply_style``.
"""

from __future__ import annotations

import types
import typing
from dataclasses import dataclass, field, fields

from plotforge import config


@dataclass
class StyleModel:
    """All style options. Empty strings / None mean 'automatic'."""

    # --- Figure -----------------------------------------------------------
    width: int | None = None  # None = fit the window width
    height: int = config.FIGURE_HEIGHT
    template: str = config.TEMPLATE
    paper_bgcolor: str = config.PAPER_BGCOLOR
    plot_bgcolor: str = config.PLOT_BGCOLOR
    margin_l: int = config.MARGIN["l"]
    margin_r: int = config.MARGIN["r"]
    margin_t: int = config.MARGIN["t"]
    margin_b: int = config.MARGIN["b"]
    outer_border_on: bool = False  # border around the whole figure canvas
    outer_border_color: str = "#000000"
    outer_border_width: float = 1.5
    axis_line_width: float = 1.0  # width of axis lines (both axes)

    # --- Titles & fonts ----------------------------------------------------
    title_text: str = ""  # "" = no title
    title_size: int = config.TITLE_FONT_SIZE
    title_color: str = "#000000"
    title_align: str = "center"  # left | center | right
    font_family: str = config.FONT_FAMILY
    axis_title_size: int = config.AXIS_TITLE_FONT_SIZE

    # --- X axis -------------------------------------------------------------
    x_title: str = ""  # "" = keep the automatic (column) title
    x_min: float | None = None  # both min & max set -> fixed range
    x_max: float | None = None
    x_log: bool = False
    x_tick_size: int = config.TICK_FONT_SIZE
    x_tick_angle: float | None = None  # None = automatic
    x_tick_format: str = ""  # d3-format / strftime string
    x_ticks: str = ""  # tick marks: "" = template default | outside | inside | none
    x_tick_len: int = 5
    x_tick_width: float = 1.0
    x_grid: bool = True
    x_grid_color: str = "#e5e5e5"
    x_zeroline: bool = False
    x_line: bool = True  # show the axis line itself
    x_mirror: bool = False  # mirror the axis line (box frame)
    x_reversed: bool = False

    # --- Y axis -------------------------------------------------------------
    y_title: str = ""
    y_min: float | None = None
    y_max: float | None = None
    y_log: bool = False
    y_tick_size: int = config.TICK_FONT_SIZE
    y_tick_angle: float | None = None
    y_tick_format: str = ""
    y_ticks: str = ""
    y_tick_len: int = 5
    y_tick_width: float = 1.0
    y_grid: bool = True
    y_grid_color: str = "#e5e5e5"
    y_zeroline: bool = False
    y_line: bool = True
    y_mirror: bool = False
    y_reversed: bool = False

    # --- Colors & groups ------------------------------------------------------
    palette: str = config.DEFAULT_QUALITATIVE_PALETTE
    colorscale: str = config.DEFAULT_CONTINUOUS_COLORSCALE
    opacity: float = 1.0
    group_colors_on: bool = False  # apply the manual per-group pickers?
    #: group/category name -> hex color; filled from the pattern-matched
    #: color pickers, not from a single control.
    group_colors: dict[str, str] = field(default_factory=dict)

    # --- Reference lines / bands / annotations ------------------------------
    #: Entry dicts filled from the dynamic decoration controls (see
    #: ``ui/controls_style.py``), not from single pattern-id controls:
    #: line:  {orient, value, color, dash, width, label}
    #: band:  {orient, start, end, color, opacity}
    #: annot: {text, x, y, arrow, size, color}
    ref_lines: list[dict] = field(default_factory=list)
    ref_bands: list[dict] = field(default_factory=list)
    annotations: list[dict] = field(default_factory=list)

    # --- Legend ------------------------------------------------------------
    legend_show: bool = True
    legend_title: str = ""  # "" = automatic (column name)
    legend_position: str = "outside-right"
    legend_orientation: str = "v"  # v | h
    legend_font_size: int = config.LEGEND_FONT_SIZE


def _convert(value: object, annotation: object) -> object:
    """Coerce a raw control value to a field's annotated type.

    Dash controls deliver strings/None for numbers and None for empty
    text inputs; normalize so StyleModel always holds clean values.
    """
    # Unwrap "X | None": empty input means None, else convert as X.
    if isinstance(annotation, types.UnionType):
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if value is None or value == "":
            return None
        annotation = args[0]
    if annotation is bool:
        return bool(value)
    if annotation is int:
        return int(float(value))
    if annotation is float:
        return float(value)
    if annotation is str:
        return "" if value is None else str(value)
    return value


#: Fields populated from dynamic control groups (not one control each);
#: from_values ignores them in ``values`` and fills them from arguments.
_COLLECTION_FIELDS = {"group_colors", "ref_lines", "ref_bands", "annotations"}


def from_values(
    values: dict[str, object],
    group_colors: dict[str, str] | None = None,
    decorations: dict[str, list[dict]] | None = None,
) -> StyleModel:
    """Build a StyleModel from ``field name -> control value``.

    Unknown keys are ignored; missing fields keep their defaults; values
    that fail conversion (e.g. half-typed numbers) also keep defaults so
    a live keystroke never crashes the render callback. ``decorations``
    maps collection field names (``ref_lines``/``ref_bands``/
    ``annotations``) to their entry lists.
    """
    style = StyleModel()
    hints = typing.get_type_hints(StyleModel)
    valid = {f.name for f in fields(StyleModel)}
    for name, raw in values.items():
        if name not in valid or name in _COLLECTION_FIELDS:
            continue
        try:
            setattr(style, name, _convert(raw, hints[name]))
        except (TypeError, ValueError):
            continue  # keep the default rather than erroring mid-typing
    if group_colors:
        style.group_colors = dict(group_colors)
    for name, entries in (decorations or {}).items():
        if name in _COLLECTION_FIELDS and entries:
            setattr(style, name, list(entries))
    return style


def defaults_by_field() -> dict[str, object]:
    """Field name -> default value (used by the reset-style button)."""
    model = StyleModel()
    return {f.name: getattr(model, f.name) for f in fields(StyleModel)}


def entries_by_index(pattern_items: list[dict]) -> dict[int, dict]:
    """Group ctx pattern entries ``{'id': {'idx': i, 'prop': p}, 'value': v}``
    into ``idx -> {prop: value}`` dicts (one per decoration entry)."""
    grouped: dict[int, dict] = {}
    for item in pattern_items:
        ident = item.get("id") or {}
        grouped.setdefault(ident.get("idx"), {})[ident.get("prop")] = item.get("value")
    return grouped
