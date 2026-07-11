"""Shared pytest fixtures: paths to sample data files and loaded frames."""

from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    """The canonical sample dataset used across plot/style tests."""
    df = pd.read_csv(FIXTURES / "sample.csv")
    df["measured_on"] = pd.to_datetime(df["measured_on"])
    return df


def as_upload_payload(path: Path) -> str:
    """Encode a file the way ``dcc.Upload`` delivers it to callbacks."""
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:application/octet-stream;base64,{b64}"


@pytest.fixture()
def fixtures_dir() -> Path:
    return FIXTURES
