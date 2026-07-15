"""Chart section of the sidebar: chart-type picker + dynamic mapping UI.

Everything here is generated from the plot registry: the chart-type
dropdown lists registered plots, and the mapping/option widgets are
built from the selected plot's ``MappingSpec`` / ``OptionSpec``
declarations. Pattern-matching component ids let one callback read all
of them regardless of chart type.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from plotforge.plots.base import BasePlot, OptionSpec
from plotforge.plots.registry import all_plots

#: Badge shown next to a column name in mapping dropdowns.
_KIND_BADGE = {"numeric": "#", "categorical": "abc", "datetime": "date"}


def mapping_id(name: str) -> dict:
    """Pattern-matching id for a mapping dropdown."""
    return {"type": "mapping", "name": name}


def option_id(name: str) -> dict:
    """Pattern-matching id for a chart-specific option widget."""
    return {"type": "plot-opt", "name": name}


def build_chart_controls() -> html.Div:
    """Static content of the Chart accordion section."""
    # Local import: controls_layers needs _column_options from here.
    from plotforge.ui.controls_layers import build_layer_section

    plots = all_plots()
    return html.Div(
        [
            dbc.Label("Chart type", className="small mb-1 fw-bold"),
            dcc.Dropdown(
                id="chart-type",
                options=[
                    {"label": cls.label, "value": name} for name, cls in plots.items()
                ],
                value=next(iter(plots), None),
                clearable=False,
                className="mb-3",
            ),
            html.Div(id="mapping-controls"),
            html.Div(id="plot-options-controls"),
            build_layer_section(),
        ]
    )


def _column_options(
    columns: list[str], column_types: dict[str, str], kinds: tuple[str, ...]
) -> list[dict]:
    """Dropdown options for one slot: matching columns first, annotated.

    Non-matching columns are still offered (disabled) so the user sees
    why a column can't go in a numeric-only slot.
    """
    options = []
    for col in columns:
        kind = column_types.get(col, "categorical")
        badge = _KIND_BADGE.get(kind, "?")
        options.append(
            {
                "label": f"{col}  ({badge})",
                "value": col,
                "disabled": kind not in kinds,
            }
        )
    # Selectable columns first, keeping original order within each half.
    return sorted(options, key=lambda o: o["disabled"])


def build_mapping_controls(
    plot_cls: type[BasePlot],
    columns: list[str],
    column_types: dict[str, str],
    previous: dict[str, str] | None = None,
) -> list:
    """Mapping dropdowns for ``plot_cls``, pre-filled where possible.

    Selections from the previously shown chart type carry over when the
    slot name matches (``previous``); otherwise required slots default
    to the first columns of an accepted kind so a fresh upload renders
    a figure immediately.
    """
    previous = previous or {}
    children: list = [dbc.Label("Columns", className="small mb-1 fw-bold")]
    used: set[str] = set()

    for spec in plot_cls.all_mappings():
        required = spec in plot_cls.required_mappings
        value = previous.get(spec.name)
        if value and (
            value not in column_types or column_types[value] not in spec.kinds
        ):
            value = None  # stale or incompatible carry-over
        if not value and required:
            # Default: first not-yet-used column of an accepted kind.
            value = next(
                (
                    c
                    for c in columns
                    if column_types.get(c) in spec.kinds and c not in used
                ),
                None,
            )
        if value:
            used.add(value)

        label = spec.label + ("" if required else " (optional)")
        children.append(
            html.Div(
                [
                    dbc.Label(label, className="small mb-0"),
                    dcc.Dropdown(
                        id=mapping_id(spec.name),
                        options=_column_options(columns, column_types, spec.kinds),
                        value=value,
                        clearable=not required,
                        placeholder="Select column...",
                    ),
                    (
                        html.Small(spec.help, className="text-muted")
                        if spec.help
                        else None
                    ),
                ],
                className="mb-2",
            )
        )
    return children


def _option_widget(opt: OptionSpec, value: object):
    """Build the input component for one OptionSpec."""
    if opt.widget == "dropdown":
        options = [
            (
                {"label": c[0], "value": c[1]}
                if isinstance(c, (tuple, list))
                else {"label": str(c), "value": c}
            )
            for c in opt.choices
        ]
        return dcc.Dropdown(
            id=option_id(opt.name), options=options, value=value, clearable=False
        )
    if opt.widget == "checkbox":
        return dbc.Checkbox(id=option_id(opt.name), value=bool(value))
    if opt.widget == "slider":
        return dcc.Slider(
            id=option_id(opt.name),
            min=opt.min,
            max=opt.max,
            step=opt.step,
            value=value,
            marks=None,
            tooltip={"placement": "bottom", "always_visible": False},
        )
    # Fallback: plain number input.
    return dbc.Input(
        id=option_id(opt.name),
        type="number",
        value=value,
        min=opt.min,
        max=opt.max,
        step=opt.step,
        size="sm",
    )


def build_option_controls(
    plot_cls: type[BasePlot], previous: dict[str, object] | None = None
) -> list:
    """Chart-specific option widgets for ``plot_cls``."""
    if not plot_cls.extra_options:
        return []
    previous = previous or {}
    children: list = [
        html.Hr(className="my-2"),
        dbc.Label(f"{plot_cls.label} options", className="small mb-1 fw-bold"),
    ]
    for opt in plot_cls.extra_options:
        value = previous.get(opt.name, opt.default)
        children.append(
            html.Div(
                [
                    dbc.Label(opt.label, className="small mb-0"),
                    _option_widget(opt, value),
                ],
                className="mb-2",
            )
        )
    return children
