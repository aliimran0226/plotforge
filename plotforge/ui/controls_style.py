"""Style section of the sidebar: accordion of controls for StyleModel.

Every control's id is ``{"type": "style", "field": <StyleModel field>}``,
so the render callback can collect them all with one pattern-matching
Input and ``style_model.from_values`` can rebuild the dataclass. The
section table below (``_SECTIONS``) is the UI-side companion of
StyleModel - one entry per field, grouped for the accordion.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from plotforge import config
from plotforge.styling.style_model import defaults_by_field

#: Cap on generated per-group color pickers (a legend beyond this is
#: unreadable anyway).
MAX_GROUP_PICKERS = 24


def style_id(field: str) -> dict:
    """Pattern-matching id for the control bound to a StyleModel field."""
    return {"type": "style", "field": field}


def group_color_id(group: str) -> dict:
    """Pattern-matching id for one per-group color picker."""
    return {"type": "group-color", "group": group}


def decor_id(kind: str, idx: int, prop: str) -> dict:
    """Pattern-matching id for one property of one decoration entry.

    ``kind`` is 'line', 'band', or 'annot'; entries of a kind share an
    idx namespace managed by ``decor-store``.
    """
    return {"type": f"decor-{kind}", "idx": idx, "prop": prop}


def decor_del_id(kind: str, idx: int) -> dict:
    """Pattern-matching id for a decoration entry's remove button."""
    return {"type": f"decor-del-{kind}", "idx": idx}


# ---------------------------------------------------------------------------
# Control table: (field, label, widget, extra)
# widget: number | text | color | checkbox | dropdown | slider
# ---------------------------------------------------------------------------


def _axis_entries(p: str) -> list[tuple]:
    """Entries for one axis; ``p`` is the field prefix 'x' or 'y'."""
    return [
        (f"{p}_title", "Axis title (empty = column name)", "text", {}),
        (f"{p}_min", "Range min (empty = auto)", "number", {}),
        (f"{p}_max", "Range max (empty = auto)", "number", {}),
        (f"{p}_log", "Log scale", "checkbox", {}),
        (f"{p}_reversed", "Reversed", "checkbox", {}),
        (f"{p}_tick_size", "Tick label size", "number", {"min": 4, "max": 40}),
        (
            f"{p}_tick_angle",
            "Tick angle (empty = auto)",
            "number",
            {"min": -180, "max": 180},
        ),
        (
            f"{p}_tick_format",
            "Tick format (e.g. .2f or %b %Y)",
            "text",
            {},
        ),
        (
            f"{p}_ticks",
            "Tick marks",
            "dropdown",
            {
                "choices": [
                    ("Template default", ""),
                    ("Outside", "outside"),
                    ("Inside", "inside"),
                    ("Hidden", "none"),
                ]
            },
        ),
        (f"{p}_tick_len", "Tick length", "number", {"min": 0, "max": 30}),
        (f"{p}_tick_width", "Tick width", "number", {"min": 0.5, "max": 8}),
        (f"{p}_grid", "Gridlines", "checkbox", {}),
        (f"{p}_grid_color", "Gridline color", "color", {}),
        (f"{p}_zeroline", "Zero line", "checkbox", {}),
        (f"{p}_line", "Axis line", "checkbox", {}),
        (f"{p}_mirror", "Mirror axis line (box frame)", "checkbox", {}),
    ]


_SECTIONS: list[tuple[str, list[tuple]]] = [
    (
        "Figure",
        [
            ("width", "Width (px)", "number", {"min": 200, "max": 4000}),
            ("height", "Height (px)", "number", {"min": 200, "max": 4000}),
            ("template", "Template", "dropdown", {"choices": config.TEMPLATES}),
            ("paper_bgcolor", "Background (paper)", "color", {}),
            ("plot_bgcolor", "Background (plot area)", "color", {}),
            ("margin_l", "Margin left", "number", {"min": 0, "max": 400}),
            ("margin_r", "Margin right", "number", {"min": 0, "max": 400}),
            ("margin_t", "Margin top", "number", {"min": 0, "max": 400}),
            ("margin_b", "Margin bottom", "number", {"min": 0, "max": 400}),
            ("outer_border_on", "Border around figure", "checkbox", {}),
            ("outer_border_color", "Border color", "color", {}),
            ("outer_border_width", "Border width", "number", {"min": 0.5, "max": 12}),
            (
                "axis_line_width",
                "Axis line width",
                "number",
                {"min": 0.5, "max": 8},
            ),
        ],
    ),
    (
        "Titles & Fonts",
        [
            ("title_text", "Figure title", "text", {}),
            ("title_size", "Title size", "number", {"min": 6, "max": 72}),
            ("title_color", "Title color", "color", {}),
            (
                "title_align",
                "Title alignment",
                "dropdown",
                {
                    "choices": [
                        ("Left", "left"),
                        ("Center", "center"),
                        ("Right", "right"),
                    ]
                },
            ),
            (
                "font_family",
                "Font family (global)",
                "dropdown",
                {"choices": config.FONT_FAMILIES},
            ),
            ("axis_title_size", "Axis title size", "number", {"min": 4, "max": 40}),
        ],
    ),
    ("X Axis", _axis_entries("x")),
    ("Y Axis", _axis_entries("y")),
    (
        "Colors & Groups",
        [
            (
                "palette",
                "Qualitative palette",
                "dropdown",
                {"choices": list(config.QUALITATIVE_PALETTES)},
            ),
            (
                "colorscale",
                "Continuous colorscale",
                "dropdown",
                {"choices": config.CONTINUOUS_COLORSCALES},
            ),
            (
                "opacity",
                "Opacity",
                "slider",
                {"min": 0.1, "max": 1.0, "step": 0.05},
            ),
            ("group_colors_on", "Manual group colors", "checkbox", {}),
            # The per-group pickers are injected here by a callback once
            # the grouping column (and its categories) is known.
            ("__group_colors__", None, "placeholder", {}),
        ],
    ),
    (
        "Legend",
        [
            ("legend_show", "Show legend", "checkbox", {}),
            ("legend_title", "Legend title (empty = auto)", "text", {}),
            (
                "legend_position",
                "Position",
                "dropdown",
                {
                    "choices": [
                        ("Outside right", "outside-right"),
                        ("Below", "below"),
                        ("Inside top-left", "inside-top-left"),
                        ("Inside top-right", "inside-top-right"),
                        ("Inside bottom-left", "inside-bottom-left"),
                        ("Inside bottom-right", "inside-bottom-right"),
                    ]
                },
            ),
            (
                "legend_orientation",
                "Orientation",
                "dropdown",
                {"choices": [("Vertical", "v"), ("Horizontal", "h")]},
            ),
            ("legend_font_size", "Font size", "number", {"min": 4, "max": 40}),
        ],
    ),
]


def _widget(field: str, widget: str, default: object, extra: dict):
    """Build one style input component."""
    wid = style_id(field)
    if widget == "dropdown":
        options = [
            (
                {"label": c[0], "value": c[1]}
                if isinstance(c, (tuple, list))
                else {"label": str(c), "value": c}
            )
            for c in extra.get("choices", [])
        ]
        return dcc.Dropdown(id=wid, options=options, value=default, clearable=False)
    if widget == "checkbox":
        return dbc.Checkbox(id=wid, value=bool(default))
    if widget == "slider":
        return dcc.Slider(
            id=wid,
            min=extra.get("min"),
            max=extra.get("max"),
            step=extra.get("step"),
            value=default,
            marks=None,
            tooltip={"placement": "bottom", "always_visible": False},
        )
    if widget == "color":
        return dbc.Input(id=wid, type="color", value=default, size="sm")
    if widget == "text":
        return dbc.Input(
            id=wid, type="text", value=default or "", size="sm", debounce=True
        )
    # number
    return dbc.Input(
        id=wid,
        type="number",
        value=default,
        min=extra.get("min"),
        max=extra.get("max"),
        size="sm",
        debounce=True,
    )


def _decorations_section() -> list:
    """Content of the 'Reference lines & annotations' accordion item."""

    def add_button(label: str, bid: str) -> dbc.Button:
        return dbc.Button(label, id=bid, color="secondary", outline=True, size="sm")

    return [
        html.Div(
            [
                add_button("+ H line", "add-decor-hline"),
                add_button("+ V line", "add-decor-vline"),
                add_button("+ Band", "add-decor-band"),
                add_button("+ Text", "add-decor-annot"),
            ],
            className="d-flex gap-1 flex-wrap mb-2",
        ),
        html.Div(
            html.Small(
                "Add threshold lines, shaded bands, or text labels.",
                className="text-muted",
            ),
            id="decor-controls",
        ),
        dcc.Store(
            id="decor-store", data={"line": [], "band": [], "annot": [], "next": 0}
        ),
    ]


def build_style_controls() -> html.Div:
    """Static content of the Style accordion section."""
    defaults = defaults_by_field()
    items = []
    for section_label, entries in _SECTIONS:
        rows = []
        for field, label, widget, extra in entries:
            if widget == "placeholder":
                rows.append(html.Div(id="group-color-controls"))
                continue
            rows.append(
                html.Div(
                    [
                        dbc.Label(label, className="small mb-0"),
                        _widget(field, widget, defaults.get(field), extra),
                    ],
                    className="mb-2",
                )
            )
        items.append(dbc.AccordionItem(rows, title=section_label))
    items.append(
        dbc.AccordionItem(_decorations_section(), title="Reference lines & annotations")
    )

    return html.Div(
        [
            dbc.Button(
                "Reset style to defaults",
                id="reset-style",
                color="secondary",
                outline=True,
                size="sm",
                className="w-100 mb-2",
            ),
            dbc.Accordion(items, start_collapsed=True, flush=True, always_open=True),
        ]
    )


def _to_hex(color: str) -> str:
    """Normalize 'rgb(r,g,b)' palette entries to hex for <input type=color>."""
    color = color.strip()
    if color.startswith("#"):
        return color
    if color.startswith("rgb"):
        try:
            r, g, b = [
                int(float(v)) for v in color[color.find("(") + 1 : -1].split(",")[:3]
            ]
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            pass
    return "#636efa"  # plotly blue as a safe fallback


def make_group_color_pickers(
    groups: list[str], palette: list[str], current: dict[str, str] | None = None
) -> list:
    """One color picker per detected group, seeded from the palette.

    ``current`` preserves the user's picks for groups that still exist
    when the pickers are regenerated (e.g. after a chart-type switch).
    """
    current = current or {}
    if not groups:
        return [
            html.Small(
                "Map a column to Color to pick per-group colors.",
                className="text-muted",
            )
        ]
    shown = groups[:MAX_GROUP_PICKERS]
    rows = []
    for i, group in enumerate(shown):
        seed = current.get(group) or _to_hex(palette[i % len(palette)])
        rows.append(
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Label(str(group), className="small mb-0 text-truncate"),
                        width=7,
                    ),
                    dbc.Col(
                        dbc.Input(
                            id=group_color_id(str(group)),
                            type="color",
                            value=seed,
                            size="sm",
                        ),
                        width=5,
                    ),
                ],
                className="align-items-center mb-1",
            )
        )
    if len(groups) > MAX_GROUP_PICKERS:
        rows.append(
            html.Small(
                f"Showing first {MAX_GROUP_PICKERS} of {len(groups)} groups.",
                className="text-muted",
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Decoration entry cards (reference lines / bands / annotations)
# ---------------------------------------------------------------------------

#: Dash choices for reference-line orientation and dash style.
_ORIENT_CHOICES = [
    {"label": "Horizontal", "value": "h"},
    {"label": "Vertical", "value": "v"},
]
_DASH_CHOICES = [
    {"label": s.capitalize(), "value": s} for s in ("solid", "dash", "dot", "dashdot")
]


def _decor_card(kind: str, idx: int, title: str, body: list) -> dbc.Card:
    """Frame of one decoration entry: header, remove button, inputs."""
    header = html.Div(
        [
            html.Small(title, className="fw-bold"),
            dbc.Button(
                "Remove",
                id=decor_del_id(kind, idx),
                color="link",
                size="sm",
                className="p-0 text-danger small",
            ),
        ],
        className="d-flex justify-content-between align-items-center mb-1",
    )
    return dbc.Card(dbc.CardBody([header, *body], className="p-2"), className="mb-2")


def _decor_input(kind: str, idx: int, prop: str, label: str, widget, **kwargs):
    """One labeled input inside a decoration card."""
    return html.Div(
        [
            dbc.Label(label, className="small mb-0"),
            widget(id=decor_id(kind, idx, prop), **kwargs),
        ],
        className="mb-1",
    )


def make_line_entry(idx: int, current: dict) -> dbc.Card:
    """Card for one reference line."""
    orient = current.get("orient") or "h"
    body = [
        _decor_input(
            "line",
            idx,
            "orient",
            "Orientation",
            dcc.Dropdown,
            options=_ORIENT_CHOICES,
            value=orient,
            clearable=False,
        ),
        _decor_input(
            "line",
            idx,
            "value",
            "Position (number or date)",
            dbc.Input,
            type="text",
            value=current.get("value") or "",
            size="sm",
            debounce=True,
        ),
        _decor_input(
            "line",
            idx,
            "dash",
            "Line style",
            dcc.Dropdown,
            options=_DASH_CHOICES,
            value=current.get("dash") or "dash",
            clearable=False,
        ),
        _decor_input(
            "line",
            idx,
            "width",
            "Width",
            dbc.Input,
            type="number",
            value=current.get("width", 1.5),
            min=0.5,
            max=10,
            size="sm",
            debounce=True,
        ),
        _decor_input(
            "line",
            idx,
            "color",
            "Color",
            dbc.Input,
            type="color",
            value=current.get("color") or "#444444",
            size="sm",
        ),
        _decor_input(
            "line",
            idx,
            "label",
            "Label (optional)",
            dbc.Input,
            type="text",
            value=current.get("label") or "",
            size="sm",
            debounce=True,
        ),
    ]
    title = "Horizontal line" if orient == "h" else "Vertical line"
    return _decor_card("line", idx, title, body)


def make_band_entry(idx: int, current: dict) -> dbc.Card:
    """Card for one shaded band."""
    body = [
        _decor_input(
            "band",
            idx,
            "orient",
            "Orientation",
            dcc.Dropdown,
            options=_ORIENT_CHOICES,
            value=current.get("orient") or "v",
            clearable=False,
        ),
        _decor_input(
            "band",
            idx,
            "start",
            "From (number or date)",
            dbc.Input,
            type="text",
            value=current.get("start") or "",
            size="sm",
            debounce=True,
        ),
        _decor_input(
            "band",
            idx,
            "end",
            "To",
            dbc.Input,
            type="text",
            value=current.get("end") or "",
            size="sm",
            debounce=True,
        ),
        _decor_input(
            "band",
            idx,
            "color",
            "Fill color",
            dbc.Input,
            type="color",
            value=current.get("color") or "#fdae61",
            size="sm",
        ),
        _decor_input(
            "band",
            idx,
            "opacity",
            "Opacity",
            dbc.Input,
            type="number",
            value=current.get("opacity", 0.2),
            min=0.05,
            max=1,
            step=0.05,
            size="sm",
            debounce=True,
        ),
    ]
    return _decor_card("band", idx, "Shaded band", body)


def make_annot_entry(idx: int, current: dict) -> dbc.Card:
    """Card for one text annotation."""
    body = [
        _decor_input(
            "annot",
            idx,
            "text",
            "Text",
            dbc.Input,
            type="text",
            value=current.get("text") or "",
            size="sm",
            debounce=True,
        ),
        _decor_input(
            "annot",
            idx,
            "x",
            "X (number or date)",
            dbc.Input,
            type="text",
            value=current.get("x") or "",
            size="sm",
            debounce=True,
        ),
        _decor_input(
            "annot",
            idx,
            "y",
            "Y",
            dbc.Input,
            type="text",
            value=current.get("y") or "",
            size="sm",
            debounce=True,
        ),
        _decor_input(
            "annot",
            idx,
            "size",
            "Font size",
            dbc.Input,
            type="number",
            value=current.get("size", 12),
            min=6,
            max=48,
            size="sm",
            debounce=True,
        ),
        _decor_input(
            "annot",
            idx,
            "color",
            "Color",
            dbc.Input,
            type="color",
            value=current.get("color") or "#000000",
            size="sm",
        ),
        html.Div(
            [
                dbc.Checkbox(
                    id=decor_id("annot", idx, "arrow"),
                    value=bool(current.get("arrow", True)),
                ),
                dbc.Label("Arrow to point", className="small mb-0 ms-1"),
            ],
            className="d-flex align-items-center mb-1",
        ),
    ]
    return _decor_card("annot", idx, "Text annotation", body)


_ENTRY_BUILDERS = {
    "line": make_line_entry,
    "band": make_band_entry,
    "annot": make_annot_entry,
}


def make_decoration_controls(store: dict, current: dict[str, dict[int, dict]]) -> list:
    """All decoration cards, rebuilt from the store's entry ids.

    ``current`` maps kind -> idx -> {prop: value} and preserves what the
    user already typed when the card list is regenerated.
    """
    cards = []
    for kind, builder in _ENTRY_BUILDERS.items():
        for idx in store.get(kind, []):
            cards.append(builder(idx, current.get(kind, {}).get(idx, {})))
    if not cards:
        return [
            html.Small(
                "Add threshold lines, shaded bands, or text labels.",
                className="text-muted",
            )
        ]
    return cards
