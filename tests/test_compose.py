"""Tests for panel snapshots and grid composition."""

from __future__ import annotations

import io

import pytest

import plotforge.plots  # noqa: F401  (registers the built-in chart types)
from plotforge import compose
from plotforge.data.store import Dataset

TYPES = {
    "dose": "numeric",
    "response": "numeric",
    "response_err": "numeric",
    "group": "categorical",
    "batch": "categorical",
    "measured_on": "datetime",
}


@pytest.fixture(autouse=True)
def clean_panels():
    compose.clear()
    yield
    compose.clear()


@pytest.fixture()
def panel_spec(sample_df):
    dataset = Dataset(
        filename="sample.csv",
        raw=b"",
        df=sample_df,
        sheets=None,
        active_sheet=None,
        column_types=TYPES,
    )
    return compose.PanelSpec(
        chart_type="scatter",
        mapping={"x": "dose", "y": "response", "color": "group"},
        options={},
        style_values={},
        group_colors={},
        decorations={},
        layers=[],
        dataset=dataset,
        title="Scatter - sample.csv",
    )


def test_panel_store_roundtrip(panel_spec):
    pid = compose.save_panel(panel_spec)
    assert [p for p, _ in compose.list_panels()] == [pid]
    compose.remove_panel(pid)
    assert compose.list_panels() == []


def test_panel_store_cap(panel_spec):
    for _ in range(compose.MAX_PANELS + 3):
        compose.save_panel(panel_spec)
    assert len(compose.list_panels()) == compose.MAX_PANELS


def test_move_panel_up(panel_spec):
    first = compose.save_panel(panel_spec)
    second = compose.save_panel(panel_spec)
    compose.move_panel_up(second)
    assert [p for p, _ in compose.list_panels()] == [second, first]
    compose.move_panel_up(second)  # already first: no-op
    assert [p for p, _ in compose.list_panels()] == [second, first]


@pytest.mark.parametrize(
    ("position", "label"),
    [(0, "(a)"), (1, "(b)"), (25, "(z)"), (26, "(aa)"), (27, "(ab)")],
)
def test_panel_label(position, label):
    assert compose.panel_label(position) == label


def test_build_panel_figure_has_label(panel_spec):
    fig = compose.build_panel_figure(panel_spec, 400, 300, label="(a)")
    assert fig.layout.width == 400 and fig.layout.height == 300
    labels = [a for a in fig.layout.annotations if a.text == "<b>(a)</b>"]
    assert len(labels) == 1


def test_compose_grid_geometry(panel_spec):
    for _ in range(3):
        compose.save_panel(panel_spec)
    panels = [spec for _, spec in compose.list_panels()]
    try:
        img = compose.compose_grid(
            panels, columns=2, cell_width=300, cell_height=200, scale=1
        )
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"kaleido unavailable here: {exc}")
    from PIL import Image

    stitched = Image.open(io.BytesIO(img))
    # 3 panels in 2 columns -> 2 rows; unused cell stays white.
    assert stitched.size == (600, 400)


def test_compose_grid_requires_panels():
    with pytest.raises(ValueError, match="No panels"):
        compose.compose_grid([], columns=2)


def test_compose_grid_error_names_the_panel(panel_spec):
    from plotforge.plots.base import PlotError

    # A panel with a broken layer must fail with the panel's label and
    # title in the message, not just the raw layer error.
    panel_spec.layers = [{"chart": "line", "mapping": {}}]
    with pytest.raises(PlotError, match=r"Panel \(a\) \(Scatter - sample\.csv\)"):
        compose.compose_grid([panel_spec], columns=1)
