"""Dash application factory.

``create_app()`` builds the Dash app: theme, layout, and callback
registration. Kept as a factory so tests can create isolated app
instances.
"""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc

import plotforge.plots  # noqa: F401  (imports register all chart types)
from plotforge.callbacks import (
    compose_callbacks,
    data_callbacks,
    export_callbacks,
    layer_callbacks,
    plot_callbacks,
    style_callbacks,
)
from plotforge.ui.layout import build_layout


def create_app() -> dash.Dash:
    """Create and configure the PlotForge Dash application."""
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
        title="PlotForge",
        # Callbacks reference components that only exist after later
        # phases add them dynamically; don't error on missing ids.
        suppress_callback_exceptions=True,
    )
    # Assigned as a function so the layout is rebuilt per page load:
    # parts of it reflect server-side state (the Compose panel list),
    # which would otherwise be frozen at server-start.
    app.layout = build_layout
    # App-chrome dark mode: flips Bootstrap's color mode on <html>.
    # Figures are unaffected - their look comes from the plotly template.
    app.clientside_callback(
        "function(on) {"
        "document.documentElement.setAttribute("
        "'data-bs-theme', on ? 'dark' : 'light');"
        "return '';"
        "}",
        dash.Output("theme-dummy", "children"),
        dash.Input("theme-switch", "value"),
    )
    data_callbacks.register_callbacks(app)
    plot_callbacks.register_callbacks(app)
    layer_callbacks.register_callbacks(app)
    style_callbacks.register_callbacks(app)
    export_callbacks.register_callbacks(app)
    compose_callbacks.register_callbacks(app)
    return app
