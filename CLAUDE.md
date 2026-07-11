# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PlotForge: a single-user, locally run Dash/Plotly app for building publication-ready figures from uploaded CSV/TSV/Excel data. PLAN.md is the original implementation plan; the app is fully implemented.

## Commands

All commands use the project venv (`.venv/`). Activate it, or prefix with `.venv\Scripts\python -m` (Windows) / `.venv/bin/python -m`.

```bash
pip install -e ".[dev]"        # dev setup (package + pytest, black, ruff)
python run.py --debug          # run with hot reload; scans for a free port from 8050 up
pytest                         # full suite
pytest tests/test_plots.py -k heatmap   # single test / area
black plotforge tests run.py   # format (required before commit)
ruff check plotforge tests run.py       # lint (--fix for autofixes)
```

Machine note: port 8050 is often occupied here (unrelated app); `run.py` handles it. The kaleido export tests need a Chromium browser and auto-skip without one.

## Architecture

Render pipeline (one pass, everything else hangs off it):

upload → `data/loader.py` (parse + dtype inference: numeric/categorical/datetime) → `data/store.py` (server-side dict cache; browser only holds a token in `dcc.Store("dataset-token")`) → mapping UI generated from the plot registry → `render_figure` callback → `BasePlot.build()` (bare figure) → `styling/apply.py:apply_style()` (all styling) → `dcc.Graph`. Export (`callbacks/export_callbacks.py`) reruns this exact path at the requested size via kaleido — it never screenshots the on-screen graph.

Two generation mechanisms make the UI declarative; understand both before touching UI code:

1. **Plot registry** (`plots/registry.py`): each chart type is one module in `plotforge/plots/` with a `BasePlot` subclass declaring `name`, `label`, `required_mappings`/`optional_mappings` (`MappingSpec`), `extra_options` (`OptionSpec`), and a `build(df, mapping, options)` classmethod, registered with `@register_plot` and imported in `plots/__init__.py` (**import order = dropdown order; the import list has `isort:skip` — keep it**). The chart dropdown, mapping dropdowns, and option widgets are all generated from these declarations.
2. **StyleModel** (`styling/style_model.py`): one dataclass field per style option. Style controls in `ui/controls_style.py` use pattern ids `{"type": "style", "field": <field name>}` — the field name in the `_SECTIONS` table is the link between control, dataclass, and `apply_style`. Adding an option = field + `_SECTIONS` entry + `apply_style` line.

All runtime-generated controls use dict (pattern-matching) ids; callbacks read them with `ALL` matchers and rebuild dicts from `ctx.inputs_list`/`states_list`.

Division of responsibility: `build()` never sets colors/fonts/sizes — `apply_style` owns all styling (it re-assigns trace colors post-build because plotly.express bakes them in; `layout.colorway` alone is not enough). Callbacks stay thin; logic lives in importable functions in `data/`, `plots/`, `styling/` so it is testable without Dash.

Error handling contract: raise `LoaderError` (data) or `PlotError` (figures) with user-readable messages — callbacks display them verbatim in alerts. `validate(mapping, column_types, options)` can be overridden for mode-dependent requirements (see heatmap's wide/long modes).

## Conventions with teeth

- `tests/test_plots.py::SMOKE_MAPPINGS` must contain an entry for every registered chart type — a test fails otherwise. Fixture columns: `dose`, `response`, `response_err` (numeric), `group`, `batch` (categorical), `measured_on` (datetime).
- Same-commit rule: design changes update `tool_structure.md` (the why, dated entries); changes to extension recipes or the callback map update `README_DEV.md` (the how). Step-by-step extension guides live in README_DEV.md — follow them rather than improvising.
- Conventional commit messages (`feat:`, `fix:`, `docs:`, `chore:`).
- Version bumps touch both `pyproject.toml` and `plotforge/__init__.py`.
