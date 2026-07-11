"""Dash application factory.

``create_app()`` builds the Dash app: theme, layout, and callback
registration. Kept as a factory so tests can create isolated app
instances.
"""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc

import plotforge.plots  # noqa: F401  (imports register all chart types)
from plotforge.callbacks import data_callbacks, plot_callbacks
from plotforge.ui.layout import build_layout


def create_app() -> dash.Dash:
    """Create and configure the PlotForge Dash application."""
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.FLATLY],
        title="PlotForge",
        # Callbacks reference components that only exist after later
        # phases add them dynamically; don't error on missing ids.
        suppress_callback_exceptions=True,
    )
    app.layout = build_layout()
    data_callbacks.register_callbacks(app)
    plot_callbacks.register_callbacks(app)
    return app
