"""Plot modules.

Each module in this package defines one chart type as a ``BasePlot``
subclass registered via ``@register_plot``. Importing a module here is
what makes its chart type appear in the UI - see ``registry.py`` and
the "How to add a new chart type" recipe in README_DEV.md.
"""

# Import order = order in the chart-type dropdown.
from plotforge.plots import (  # noqa: F401
    bar,
    histogram,
    line,
    scatter,
)
