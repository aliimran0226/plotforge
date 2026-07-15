# PlotForge

**A local playground for building publication-ready figures — no coding required.**

PlotForge runs on your own computer and opens in your browser. Upload a CSV, TSV, or Excel file, pick a chart type, map your columns, fine-tune every visual detail live, and export a high-resolution PNG/JPG or vector SVG/PDF ready for a paper, poster, or slide deck.

- 13 chart types: scatter, line, bar, histogram, box, violin, strip/jitter, heatmap, 2D density, ECDF, area, pie, and error-bar plots
- Deep styling: sizes, fonts, titles, per-axis ranges/log/ticks/grids, color palettes (including colorblind-safe), per-group colors, legend placement, templates
- High-DPI export at any pixel size with a 1–5× scale factor, plus vector SVG/PDF output
- Your data never leaves your machine

## Installation

You need **Python 3.10 or newer** ([python.org/downloads](https://www.python.org/downloads/)).

```bash
git clone <repository-url>
cd plotforge

# Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Launching

```bash
python run.py
```

A browser tab opens automatically (something like `http://127.0.0.1:8050`). Keep the terminal window open while you work; press `Ctrl+C` there to stop. If the default port is busy, PlotForge automatically picks the next free one.

## Step-by-step walkthrough

The sidebar walks you through four numbered sections, top to bottom. The figure on the right updates live after every change.

### 1. Data — upload your file

Drag a file onto the upload box (or click it to browse). You'll see:

- the filename with row and column counts,
- a preview of the first 15 rows,
- each column's detected type in the header: `(#)` numeric, `(abc)` text/categorical, `(date)` dates.

For Excel workbooks with several sheets, a **sheet picker** appears — switching sheets re-reads the data instantly.

**Data expectations:** the first row should be column headers, and each subsequent row one observation ("tidy"/long format works best — e.g. columns `dose`, `response`, `treatment_group` rather than one column per group). Wide numeric tables are supported by the heatmap's "Wide matrix" option.

### 2. Chart — pick a type and map columns

Choose a chart type, then tell PlotForge which column goes where. Only the slots that chart supports are shown; required ones are pre-filled with a sensible guess so you get a figure immediately. Common optional slots:

- **Color / group** — split the data into colored groups (one legend entry each)
- **Facet rows / columns** — split into a grid of subplots
- Chart-specific extras appear below (histogram bins, box notches, donut hole, error-bar columns, …)

Columns that don't fit a slot's type are greyed out rather than hidden, so you can see why something isn't selectable.

### 3. Style — make it publication-ready

Six collapsible groups of controls, all live:

- **Figure** — width/height, template (overall look), backgrounds, margins
- **Titles & Fonts** — figure title (text/size/color/alignment), global font, axis-title size
- **X Axis / Y Axis** — title, fixed range, log scale, reversed, tick size/angle/format, gridlines, zero line, axis line and mirrored "box" frame
- **Colors & Groups** — qualitative palette (try *Safe* for colorblind-friendly figures), continuous colorscale, opacity, and manual per-group color pickers
- **Legend** — show/hide, title, position (outside, below, or inside a corner), orientation, font size

**Reset style to defaults** at the top of the section undoes all styling in one click (your data and column mappings stay).

### 4. Export — save the figure

Set the output size in pixels, a **scale factor** (pixel multiplier for high-DPI output — scale 3 of a 1200×800 figure yields 3600×2400 px, roughly 300 DPI at print size), the format (PNG, JPG, or vector SVG/PDF — vector formats stay sharp at any size and are what most journals prefer), and a filename, then click **Export figure**. The download uses exactly the figure and style you see, rendered at the export size rather than the on-screen size.

The small camera icon in the figure's toolbar also saves a quick screen-resolution PNG.

## Supported file formats

| Format | Extensions | Notes |
|---|---|---|
| CSV | `.csv`, `.txt` | Separator auto-detected (`,` `;` tab …) |
| TSV | `.tsv` | Tab-separated |
| Excel | `.xlsx`, `.xls` | Multi-sheet supported; pick the sheet after upload |

## Troubleshooting

**The browser tab doesn't open / "port in use"**
PlotForge scans for a free port automatically; check the terminal for the actual URL. To force a port: `python run.py --port 8123`.

**"Could not parse …" after upload**
Check that the first row contains column names and that rows have a consistent number of cells. Files exported from Excel as "CSV UTF-8" work well.

**Excel upload fails**
The file may be password-protected or corrupted. If you installed dependencies yourself, make sure `openpyxl` is present: `pip install openpyxl`.

**Export fails but the figure looks fine**
Static export uses the `kaleido` library, which needs a Chromium-based browser (Chrome or Edge) on the machine. If none is found, run `plotly_get_chrome` inside the activated virtual environment to download one, then try again. The camera icon in the figure toolbar is a quick fallback.

**Dates are treated as text**
PlotForge detects date columns when at least ~90 % of the values parse as dates. Mixed or unusual formats may fall back to categorical; a consistent format like `2025-01-31` is safest.

## For developers

Want to add a chart type or style option? See [README_DEV.md](README_DEV.md) for the developer guide and [tool_structure.md](tool_structure.md) for the design rationale. The short version: chart types are self-contained modules registered in `plotforge/plots/`, and the UI generates itself from their declarations.
