# PlotForge — Design Log

Living document: records the architecture and the *why* behind design decisions. Updated in the same commit as any design change. The *how-to-extend* recipes live in [README_DEV.md](README_DEV.md).

## Architecture overview

```
run.py                     Entry point: starts server, opens browser tab
plotforge/
├── app.py                 Dash app factory, layout assembly
├── config.py              Defaults: figure size, fonts, palettes, themes
├── data/
│   ├── loader.py          File parsing (csv/tsv/xlsx), sheet selection, dtype inference
│   └── store.py           Server-side data cache keyed by session
├── plots/
│   ├── registry.py        Plot-type registry — THE extension point
│   ├── base.py            BasePlot abstract class
│   └── <one module per chart type>
├── styling/
│   ├── style_model.py     Dataclass capturing ALL style options
│   └── apply.py           apply_style(fig, style) — styles any figure
├── ui/
│   ├── layout.py          Page skeleton: sidebar (controls) + main (figure)
│   ├── controls_data.py   Upload widget, sheet picker, data preview
│   ├── controls_mapping.py Chart type selector + dynamic column mapping
│   ├── controls_style.py  Accordion of style controls
│   └── controls_export.py Export size / scale / format / filename
└── callbacks/             Thin Dash callbacks (data, plot, export)
tests/                     pytest suite + fixture data files
```

## Design decisions

### 2026-07-11 — Framework: Dash + Plotly + dash-bootstrap-components
Dash keeps everything in Python (the target user is a scientist, not a web dev), Plotly gives interactive + kaleido static export from the same figure object, and dash-bootstrap-components provides accordions/tabs/alerts without hand-written CSS. Alternatives considered: Streamlit (reruns whole script per interaction — poor fit for a many-control live playground), Panel/Bokeh (weaker static-export story).

### 2026-07-11 — Plot registry pattern
Each chart type is one module defining a `BasePlot` subclass registered via the `@register_plot` decorator. Chart dropdown, mapping UI, and options UI are generated from the registry, so a new chart type = one new file + one import. This is the project's primary extension point.

### 2026-07-11 — StyleModel as single source of truth
All style options live as fields on one dataclass (`styling/style_model.py`), with defaults sourced from `config.py`. One `apply_style(fig, style)` function applies them to any figure, so styling is uniform across chart types and adding an option touches a known, small set of places.

### 2026-07-11 — Style controls are authoritative, except "auto"-less colors
Style controls apply exactly what they show (a gridline toggle wins over the template). The exception: background and gridline *colors* only apply when moved off the PlotForge default, because an `<input type=color>` cannot express "automatic" — otherwise picking a template like `seaborn` would instantly lose its signature background to our default white. Trade-off: re-picking exactly the default color is not treated as an override.

### 2026-07-11 — Palette recoloring happens post-build
plotly.express bakes concrete colors into traces, so `layout.colorway` alone cannot re-palette a built figure. `apply_style` therefore reassigns trace colors from the chosen palette (by legend-group first-appearance order), which is also where per-group manual overrides hook in. Plot modules stay color-agnostic.

### 2026-07-11 — App factory pattern
`create_app()` builds the app rather than a module-level singleton, so tests can construct isolated instances and `run.py` stays trivial.

## Known limitations / future ideas

- SVG/PDF export (kaleido supports it; only PNG/JPG exposed initially)
- Figure "recipes" (save/load a mapping+style configuration)
- Multi-panel figure composition

## Deviations from the original plan

*(none yet)*
