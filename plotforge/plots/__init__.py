"""Plot modules.

Each module in this package defines one chart type as a ``BasePlot``
subclass registered via ``@register_plot``. Importing a module here is
what makes its chart type appear in the UI - see ``registry.py`` and
the "How to add a new chart type" recipe in README_DEV.md.
"""

# Import order = order in the chart-type dropdown (first entry is the
# default chart), so keep this list deliberately ordered.
# isort:skip is required to stop the formatter re-alphabetizing it.
from plotforge.plots import (  # noqa: F401  # isort:skip
    scatter,
    line,
    bar,
    histogram,
    box,
    violin,
    strip,
    heatmap,
    density,
    ecdf,
    area,
    pie,
    errorbar,
)
