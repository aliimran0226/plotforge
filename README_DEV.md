# PlotForge — Developer Guide

> **Status:** stub — the full guide (codebase tour, callback map, extension recipes) lands in Phase 7.

## Dev setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
python run.py --debug   # Dash hot-reload + in-browser error overlay
```

## Testing

```bash
pytest
```

## Formatting / linting

```bash
black plotforge tests run.py
ruff check plotforge tests run.py
```

Design rationale lives in [tool_structure.md](tool_structure.md).
