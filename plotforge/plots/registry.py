"""Plot-type registry - THE extension point for new chart types.

Plot classes register themselves with the ``@register_plot`` decorator.
The chart-type dropdown, the column-mapping UI, and the chart-specific
options UI are all generated from this registry, so adding a chart type
means: write one module with a ``BasePlot`` subclass, decorate it, and
import it in ``plots/__init__.py``. Nothing else changes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid a circular import at runtime; base imports nothing from here
    from plotforge.plots.base import BasePlot

# Maps plot ``name`` -> plot class, in registration (i.e., import) order.
_REGISTRY: dict[str, type[BasePlot]] = {}


def register_plot(cls: type[BasePlot]) -> type[BasePlot]:
    """Class decorator that adds a ``BasePlot`` subclass to the registry.

    Args:
        cls: The plot class. Must define a unique, non-empty ``name``.

    Returns:
        The class unchanged (so the decorator is transparent).

    Raises:
        ValueError: If ``name`` is missing or already registered.
    """
    name = getattr(cls, "name", "")
    if not name:
        raise ValueError(f"{cls.__name__} must define a non-empty 'name' attribute")
    if name in _REGISTRY:
        raise ValueError(f"Duplicate plot name {name!r} ({cls.__name__})")
    _REGISTRY[name] = cls
    return cls


def get_plot(name: str) -> type[BasePlot]:
    """Return the plot class registered under ``name``.

    Raises:
        KeyError: If no plot with that name is registered.
    """
    if name not in _REGISTRY:
        raise KeyError(f"No plot registered under {name!r}")
    return _REGISTRY[name]


def all_plots() -> dict[str, type[BasePlot]]:
    """Return a copy of the registry (name -> class, in registration order)."""
    return dict(_REGISTRY)
