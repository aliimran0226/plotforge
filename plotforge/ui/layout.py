"""Page skeleton: left sidebar (controls) + main figure area.

The sidebar is an accordion with the workflow sections Data, Chart,
Style, and Export. Each section's content is built by its own module
(``controls_data``, ``controls_mapping``, ``controls_style``,
``controls_export``) so this file only assembles the skeleton.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from plotforge import __version__
from plotforge.ui.controls_compose import build_compose_controls
from plotforge.ui.controls_data import build_data_controls
from plotforge.ui.controls_export import build_export_controls
from plotforge.ui.controls_mapping import build_chart_controls
from plotforge.ui.controls_style import build_style_controls


def _section_title(icon: str, text: str) -> html.Span:
    """Accordion section title with a Bootstrap icon."""
    return html.Span(
        [html.I(className=f"bi bi-{icon} me-2 text-primary"), text],
        className="fw-semibold",
    )


def build_layout() -> dbc.Container:
    """Return the full page layout for the Dash app."""
    sidebar = dbc.Accordion(
        [
            dbc.AccordionItem(
                build_data_controls(),
                title=_section_title("table", "1. Data"),
                item_id="data",
            ),
            dbc.AccordionItem(
                build_chart_controls(),
                title=_section_title("bar-chart-line", "2. Chart"),
                item_id="chart",
            ),
            dbc.AccordionItem(
                build_style_controls(),
                title=_section_title("palette", "3. Style"),
                item_id="style",
            ),
            dbc.AccordionItem(
                build_export_controls(),
                title=_section_title("download", "4. Export"),
                item_id="export",
            ),
            dbc.AccordionItem(
                build_compose_controls(),
                title=_section_title("grid-3x3-gap", "5. Compose"),
                item_id="compose",
            ),
        ],
        active_item="data",
        always_open=True,
        id="sidebar-accordion",
    )

    figure_area = dbc.Card(
        dbc.CardBody(
            [
                dbc.Alert(
                    id="plot-error",
                    color="danger",
                    dismissable=True,
                    is_open=False,
                    className="py-2 small",
                ),
                dcc.Loading(
                    html.Div(
                        html.P(
                            "Upload a data file to get started.",
                            className="text-muted text-center mt-5",
                        ),
                        id="figure-container",
                    ),
                    type="default",
                ),
            ]
        ),
        className="h-100",
    )

    header = dbc.Navbar(
        dbc.Container(
            [
                html.Div(
                    [
                        html.I(className="bi bi-graph-up-arrow me-2 fs-4 text-primary"),
                        dbc.NavbarBrand("PlotForge", className="fw-bold mb-0"),
                        html.Span(
                            f"v{__version__} · publication-ready figures",
                            className="navbar-text text-muted small ms-2 "
                            "d-none d-md-inline",
                        ),
                    ],
                    className="d-flex align-items-center",
                ),
                html.Div(
                    [
                        html.I(className="bi bi-sun me-1 text-muted small"),
                        dbc.Switch(id="theme-switch", value=False, className="mb-0"),
                        html.I(className="bi bi-moon-stars text-muted small"),
                        html.Span(id="theme-dummy", className="d-none"),
                    ],
                    className="d-flex align-items-center",
                    title="Dark mode (app only - figures keep their template)",
                ),
            ],
            fluid=True,
        ),
        className="mb-3 border-bottom bg-body-tertiary pf-header",
    )

    return dbc.Container(
        [
            header,
            dbc.Row(
                [
                    dbc.Col(sidebar, width=12, lg=4, xl=3, className="mb-3 pf-sidebar"),
                    dbc.Col(figure_area, width=12, lg=8, xl=9, className="pf-figure"),
                ],
            ),
        ],
        fluid=True,
    )
