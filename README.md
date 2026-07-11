# PlotForge

A local, browser-based playground for building **publication-ready figures** from your data. Upload a CSV/TSV/Excel file, pick a chart type, map columns, tweak every visual property live, and export high-resolution PNG/JPG images.

> **Status:** under construction — full user guide coming with the first release.

## Quick start

```bash
git clone <this-repo>
cd plotforge
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

A browser tab opens at `http://127.0.0.1:8050`.

## For developers

See [README_DEV.md](README_DEV.md) for how to work on the codebase and [tool_structure.md](tool_structure.md) for design decisions.
