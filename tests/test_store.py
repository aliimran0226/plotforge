"""Tests for the server-side dataset cache."""

from __future__ import annotations

import pandas as pd
import pytest

from plotforge.data import store


@pytest.fixture(autouse=True)
def _fresh_cache():
    store.clear()
    yield
    store.clear()


def _dataset(name: str = "f.csv") -> store.Dataset:
    return store.Dataset(
        filename=name,
        raw=b"x",
        df=pd.DataFrame({"a": [1]}),
        sheets=None,
        active_sheet=None,
    )


def test_put_get_roundtrip():
    token = store.put(_dataset())
    got = store.get(token)
    assert got is not None
    assert got.filename == "f.csv"


def test_get_missing_returns_none():
    assert store.get("nope") is None
    assert store.get(None) is None


def test_update_replaces_in_place():
    token = store.put(_dataset("a.csv"))
    store.update(token, _dataset("b.csv"))
    assert store.get(token).filename == "b.csv"


def test_eviction_is_fifo():
    tokens = [store.put(_dataset(f"{i}.csv")) for i in range(store.MAX_ENTRIES + 2)]
    assert store.get(tokens[0]) is None  # oldest evicted
    assert store.get(tokens[-1]) is not None
