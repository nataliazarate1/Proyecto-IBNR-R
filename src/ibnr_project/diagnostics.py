from __future__ import annotations

import numpy as np
import pandas as pd


def build_link_ratio_count_table(observed_mask: np.ndarray) -> pd.DataFrame:
    counts = []
    n_periods = observed_mask.shape[1]
    for period in range(n_periods - 1):
        valid_pairs = observed_mask[:, period] & observed_mask[:, period + 1]
        counts.append(
            {
                "development_period": period + 1,
                "n_individual_ratios": int(valid_pairs.sum()),
            }
        )
    return pd.DataFrame(counts)


def compute_running_statistics(results_df: pd.DataFrame, scenario: str, method: str) -> pd.DataFrame:
    subset = (
        results_df.loc[(results_df["scenario"] == scenario) & (results_df["method"] == method)]
        .sort_values("replica")
        .reset_index(drop=True)
    )
    errors = subset["estimated_ibnr"].to_numpy() - subset["true_ibnr"].to_numpy()
    abs_pct_errors = np.abs(errors / subset["true_ibnr"].to_numpy())
    replicas = np.arange(1, len(subset) + 1)

    cumulative_squared_error = np.cumsum(np.square(errors))
    cumulative_bias = np.cumsum(errors)
    cumulative_mape = np.cumsum(abs_pct_errors)

    out = subset.loc[:, ["scenario", "method", "replica"]].copy()
    out["running_bias"] = cumulative_bias / replicas
    out["running_rmse"] = np.sqrt(cumulative_squared_error / replicas)
    out["running_mape"] = cumulative_mape / replicas
    return out


def summarize_method_dominance(ranking_df: pd.DataFrame) -> pd.DataFrame:
    winners = ranking_df.loc[ranking_df["rank"] == 1]
    return (
        winners.groupby("method", as_index=False)
        .agg(n_scenarios_won=("scenario", "count"))
        .sort_values("n_scenarios_won", ascending=False)
        .reset_index(drop=True)
    )
