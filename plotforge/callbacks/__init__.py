"""Dash callbacks, grouped by concern (data, plot, export).

Each module exposes ``register_callbacks(app)``; ``app.py`` calls them
all. Callbacks stay thin - real logic lives in importable functions in
``data/``, ``plots/``, and ``styling/`` so it can be unit-tested.
"""
