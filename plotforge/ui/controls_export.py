"""Export section of the sidebar: size, scale, format, filename, button.

The actual export happens server-side (kaleido) in
``callbacks/export_callbacks.py`` and is delivered via ``dcc.Download``.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from plotforge import config


def build_export_controls() -> html.Div:
    """Return the static content of the Export accordion section."""
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Width (px)", className="small mb-0"),
                            dbc.Input(
                                id="export-width",
                                type="number",
                                value=config.EXPORT_WIDTH,
                                min=100,
                                max=8000,
                                size="sm",
                            ),
                        ]
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Height (px)", className="small mb-0"),
                            dbc.Input(
                                id="export-height",
                                type="number",
                                value=config.EXPORT_HEIGHT,
                                min=100,
                                max=8000,
                                size="sm",
                            ),
                        ]
                    ),
                ],
                className="mb-2",
            ),
            dbc.Label("Scale factor", className="small mb-0"),
            dcc.Slider(
                id="export-scale",
                min=1,
                max=5,
                step=1,
                value=config.EXPORT_SCALE,
                marks={i: str(i) for i in range(1, 6)},
            ),
            html.Small(
                "Pixel multiplier for high-DPI output: scale 3 of a "
                "1200x800 px figure gives 3600x2400 px (~300 DPI when "
                "printed 12 inches wide).",
                className="text-muted d-block mb-2",
            ),
            dbc.Label("Format", className="small mb-0"),
            dcc.Dropdown(
                id="export-format",
                options=[
                    {"label": "PNG", "value": "png"},
                    {"label": "JPG", "value": "jpg"},
                ],
                value=config.EXPORT_FORMAT,
                clearable=False,
                className="mb-2",
            ),
            dbc.Label("Filename", className="small mb-0"),
            dbc.Input(
                id="export-filename",
                type="text",
                value=config.EXPORT_FILENAME,
                size="sm",
                className="mb-3",
            ),
            dbc.Button(
                "Export figure",
                id="export-button",
                color="primary",
                className="w-100",
            ),
            dbc.Alert(
                id="export-error",
                color="danger",
                dismissable=True,
                is_open=False,
                className="py-2 small mt-2",
            ),
            dcc.Download(id="export-download"),
        ]
    )
