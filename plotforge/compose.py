"""Figure composition: saved panels arranged in a grid, one image out.

The user snapshots the current figure as a *panel*; a panel stores the
raw control values (mapping, options, style values, layers) plus a
reference to the dataset, so it re-renders exactly like the live figure
did. Composition renders every panel at the cell size via kaleido and
stitches the PNGs with pillow - no plotly subplot merging, so panels
keep their own legends, color axes, and margins.

Vector formats can't be stitched pixelwise, so compositions export as
PNG/JPG only.
"""

from __future__ import annotations

import io
import itertools
import math
import string
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field

from PIL import Image

from plotforge.data.store import Dataset
from plotforge.figure import build_figure
from plotforge.plots.base import PlotError
from plotforge.styling import style_model

#: Keep at most this many saved panels.
MAX_PANELS = 12

#: Default size of one grid cell in px (before scaling).
CELL_WIDTH = 600
CELL_HEIGHT = 420


@dataclass
class PanelSpec:
    """Everything needed to re-render one saved figure."""

    chart_type: str
    mapping: dict[str, object]
    options: dict[str, object]
    style_values: dict[str, object]
    group_colors: dict[str, str]
    decorations: dict[str, list[dict]]
    layers: list[dict]
    #: The dataset itself (not its cache token), so panels survive
    #: dataset-cache eviction and later uploads.
    dataset: Dataset = field(repr=False)
    title: str = ""  # shown in the panel list, e.g. "Scatter - data.csv"


# Insertion-ordered: composition order = save order (with move-up).
_PANELS: OrderedDict[str, PanelSpec] = OrderedDict()


def save_panel(spec: PanelSpec) -> str:
    """Store a panel and return its id. Oldest panel is dropped at the cap."""
    pid = uuid.uuid4().hex
    _PANELS[pid] = spec
    while len(_PANELS) > MAX_PANELS:
        _PANELS.popitem(last=False)
    return pid


def remove_panel(pid: str) -> None:
    _PANELS.pop(pid, None)


def move_panel_up(pid: str) -> None:
    """Swap a panel with its predecessor in composition order."""
    keys = list(_PANELS)
    if pid not in keys or keys.index(pid) == 0:
        return
    i = keys.index(pid)
    keys[i - 1], keys[i] = keys[i], keys[i - 1]
    reordered = OrderedDict((k, _PANELS[k]) for k in keys)
    _PANELS.clear()
    _PANELS.update(reordered)


def list_panels() -> list[tuple[str, PanelSpec]]:
    return list(_PANELS.items())


def clear() -> None:
    """Drop all panels (used by tests)."""
    _PANELS.clear()


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def panel_label(position: int) -> str:
    """0 -> '(a)', 1 -> '(b)', ... 26 -> '(aa)'."""
    letters = string.ascii_lowercase
    n, out = position, ""
    while True:
        n, r = divmod(n, 26)
        out = letters[r] + out
        if n == 0:
            return f"({out})"
        n -= 1


def build_panel_figure(spec: PanelSpec, width: int, height: int, label: str = ""):
    """Re-render one panel at the given cell size, optionally labeled."""
    style = style_model.from_values(
        spec.style_values, spec.group_colors, spec.decorations
    )
    style.width, style.height = width, height
    fig = build_figure(
        spec.chart_type, spec.dataset, spec.mapping, spec.options, style, spec.layers
    )
    if label:
        fig.add_annotation(
            x=0.0,
            y=1.0,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(size=max(14, style.title_size - 4)),
        )
    return fig


def compose_grid(
    panels: list[PanelSpec],
    columns: int,
    cell_width: int = CELL_WIDTH,
    cell_height: int = CELL_HEIGHT,
    scale: int = 1,
    labels: bool = True,
    fmt: str = "png",
) -> bytes:
    """Render every panel and stitch them into one grid image.

    Returns PNG or JPG bytes; the grid fills row by row, left to right,
    with white in unused cells.
    """
    if not panels:
        raise ValueError("No panels saved yet.")
    columns = max(1, min(int(columns or 1), len(panels)))
    rows = math.ceil(len(panels) / columns)

    cw, ch = cell_width * scale, cell_height * scale
    canvas = Image.new("RGB", (columns * cw, rows * ch), "white")
    cells = itertools.product(range(rows), range(columns))
    for (row, col), (position, spec) in zip(cells, enumerate(panels), strict=False):
        label = panel_label(position) if labels else ""
        try:
            fig = build_panel_figure(spec, cell_width, cell_height, label)
        except PlotError as exc:
            # Name the offending panel - the raw message ("Layer 1
            # needs...") gives no hint which saved figure is broken.
            raise PlotError(
                f"Panel {panel_label(position)} ({spec.title}): {exc}"
            ) from exc
        png = fig.to_image(
            format="png", width=cell_width, height=cell_height, scale=scale
        )
        tile = Image.open(io.BytesIO(png)).convert("RGB")
        canvas.paste(tile, (col * cw, row * ch))

    out = io.BytesIO()
    canvas.save(out, format="JPEG" if fmt == "jpg" else "PNG")
    return out.getvalue()
