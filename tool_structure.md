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

### 2026-07-11 — Server-side data cache keyed by token
Uploaded DataFrames live in an in-process dict (`data/store.py`); the browser only holds a random token in a `dcc.Store`. Rationale: round-tripping data through the client (the common Dash JSON-in-Store pattern) is slow and memory-hungry for real datasets and pointless for a single-user local app. The cache is FIFO-bounded (8 entries) and also keeps the raw upload bytes so Excel sheet switches re-parse without re-uploading. Trade-off: state is lost on server restart — acceptable locally, would need Redis/disk if this ever became multi-user.

### 2026-07-11 — Pattern-matching component ids for all generated controls
Mapping dropdowns (`{"type":"mapping","name":…}`), chart options (`plot-opt`), style controls (`{"type":"style","field":…}` — field = StyleModel field name), and group color pickers (`group-color`) all use dict ids. One render callback reads them all with `ALL` matchers regardless of which chart type generated them; the style ids double as the link between UI and dataclass. This is what lets the UI be *generated* from declarations instead of hand-wired.

### 2026-07-11 — Export rebuilds the figure server-side (kaleido)
Export does not screenshot the on-screen graph: it reruns the same `build_figure` path with the same control values and renders via kaleido at the requested width/height/scale. Guarantees pixel-exact sizing independent of the browser window. kaleido v1 requires a Chromium browser on the machine; the modebar camera icon remains as a dependency-free fallback and the failure alert points at the README troubleshooting entry.

### 2026-07-11 — Heatmap declares no required mappings
Long data needs x+y, wide-matrix mode needs neither, and the registry's `required_mappings` is static — so heatmap declares everything optional and overrides `validate(mapping, column_types, options)` (options were added to the signature for exactly this). Precedent for future mode-dependent charts.

### 2026-07-11 — run.py scans for a free port
Deviation from the plan's fixed 8050: this machine (and many dev machines) already had 8050 occupied, so the default is now "first free port from 8050 upward" with `--port` as an explicit override that fails loudly instead.

### 2026-07-15 — Overlay layers reuse the plot registry, not a new abstraction
An overlay layer is just another registered plot (restricted to the cartesian set in `plots/overlay.py:OVERLAYABLE`) built with default options and its traces appended to the base figure — optionally on a right-hand `yaxis2`. This reuses `validate()`/`build()` untouched; the merge only names nameless traces (after the layer's y column) and tags each trace with `meta={"plotforge_layer": n}` so `apply_style`'s recoloring gives every layer its own palette slots (all px figures start at the same first color). Facets + layers are refused: there is no single target axis. Layer errors are re-raised prefixed with "Layer N:" so the shared error alert stays unambiguous. The card UI follows the decorations dynamic-entry pattern with one twist: rebuilding cards recreates components that are Inputs of the managing callback itself, so `layers-store` also carries a structure fingerprint that turns the rebuild echo into a PreventUpdate instead of a loop.

### 2026-07-15 — Decorations as dynamic entry lists on StyleModel
Reference lines, shaded bands, and text annotations are variable-length, which single pattern-id controls can't express. The design generalizes the group-color-picker precedent: a `dcc.Store` (`decor-store`) tracks entry ids per kind, a manage callback adds/removes entry cards (preserving typed values by reading all current pattern States), and every card input carries `{"type": "decor-<kind>", "idx": …, "prop": …}`. StyleModel holds the results as list-of-dict fields (`ref_lines`/`ref_bands`/`annotations`) filled via a `decorations` argument to `from_values` — never from the scalar `values` dict. `apply_style` re-adds them on every pass, which is safe because it always receives a freshly built figure. Coordinates are text inputs coerced number-first so datetime/categorical axis positions work.

### 2026-07-15 — Outer figure border as a paper-coordinate shape
Plotly has no "canvas border" property, and paper coordinates (0..1) span only the plot region. The outer border is therefore a rect shape extended past the paper domain by `margin / plot-size` — which requires a concrete figure size, so the export callback now bakes the export width/height into the StyleModel before building (rendered output is identical; kaleido's size args agree with the layout). Auto-sized figures fall back to framing the plot region. Tick-mark style is a dropdown whose empty value means "leave the template alone" — the same "auto"-capable-control reasoning as the background colors.

### 2026-07-15 — Upload contents are cleared after ingest; sheet switches read the cache
`dcc.Upload` only fires when its contents *change*, so uploading the same file twice was a silent no-op. The upload callback now also outputs `data-upload.contents = None` (its own input — Dash allows the self-loop; the echo is absorbed by the existing empty-contents guard). Consequence: the sheet-switch callback can no longer read the upload contents, so it re-parses from `Dataset.raw` in the server-side cache instead — which is why the raw bytes were cached in the first place. One-sided axis ranges are now honored too, via plotly's `autorange: "min"/"max"` partial modes; apply_style leaves `autorange` untouched when the user expressed no opinion (px.imshow's reversed y axis depends on that).

### 2026-07-15 — Plots pre-aggregate what px won't
`px.pie` never merges duplicate category rows (duplicate slices, and per-slice colors misalign once plotly.js merges labels client-side), so the pie plot aggregates to one row per category before building — sum for a mapped values column, row counts otherwise. Derived count columns (pie, bar) use an internal `__plotforge_count__` name displayed as "count" via `labels=`, so datasets with a real `count`/`size` column can't collide. `config.MAX_CATEGORIES` (previously unused) now caps pie slices with a friendly PlotError, and the density plot's `validate` refuses filled contours combined with color grouping (px forbids it; the fills would hide each other).

### 2026-07-15 — Palette slots keyed by px-assigned color, not trace name
Recoloring by trace name turned *any* multi-trace grouping into color groups — a symbol-only scatter (all traces deliberately the same color, distinguished by marker shape) came out rainbow-colored. Palette slots are now keyed by the color px originally assigned, so traces px colored alike stay alike, while color-grouped traces still fan out across the palette. Manual per-group overrides remain keyed by trace name (that is what the pickers show). Same pass: transparent line colors are never overwritten (px hides strip-plot box skeletons with them), and axis-title overrides now rename every titled facet axis instead of only the first.

### 2026-07-15 — Loader sniffs delimiters from a whitelist
`pd.read_csv(sep=None)` sniffs over *any* character and corrupted single-column files (it happily picked a letter from the header as the delimiter). The loader now sniffs with `csv.Sniffer` restricted to `, ; \t |` and falls back to a comma, which is harmless for single-column files. Trade-off: exotic delimiters (spaces, `:`) are no longer auto-detected — none were reliably detected before either.

## Extension recipes

Step-by-step guides (new chart type, new style option, new file format) live in [README_DEV.md](README_DEV.md#extension-guides), along with the callback map. This file only records why the seams are where they are.

## Known limitations / future ideas

- Background/gridline color pickers can't express "auto", so re-picking the exact default color is not treated as an override (see the style-controls decision above)
- Figure "recipes" (save/load a mapping+style configuration)
- Multi-panel figure composition
- Per-facet axis overrides (controls currently apply to all subplot axes)
