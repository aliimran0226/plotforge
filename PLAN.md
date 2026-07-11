# Implementation Plan: PlotForge — Publication-Ready Figure Playground

## Instructions for Claude Code

You are implementing a local, browser-based data visualization playground in Python using Dash and Plotly. A scientist uploads a CSV/TSV/Excel file and interactively builds publication-ready figures with deep customization. Follow this plan phase by phase, committing to git at each milestone. Read the whole plan before writing any code.

---

## 1. Project Goal

A single-user, locally run web app (`python run.py` opens a browser tab) that:

1. Accepts CSV, TSV, and Excel (`.xlsx`, `.xls`) uploads, including multi-sheet Excel files (user picks the sheet).
2. Offers a wide range of chart types (see §4).
3. Exposes a "playground" customization panel: every visual property a scientist needs for a publication figure is adjustable live (see §5).
4. Exports figures as PNG/JPG at user-specified resolution (width/height in px + scale factor for high DPI).
5. Is architected so new chart types and new customization options can be added later with minimal changes (see §6).

## 2. Tech Stack

- **Python ≥ 3.10**
- **Dash** (UI framework) + **dash-bootstrap-components** (clean layout, accordions, tabs)
- **Plotly** (figures)
- **pandas** (data handling), **openpyxl** (Excel reading)
- **kaleido** (static PNG/JPG export server-side; also enable Plotly's built-in modebar download as a fallback)
- Pin all versions in `requirements.txt`. Also provide `pyproject.toml` so the project is pip-installable (`pip install -e .`).

## 3. Repository Structure

```
plotforge/
├── README.md                  # User-facing guide (see §9)
├── README_DEV.md              # Developer guide (see §10)
├── tool_structure.md          # Living design-decision log (see §11)
├── requirements.txt
├── pyproject.toml
├── .gitignore                 # Python template + uploads/, exports/, .venv/
├── run.py                     # Entry point: starts server, opens browser tab
├── plotforge/
│   ├── __init__.py
│   ├── app.py                 # Dash app factory, layout assembly
│   ├── config.py              # Defaults: figure size, fonts, palettes, themes
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py          # File parsing (csv/tsv/xlsx), sheet selection,
│   │   │                      #   dtype inference, categorical vs numeric detection
│   │   └── store.py           # Server-side data cache keyed by session
│   ├── plots/
│   │   ├── __init__.py
│   │   ├── registry.py        # Plot-type registry (see §6) — THE extension point
│   │   ├── base.py            # BasePlot abstract class: build(df, mapping, style) -> go.Figure
│   │   ├── scatter.py
│   │   ├── line.py
│   │   ├── bar.py
│   │   ├── histogram.py
│   │   ├── box.py
│   │   ├── violin.py
│   │   ├── heatmap.py
│   │   ├── density.py         # KDE / density contour
│   │   ├── ecdf.py
│   │   ├── strip.py
│   │   ├── area.py
│   │   ├── pie.py
│   │   └── errorbar.py        # scatter/line with error bar columns
│   ├── styling/
│   │   ├── __init__.py
│   │   ├── style_model.py     # Dataclass capturing ALL style options (single source of truth)
│   │   └── apply.py           # apply_style(fig, style) — one function styles any figure
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── layout.py          # Page skeleton: sidebar (controls) + main (figure)
│   │   ├── controls_data.py   # Upload widget, sheet picker, data preview table
│   │   ├── controls_mapping.py# Chart type selector + dynamic column-mapping dropdowns
│   │   ├── controls_style.py  # Accordion of style controls (built from style_model)
│   │   └── controls_export.py # Export size / scale / format / filename
│   └── callbacks/
│       ├── __init__.py
│       ├── data_callbacks.py
│       ├── plot_callbacks.py
│       └── export_callbacks.py
└── tests/
    ├── test_loader.py
    ├── test_registry.py
    └── test_plots.py          # Each plot builds without error on sample data
    └── fixtures/              # Small sample csv/tsv/xlsx files
```

## 4. Chart Types (initial set)

Scatter, Line, Bar (grouped/stacked), Histogram (count/density, bin control), Box, Violin, Strip/Jitter, Heatmap (from long or wide data), Density contour / 2D histogram, ECDF, Area, Pie, Scatter/Line with error bars (map error columns).

Each chart type declares:
- **Required mappings** (e.g., histogram needs `x`; scatter needs `x`,`y`)
- **Optional mappings** (`color`/group, `facet_row`, `facet_col`, `size`, `symbol`, `error_x`, `error_y` — only where meaningful)
- **Type-specific options** (e.g., histogram: bin count, normalization, barmode; box: points shown, notches; violin: box overlay, points)

The mapping UI must rebuild dynamically when the chart type changes, showing only what that chart supports. Column dropdowns should indicate inferred type (numeric / categorical / datetime).

## 5. Style / Customization Panel

Implement `StyleModel` as a dataclass — one field per option, with defaults in `config.py`. Group into UI accordion sections:

**Figure**: width, height (px); background color (paper + plot area); Plotly template (plotly_white, simple_white, etc.); margins.
**Titles & Fonts**: figure title (text, size, font family, color, alignment); global font family; separate font sizes for axis titles, tick labels, legend.
**X Axis / Y Axis** (identical control sets): axis title text; range (auto or min/max); scale (linear/log); tick label size, angle; tick format; gridlines on/off + color; zero line; axis line + mirror (box frame); reversed.
**Colors & Groups**: qualitative palette picker (Plotly, D3, colorblind-safe sets like Safe/Vivid); continuous colorscale picker; per-group manual color override (color pickers generated per detected group); opacity.
**Legend**: show/hide, title, position (inside corners / outside right / below), orientation, font size.
**Chart-specific**: rendered from the active plot type's declared options (§4).

All controls update the figure live via a single callback that: reads mappings + StyleModel from control values → gets `go.Figure` from the registry → passes through `apply_style()` → renders in `dcc.Graph`.

## 6. Extensibility Architecture (critical)

- **Plot registry pattern**: each plot module defines a class inheriting `BasePlot` with class attributes `name`, `label`, `required_mappings`, `optional_mappings`, `extra_options` (schema: name, label, widget type, default, choices) and a `build()` method. A decorator `@register_plot` adds it to the registry. The chart-type dropdown, mapping UI, and options UI are all **generated from the registry** — adding a new chart type means adding one file and one import, touching nothing else.
- **StyleModel as single source of truth**: style controls in the UI are generated from (or at minimum explicitly kept in sync with) the dataclass fields. Adding a style option = add a field + a control entry + one line in `apply_style`.
- Keep callbacks thin; all logic lives in importable, testable functions.
- Document this pattern in `tool_structure.md` with a "How to add a new chart type" recipe.

## 7. UX Requirements

- Layout: left sidebar with tabs/accordions (Data → Chart → Style → Export), large figure area on the right.
- On upload: show filename, row/column counts, and a preview table (first ~15 rows) with inferred dtypes.
- Sensible defaults everywhere — an uploaded file + chart type + x/y selection should immediately produce a decent figure with zero style tweaking.
- Friendly, specific error messages (bad file, non-numeric column mapped to numeric-only slot, empty selection) shown in dismissible alerts — never a stack trace or silent failure.
- A "Reset style to defaults" button.
- Figure area uses `dcc.Loading` spinner during redraws.

## 8. Export

- Export section: width (px), height (px), scale factor (1–5, note that scale 3 ≈ 300 DPI for typical sizes), format (PNG/JPG), filename.
- Server-side export via kaleido, delivered with `dcc.Download`.
- Export uses the exact current figure + style, at the requested dimensions (not the on-screen size).

## 9. README.md (write for the end user, not developers)

Must include: what the tool is; installation (`git clone`, venv, `pip install -r requirements.txt`); launching (`python run.py`); a step-by-step walkthrough (upload → pick chart → map columns → style → export) ideally with the sidebar sections explained; supported file formats and expectations (header row, tidy/long data recommended); troubleshooting section (port in use, Excel engine missing, kaleido export issues); and a short developer note linking to `README_DEV.md`.

## 10. README_DEV.md (developer guide)

Write for a developer who wants to modify or extend the tool. Keep it practical and code-oriented; it complements (not duplicates) `tool_structure.md` — README_DEV is *how to work on the project*, tool_structure is *why it's designed this way*. Must include:

- **Dev environment setup**: clone, venv, `pip install -e ".[dev]"` (define a `dev` extra in pyproject.toml with pytest, black, ruff), running the app in debug mode (`python run.py --debug` with Dash hot-reload enabled).
- **Codebase tour**: walk through the request/render flow end to end — upload → `data/loader.py` → server-side store → mapping controls → `plots/registry.py` → `BasePlot.build()` → `styling/apply.py` → `dcc.Graph` → export callback. A simple ASCII or Mermaid flow diagram of this pipeline.
- **Extension guides (step-by-step, with code snippets)**:
  - Adding a new chart type: copy an existing plot module, define class attributes and `build()`, register with `@register_plot`, add the import, add a test fixture case.
  - Adding a new style option: add the `StyleModel` field, the control entry, the `apply_style` line, and update defaults in `config.py`.
  - Adding a new file format to the loader.
- **Callback map**: table of every Dash callback — inputs, outputs, which module owns it — so developers can trace UI behavior quickly.
- **Testing**: how to run the suite (`pytest`), what the fixtures cover, expectations for tests accompanying new plots/options.
- **Code style & tooling**: black/ruff commands, docstring and commenting conventions, type-hint policy.
- **Release/versioning note**: bump version in pyproject.toml, tag releases, update tool_structure.md changelog entries.
- Keep README_DEV.md updated whenever the extension recipes or callback map change (same-commit rule, like tool_structure.md).

## 11. tool_structure.md (living design log)

Create at project start and **update it in the same commit as any design change**. Contents:
- Architecture overview + module map (mirror of §3 with one-line purpose each)
- Key design decisions with rationale, as a running log (framework choice, registry pattern, StyleModel, server-side export, data caching approach), each entry dated
- Pointers to the step-by-step extension recipes in README_DEV.md (don't duplicate them here; this file records the *why*, README_DEV records the *how*)
- Known limitations / future ideas (e.g., SVG/PDF export, figure recipes, multi-panel composition)

## 12. Code Quality

- Comment generously: every module gets a docstring stating its role; every public function gets a docstring (args, returns); non-obvious logic gets inline comments explaining *why*.
- Type hints throughout.
- Format with `black`, lint with `ruff`; include configs in `pyproject.toml`.
- Tests (pytest): loader handles csv/tsv/xlsx + malformed files; every registered plot builds a valid figure on fixture data; `apply_style` applies representative options without error.

## 13. Git / GitHub Workflow

1. `git init` immediately; first commit = skeleton + README stub + README_DEV stub + tool_structure.md stub + .gitignore.
2. Commit at the end of every phase below with clear conventional messages (`feat:`, `fix:`, `docs:`).
3. Create the GitHub repo with `gh repo create` if the `gh` CLI is authenticated; otherwise print the exact commands for the user to create the remote and push, and pause for them.
4. Push after each phase.

## 14. Implementation Phases

**Phase 1 — Skeleton**: repo structure, config, empty registry, Dash app boots with placeholder layout, run.py opens browser. Commit.
**Phase 2 — Data layer**: upload, parsing (csv/tsv/xlsx + sheet picker), dtype inference, preview table, server-side store, error handling. Tests. Commit.
**Phase 3 — Core plotting**: BasePlot + registry + scatter, line, bar, histogram; mapping UI generated from registry; live figure rendering. Commit.
**Phase 4 — Full style panel**: StyleModel, apply_style, all §5 controls wired live. Commit.
**Phase 5 — Remaining chart types** (box, violin, strip, heatmap, density, ecdf, area, pie, errorbar) + chart-specific options. Tests. Commit.
**Phase 6 — Export** (kaleido, dcc.Download, size/scale controls). Commit.
**Phase 7 — Polish & docs**: reset button, loading states, error message audit, finalize README walkthrough, README_DEV (codebase tour, callback map, extension guides), and tool_structure.md; format/lint pass, full test run. Final commit + push.

After each phase, run the app and verify manually before committing. If a library version conflict or Dash API issue forces a deviation from this plan, note the deviation and rationale in tool_structure.md.
