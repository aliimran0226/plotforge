"""Regenerate the binary/text fixture files used by the test suite.

Run from the repo root: ``python tests/fixtures/make_fixtures.py``.
Text fixtures are also committed so tests don't depend on this script.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
RNG = np.random.default_rng(42)


def sample_frame(n: int = 40) -> pd.DataFrame:
    """Small tidy frame with numeric, categorical, and datetime columns."""
    return pd.DataFrame(
        {
            "dose": RNG.uniform(0.1, 10.0, n).round(3),
            "response": RNG.normal(50, 12, n).round(2),
            "response_err": RNG.uniform(1, 5, n).round(2),
            "group": RNG.choice(["control", "treated", "placebo"], n),
            "batch": RNG.choice(["A", "B"], n),
            "measured_on": pd.date_range("2025-01-01", periods=n, freq="D").astype(str),
        }
    )


def main() -> None:
    df = sample_frame()
    df.to_csv(HERE / "sample.csv", index=False)
    df.to_csv(HERE / "sample.tsv", sep="\t", index=False)

    # Multi-sheet workbook: main data + a wide matrix (heatmap-style).
    wide = pd.DataFrame(
        RNG.normal(0, 1, (6, 4)).round(3),
        columns=["c1", "c2", "c3", "c4"],
    )
    wide.insert(0, "row_label", [f"gene_{i}" for i in range(6)])
    with pd.ExcelWriter(HERE / "sample.xlsx") as writer:
        df.to_excel(writer, sheet_name="measurements", index=False)
        wide.to_excel(writer, sheet_name="matrix", index=False)

    # Deliberately broken fixtures.
    (HERE / "malformed.csv").write_bytes(b"\x00\x01\x02\xff\xfenot,a,valid\nfile")
    (HERE / "empty.csv").write_text("col_a,col_b\n", encoding="utf-8")
    print("fixtures written to", HERE)


if __name__ == "__main__":
    main()
