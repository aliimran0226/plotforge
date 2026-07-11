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
from plotforge.ui.controls_data import build_data_controls
from plotforge.ui.controls_mapping import build_chart_controls


def _placeholder(section: str) -> html.Div:
    """Temporary section body used until the real controls land."""
    return html.Div(
        html.Em(f"{section} controls coming soon."),
        className="text-muted p-2",
    )


def build_layout() -> dbc.Container:
    """Return the full page layout for the Dash app."""
    sidebar = dbc.Accordion(
        [
            dbc.AccordionItem(build_data_controls(), title="1. Data", item_id="data"),
            dbc.AccordionItem(
                build_chart_controls(), title="2. Chart", item_id="chart"
            ),
            dbc.AccordionItem(_placeholder("Style"), title="3. Style", item_id="style"),
            dbc.AccordionItem(
                _placeholder("Export"), title="4. Export", item_id="export"
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
                dbc.NavbarBrand("PlotForge", className="fw-bold"),
                html.Span(
                    f"v{__version__} - publication-ready figure playground",
                    className="navbar-text text-muted small",
                ),
            ],
            fluid=True,
        ),
        color="light",
        className="mb-3 border-bottom",
    )

    return dbc.Container(
        [
            header,
            dbc.Row(
                [
                    dbc.Col(sidebar, width=12, lg=4, xl=3, className="mb-3"),
                    dbc.Col(figure_area, width=12, lg=8, xl=9),
                ],
            ),
        ],
        fluid=True,
    )
