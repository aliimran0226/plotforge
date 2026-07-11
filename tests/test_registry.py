"""Tests for the plot registry and BasePlot declarations/validation."""

from __future__ import annotations

import pytest

import plotforge.plots  # noqa: F401  (registers the built-in chart types)
from plotforge.plots.base import BasePlot, MappingSpec, PlotError
from plotforge.plots.registry import all_plots, get_plot, register_plot


def test_builtin_plots_registered():
    plots = all_plots()
    for expected in ("scatter", "line", "bar", "histogram"):
        assert expected in plots


def test_get_plot_unknown_name():
    with pytest.raises(KeyError, match="nope"):
        get_plot("nope")


def test_register_requires_name():
    with pytest.raises(ValueError, match="non-empty 'name'"):

        @register_plot
        class Nameless(BasePlot):  # pragma: no cover - class body only
            @classmethod
            def build(cls, df, mapping, options):
                raise NotImplementedError


def test_register_rejects_duplicates():
    with pytest.raises(ValueError, match="Duplicate"):

        @register_plot
        class Impostor(BasePlot):  # pragma: no cover - class body only
            name = "scatter"

            @classmethod
            def build(cls, df, mapping, options):
                raise NotImplementedError


def test_every_plot_declares_ui_metadata():
    """The UI is generated from these attributes - they must exist."""
    for name, cls in all_plots().items():
        assert cls.label, f"{name} missing label"
        assert cls.required_mappings, f"{name} declares no required mappings"
        for spec in cls.all_mappings():
            assert isinstance(spec, MappingSpec)
            assert spec.kinds, f"{name}.{spec.name} accepts no column kinds"


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------

TYPES = {"dose": "numeric", "group": "categorical", "when": "datetime"}


def test_validate_missing_required():
    scatter = get_plot("scatter")
    with pytest.raises(PlotError, match="needs a column"):
        scatter.validate({"x": "dose"}, TYPES)  # y missing


def test_validate_wrong_kind():
    scatter = get_plot("scatter")
    with pytest.raises(PlotError, match="categorical"):
        scatter.validate({"x": "dose", "y": "group"}, TYPES)


def test_validate_vanished_column():
    scatter = get_plot("scatter")
    with pytest.raises(PlotError, match="no longer"):
        scatter.validate({"x": "dose", "y": "gone"}, TYPES)


def test_validate_ok():
    scatter = get_plot("scatter")
    scatter.validate({"x": "dose", "y": "dose", "color": "group"}, TYPES)
