"""Server-side data cache.

Uploaded DataFrames never travel through the browser: callbacks store
them here under a random token and pass only the token through
``dcc.Store``. For a single-user local app a process-level dict is
sufficient (no Redis / disk cache needed); the cache is bounded so
repeated uploads in a long session don't grow memory without limit.

The raw uploaded bytes are cached alongside the parsed frame so that
switching Excel sheets re-parses locally instead of requiring a
re-upload.
"""

from __future__ import annotations

import uuid
from collections import OrderedDict
from dataclasses import dataclass, field

import pandas as pd

#: Keep at most this many datasets in memory (oldest evicted first).
MAX_ENTRIES = 8


@dataclass
class Dataset:
    """Everything cached about one uploaded file."""

    filename: str
    raw: bytes  # original file bytes (for Excel sheet switching)
    df: pd.DataFrame  # parsed frame for the active sheet
    sheets: list[str] | None  # sheet names (None for csv/tsv)
    active_sheet: str | None
    column_types: dict[str, str] = field(default_factory=dict)


# Insertion-ordered so eviction is FIFO (oldest upload dropped first).
_CACHE: OrderedDict[str, Dataset] = OrderedDict()


def put(dataset: Dataset) -> str:
    """Cache a dataset and return its access token."""
    token = uuid.uuid4().hex
    _CACHE[token] = dataset
    while len(_CACHE) > MAX_ENTRIES:
        _CACHE.popitem(last=False)
    return token


def get(token: str | None) -> Dataset | None:
    """Return the dataset for ``token``, or ``None`` if absent/evicted."""
    if not token:
        return None
    return _CACHE.get(token)


def update(token: str, dataset: Dataset) -> None:
    """Replace the dataset stored under an existing token (sheet switch)."""
    _CACHE[token] = dataset


def clear() -> None:
    """Empty the cache (used by tests)."""
    _CACHE.clear()
