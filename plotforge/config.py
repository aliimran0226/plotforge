"""Central defaults for PlotForge.

Every user-tweakable default lives here so it can be changed in one
place: figure geometry, fonts, color palettes, templates, and export
settings. ``styling.style_model.StyleModel`` pulls its field defaults
from this module.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Figure geometry
# --------------------------------------------------------------------------
FIGURE_WIDTH: int = 800  # on-screen figure width in px
FIGURE_HEIGHT: int = 550  # on-screen figure height in px
MARGIN: dict[str, int] = {"l": 70, "r": 30, "t": 60, "b": 60}

# --------------------------------------------------------------------------
# Template / background
# --------------------------------------------------------------------------
TEMPLATE: str = "plotly_white"
TEMPLATES: list[str] = [
    "plotly_white",
    "simple_white",
    "plotly",
    "ggplot2",
    "seaborn",
    "presentation",
    "none",
]
PAPER_BGCOLOR: str = "#ffffff"
PLOT_BGCOLOR: str = "#ffffff"

# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------
FONT_FAMILY: str = "Arial"
FONT_FAMILIES: list[str] = [
    "Arial",
    "Helvetica",
    "Times New Roman",
    "Georgia",
    "Courier New",
    "Verdana",
    "Open Sans",
    "Computer Modern",  # LaTeX-like; falls back gracefully if not installed
]
TITLE_FONT_SIZE: int = 20
AXIS_TITLE_FONT_SIZE: int = 14
TICK_FONT_SIZE: int = 12
LEGEND_FONT_SIZE: int = 12

# --------------------------------------------------------------------------
# Color palettes
# --------------------------------------------------------------------------
# Qualitative palettes offered in the UI. Keys are the labels shown to the
# user; values are the attribute names on plotly.express.colors.qualitative.
QUALITATIVE_PALETTES: dict[str, str] = {
    "Plotly": "Plotly",
    "D3": "D3",
    "G10": "G10",
    "T10": "T10",
    "Safe (colorblind)": "Safe",
    "Vivid": "Vivid",
    "Bold": "Bold",
    "Pastel": "Pastel",
    "Dark24": "Dark24",
    "Set1": "Set1",
    "Set2": "Set2",
}
DEFAULT_QUALITATIVE_PALETTE: str = "Plotly"

# Continuous colorscales offered for heatmaps / density / continuous color.
CONTINUOUS_COLORSCALES: list[str] = [
    "Viridis",
    "Plasma",
    "Inferno",
    "Magma",
    "Cividis",
    "Blues",
    "Greens",
    "Reds",
    "YlOrRd",
    "YlGnBu",
    "RdBu",
    "Spectral",
    "Turbo",
    "Greys",
]
DEFAULT_CONTINUOUS_COLORSCALE: str = "Viridis"

# --------------------------------------------------------------------------
# Export defaults
# --------------------------------------------------------------------------
EXPORT_WIDTH: int = 1200
EXPORT_HEIGHT: int = 800
EXPORT_SCALE: int = 3  # scale 3 ~= 300 DPI at typical figure sizes
EXPORT_FORMAT: str = "png"
EXPORT_FILENAME: str = "figure"

# --------------------------------------------------------------------------
# Data handling
# --------------------------------------------------------------------------
PREVIEW_ROWS: int = 15  # rows shown in the upload preview table
MAX_CATEGORIES: int = 50  # cap on discrete categories in one figure (e.g. pie slices)
