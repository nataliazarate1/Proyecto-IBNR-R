from __future__ import annotations

import numpy as np
import pandas as pd


def _metric_row(group: pd.DataFrame) -> pd.Series:
    errors = group["estimated_ibnr"] - group["true_ibnr"]
    pct_errors = errors / group["true_ibnr"]
    estimates = group["estimated_ibnr"]

    return pd.Series(
        {
            "n_replicas": len(group),
            "bias": errors.mean(),
            "mse": np.mean(np.square(errors)),
            "rmse": np.sqrt(np.mean(np.square(errors))),
            "mape": np.mean(np.abs(pct_errors)),
            "mean_percentage_error": pct_errors.mean(),
            "sd_estimates": estimates.std(ddof=1),
            "overestimation_rate": np.mean(errors > 0),
            "underestimation_rate": np.mean(errors < 0),
            "median_absolute_error": np.median(np.abs(errors)),
        }
    )


def compute_method_metrics(results_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = results_df.groupby(["scenario", "method"], sort=False)
    for (scenario, method), group in grouped:
        row = {"scenario": scenario, "method": method}
        row.update(_metric_row(group).to_dict())
        rows.append(row)
    summary = pd.DataFrame(rows)
    return summary.sort_values(["scenario", "method"]).reset_index(drop=True)


def summarize_results_by_scenario(metrics_df: pd.DataFrame, metric: str = "rmse") -> pd.DataFrame:
    pivot = metrics_df.pivot(index="scenario", columns="method", values=metric)
    return pivot.sort_index()


def rank_methods_within_scenario(metrics_df: pd.DataFrame, metric: str = "rmse") -> pd.DataFrame:
    ranked = metrics_df.copy()
    ranked["rank"] = ranked.groupby("scenario")[metric].rank(method="dense")
    return ranked.sort_values(["scenario", "rank", "method"]).reset_index(drop=True)
