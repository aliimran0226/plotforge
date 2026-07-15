"""Built-in demo dataset, loadable with one click from the Data section.

A small dose-response experiment with the same column shapes as the
test fixtures: numeric (dose, response, response_err), categorical
(group, batch), and datetime (measured_on) - enough to try every chart
type without hunting for a file.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SAMPLE_FILENAME = "example_dose_response (built-in)"


def sample_dataframe() -> pd.DataFrame:
    """A deterministic ~60-row demo frame."""
    rng = np.random.default_rng(2026)
    doses = np.tile([0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500], 6)
    groups = np.repeat(["control", "treated", "combo"], 20)
    batches = np.tile(np.repeat(["batch A", "batch B"], 10), 3)
    effect = {"control": 1.0, "treated": 1.8, "combo": 2.6}
    response = np.array(
        [
            100 * e * d / (d + 30) + rng.normal(0, 4)
            for d, e in zip(doses, (effect[g] for g in groups), strict=True)
        ]
    )
    dates = pd.date_range("2026-01-05", periods=60, freq="D")
    return pd.DataFrame(
        {
            "dose": doses.astype(float),
            "response": response.round(2),
            "response_err": rng.uniform(2, 9, 60).round(2),
            "group": groups,
            "batch": batches,
            "measured_on": dates.strftime("%Y-%m-%d"),
        }
    )
