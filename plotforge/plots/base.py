"""BasePlot: the contract every chart type implements.

A plot class declares *what it needs* (required mappings), *what it can
use* (optional mappings), and *what it can tweak* (extra options) as
data. The UI is generated from these declarations, so the class itself
only has to implement ``build()``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd
import plotly.graph_objects as go

#: Column kinds produced by ``data.loader.infer_column_types``.
Kind = str  # 'numeric' | 'categorical' | 'datetime'
ANY_KIND: tuple[Kind, ...] = ("numeric", "categorical", "datetime")


class PlotError(Exception):
    """A figure-building problem with a user-facing message."""


@dataclass(frozen=True)
class MappingSpec:
    """One column slot of a chart (e.g. 'x', 'color', 'error_y').

    Attributes:
        name: Keyword passed to ``build()`` (and usually to plotly.express).
        label: Text shown in the UI.
        kinds: Column types this slot accepts; used both to annotate the
            dropdown and to validate the user's selection.
        help: Optional one-line hint shown under the dropdown.
    """

    name: str
    label: str
    kinds: tuple[Kind, ...] = ANY_KIND
    help: str = ""


@dataclass(frozen=True)
class OptionSpec:
    """One chart-specific option (e.g. histogram bin count).

    Attributes:
        name: Key in the ``options`` dict passed to ``build()``.
        label: Text shown in the UI.
        widget: 'dropdown' | 'number' | 'checkbox' | 'slider'.
        default: Initial value.
        choices: For dropdowns: list of values or (label, value) pairs.
        min / max / step: For number inputs and sliders.
    """

    name: str
    label: str
    widget: str
    default: object = None
    choices: list = field(default_factory=list)
    min: float | None = None
    max: float | None = None
    step: float | None = None


# Optional-mapping specs shared by many chart types; plots reference
# these instead of redefining them so labels stay consistent.
COLOR = MappingSpec("color", "Color / group", ("categorical", "numeric", "datetime"))
COLOR_CAT = MappingSpec("color", "Color / group", ("categorical",))
FACET_ROW = MappingSpec("facet_row", "Facet rows", ("categorical",))
FACET_COL = MappingSpec("facet_col", "Facet columns", ("categorical",))
SIZE = MappingSpec("size", "Marker size", ("numeric",))
SYMBOL = MappingSpec("symbol", "Marker symbol", ("categorical",))


class BasePlot(ABC):
    """Abstract base for all chart types.

    Subclasses set the class attributes below, implement ``build()``,
    and register themselves with ``@register_plot``.
    """

    #: Unique machine name (used as the dropdown value and registry key).
    name: str = ""
    #: Human-readable label shown in the chart-type dropdown.
    label: str = ""
    #: Slots the user must fill before the figure can build.
    required_mappings: tuple[MappingSpec, ...] = ()
    #: Slots that enhance the figure but may stay empty.
    optional_mappings: tuple[MappingSpec, ...] = ()
    #: Chart-specific options rendered in the sidebar.
    extra_options: tuple[OptionSpec, ...] = ()

    @classmethod
    @abstractmethod
    def build(
        cls,
        df: pd.DataFrame,
        mapping: dict[str, str],
        options: dict[str, object],
    ) -> go.Figure:
        """Build the figure for ``df``.

        Args:
            df: The uploaded data.
            mapping: Slot name -> column name, for every filled slot.
            options: Option name -> current value, for every extra option
                (missing keys fall back to the OptionSpec default).

        Returns:
            An unstyled figure; global styling is applied afterwards by
            ``styling.apply.apply_style``.

        Raises:
            PlotError: For data problems the user can fix.
        """

    # -- helpers usable by all subclasses ---------------------------------

    @classmethod
    def all_mappings(cls) -> tuple[MappingSpec, ...]:
        """Required followed by optional mapping specs."""
        return tuple(cls.required_mappings) + tuple(cls.optional_mappings)

    @classmethod
    def option_defaults(cls) -> dict[str, object]:
        """Option name -> default value for every extra option."""
        return {opt.name: opt.default for opt in cls.extra_options}

    @classmethod
    def validate(
        cls,
        mapping: dict[str, str],
        column_types: dict[str, str],
        options: dict[str, object] | None = None,
    ) -> None:
        """Check required slots are filled and column kinds are allowed.

        ``options`` lets plots whose requirements depend on a mode option
        (e.g. heatmap wide vs long) override this with custom checks.

        Raises:
            PlotError: With a message naming the offending slot/column.
        """
        for spec in cls.required_mappings:
            if not mapping.get(spec.name):
                raise PlotError(
                    f"{cls.label} needs a column for '{spec.label}'. "
                    "Pick one in the Chart section."
                )
        for spec in cls.all_mappings():
            col = mapping.get(spec.name)
            if not col:
                continue
            if col not in column_types:
                raise PlotError(
                    f"Column '{col}' (mapped to '{spec.label}') no longer "
                    "exists in the data. Re-select a column."
                )
            kind = column_types[col]
            if kind not in spec.kinds:
                allowed = " or ".join(spec.kinds)
                raise PlotError(
                    f"'{spec.label}' needs a {allowed} column, but "
                    f"'{col}' is {kind}. Pick a different column."
                )


def clean_mapping(mapping: dict[str, object]) -> dict[str, str]:
    """Drop empty/None slots so px kwargs only contain real selections."""
    return {k: v for k, v in mapping.items() if v}


def merged_options(plot_cls: type[BasePlot], options: dict[str, object]) -> dict:
    """Overlay user-provided option values on the plot's defaults."""
    merged = plot_cls.option_defaults()
    for key, value in (options or {}).items():
        if key in merged and value is not None:
            merged[key] = value
    return merged
