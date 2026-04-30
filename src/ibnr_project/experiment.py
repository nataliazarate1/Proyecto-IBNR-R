from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ContaminationScenario, SimulationConfig
from .methods import estimate_ibnr_all_methods
from .simulation import simulate_single_triangle


def run_experiment(
    config: SimulationConfig,
    scenarios: list[ContaminationScenario],
    n_replicas: int = 1000,
) -> pd.DataFrame:
    master_rng = np.random.default_rng(config.random_seed)
    rows = []

    for scenario in scenarios:
        for replica in range(1, n_replicas + 1):
            replica_rng = np.random.default_rng(master_rng.integers(0, 2**32 - 1))
            triangle = simulate_single_triangle(config, scenario, replica_rng)
            estimates = estimate_ibnr_all_methods(triangle.observed_cumulative, config)
            for method_name, result in estimates.items():
                rows.append(
                    {
                        "scenario": scenario.name,
                        "replica": replica,
                        "method": method_name,
                        "true_ibnr": triangle.true_ibnr,
                        "estimated_ibnr": result.estimated_ibnr,
                        "contamination_proportion": scenario.proportion,
                        "contamination_magnitude": scenario.magnitude,
                        "contamination_location": scenario.location,
                    }
                )

    return pd.DataFrame(rows)


def build_global_summary(metrics_df: pd.DataFrame) -> pd.DataFrame:
    return (
        metrics_df.groupby("method", as_index=False)
        .agg(
            mean_rmse=("rmse", "mean"),
            mean_mape=("mape", "mean"),
            mean_abs_bias=("bias", lambda s: np.mean(np.abs(s))),
            mean_sd=("sd_estimates", "mean"),
        )
        .sort_values("mean_rmse")
        .reset_index(drop=True)
    )
