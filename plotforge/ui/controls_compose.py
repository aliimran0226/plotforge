"""Compose section of the sidebar: saved panels -> grid image.

Panels live server-side in ``plotforge.compose``; this module only
renders the panel list and the grid settings. Composition previews and
exports are raster-only (stitched pixels), so there is no SVG/PDF here.
"""

from __future__ import annotations

import base64

import dash_bootstrap_components as dbc
from dash import dcc, html

from plotforge import compose


def panel_action_id(action: str, pid: str) -> dict:
    """Pattern id for a panel-list button; action = 'remove' | 'up'."""
    return {"type": f"panel-{action}", "pid": pid}


def build_compose_controls() -> html.Div:
    """Static content of the Compose accordion section."""
    return html.Div(
        [
            html.Small(
                "Combine saved figures into one publication-style grid "
                "with (a), (b), ... panel labels.",
                className="text-muted d-block mb-2",
            ),
            dbc.Button(
                "Save current figure as panel",
                id="save-panel",
                color="secondary",
                outline=True,
                size="sm",
                className="w-100 mb-2",
            ),
            html.Div(id="panel-list", children=make_panel_list()),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Grid columns", className="small mb-0"),
                            dbc.Input(
                                id="compose-columns",
                                type="number",
                                value=2,
                                min=1,
                                max=6,
                                size="sm",
                            ),
                        ]
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Scale", className="small mb-0"),
                            dbc.Input(
                                id="compose-scale",
                                type="number",
                                value=2,
                                min=1,
                                max=5,
                                size="sm",
                            ),
                        ]
                    ),
                ],
                className="mb-2",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Cell width", className="small mb-0"),
                            dbc.Input(
                                id="compose-cell-width",
                                type="number",
                                value=compose.CELL_WIDTH,
                                min=200,
                                max=2000,
                                size="sm",
                            ),
                        ]
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Cell height", className="small mb-0"),
                            dbc.Input(
                                id="compose-cell-height",
                                type="number",
                                value=compose.CELL_HEIGHT,
                                min=200,
                                max=2000,
                                size="sm",
                            ),
                        ]
                    ),
                ],
                className="mb-2",
            ),
            html.Div(
                [
                    dbc.Checkbox(id="compose-labels", value=True),
                    dbc.Label(
                        "Panel labels (a), (b), ...", className="small mb-0 ms-1"
                    ),
                ],
                className="d-flex align-items-center mb-2",
            ),
            dbc.Label("Format (raster only)", className="small mb-0"),
            dcc.Dropdown(
                id="compose-format",
                options=[
                    {"label": "PNG", "value": "png"},
                    {"label": "JPG", "value": "jpg"},
                ],
                value="png",
                clearable=False,
                className="mb-2",
            ),
            dbc.Label("Filename", className="small mb-0"),
            dbc.Input(
                id="compose-filename",
                type="text",
                value="composition",
                size="sm",
                className="mb-2",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(
                            "Preview",
                            id="compose-preview",
                            color="secondary",
                            outline=True,
                            size="sm",
                            className="w-100",
                        )
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Export grid",
                            id="compose-export",
                            color="primary",
                            size="sm",
                            className="w-100",
                        )
                    ),
                ]
            ),
            dbc.Alert(
                id="compose-error",
                color="danger",
                dismissable=True,
                is_open=False,
                className="py-2 small mt-2",
            ),
            dcc.Download(id="compose-download"),
        ]
    )


def make_panel_list() -> list:
    """Panel cards in composition order, with move-up/remove buttons."""
    panels = compose.list_panels()
    if not panels:
        return [
            html.Small(
                "No panels saved yet - build a figure, then save it here.",
                className="text-muted d-block mb-2",
            )
        ]
    cards = []
    for position, (pid, spec) in enumerate(panels):
        cards.append(
            dbc.Card(
                dbc.CardBody(
                    html.Div(
                        [
                            html.Small(
                                f"{compose.panel_label(position)} {spec.title}",
                                className="text-truncate me-1",
                            ),
                            html.Div(
                                [
                                    dbc.Button(
                                        "Up",
                                        id=panel_action_id("up", pid),
                                        color="link",
                                        size="sm",
                                        className="p-0 me-2 small",
                                        disabled=position == 0,
                                    ),
                                    dbc.Button(
                                        "Remove",
                                        id=panel_action_id("remove", pid),
                                        color="link",
                                        size="sm",
                                        className="p-0 text-danger small",
                                    ),
                                ],
                                className="flex-shrink-0",
                            ),
                        ],
                        className="d-flex justify-content-between align-items-center",
                    ),
                    className="p-2",
                ),
                className="mb-1",
            )
        )
    return cards


def make_preview_image(png_bytes: bytes) -> html.Img:
    """The stitched preview, shown in the main figure area."""
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return html.Img(
        src=f"data:image/png;base64,{encoded}",
        style={"maxWidth": "100%", "height": "auto"},
        className="border",
    )
