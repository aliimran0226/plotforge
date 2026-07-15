"""Tests for the export path: filename sanitizing and kaleido rendering.

The kaleido test renders a real PNG/JPG, which needs a Chromium-based
browser on the machine; it is skipped automatically if rendering fails
for environment (not code) reasons.
"""

from __future__ import annotations

import plotly.express as px
import pytest

from plotforge.callbacks.export_callbacks import export_figure_bytes, sanitize_filename

# ---------------------------------------------------------------------------
# sanitize_filename
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "fmt", "expected"),
    [
        ("figure", "png", "figure.png"),
        ("my plot: dose/response", "png", "my_plot_dose_response.png"),
        ("results.png", "jpg", "results.jpg"),  # typed extension dropped
        ("", "png", "figure.png"),
        (None, "jpg", "figure.jpg"),
        ("...", "png", "figure.png"),
    ],
)
def test_sanitize_filename(raw, fmt, expected):
    assert sanitize_filename(raw, fmt) == expected


# ---------------------------------------------------------------------------
# kaleido rendering
# ---------------------------------------------------------------------------


def _small_fig():
    return px.scatter(x=[1, 2, 3], y=[3, 1, 2])


def test_export_png_dimensions_scale():
    try:
        img = export_figure_bytes(_small_fig(), "png", 300, 200, 2)
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"kaleido unavailable here: {exc}")
    assert img[:8] == b"\x89PNG\r\n\x1a\n"
    # PNG IHDR: width/height are bytes 16-24; scale 2 doubles both.
    width = int.from_bytes(img[16:20], "big")
    height = int.from_bytes(img[20:24], "big")
    assert (width, height) == (600, 400)


def test_export_jpg_magic():
    try:
        img = export_figure_bytes(_small_fig(), "jpg", 300, 200, 1)
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"kaleido unavailable here: {exc}")
    assert img[:3] == b"\xff\xd8\xff"


def test_export_svg_magic():
    try:
        img = export_figure_bytes(_small_fig(), "svg", 300, 200, 1)
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"kaleido unavailable here: {exc}")
    assert b"<svg" in img[:300]


def test_export_pdf_magic():
    try:
        img = export_figure_bytes(_small_fig(), "pdf", 300, 200, 1)
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"kaleido unavailable here: {exc}")
    assert img[:5] == b"%PDF-"


@pytest.mark.parametrize(
    ("raw", "fmt", "expected"),
    [
        ("results.svg", "pdf", "results.pdf"),
        ("results.pdf", "svg", "results.svg"),
    ],
)
def test_sanitize_filename_vector_extensions(raw, fmt, expected):
    assert sanitize_filename(raw, fmt) == expected
