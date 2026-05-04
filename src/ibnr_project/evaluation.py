from __future__ import annotations

import numpy as np
import pandas as pd


def _metric_row(group: pd.DataFrame) -> pd.Series:
    errors = group["estimated_ibnr"] - group["true_ibnr"]
    abs_errors = np.abs(errors)
    pct_errors = errors / group["true_ibnr"]
    abs_pct_errors = np.abs(pct_errors)
    estimates = group["estimated_ibnr"]
    n = len(group)
    z_value = 1.96

    bias = errors.mean()
    mape = abs_pct_errors.mean()
    mae = abs_errors.mean()
    mcse_bias = errors.std(ddof=1) / np.sqrt(n)
    mcse_mape = abs_pct_errors.std(ddof=1) / np.sqrt(n)
    mcse_mae = abs_errors.std(ddof=1) / np.sqrt(n)

    return pd.Series(
        {
            "n_replicas": n,
            "bias": bias,
            "mse": np.mean(np.square(errors)),
            "rmse": np.sqrt(np.mean(np.square(errors))),
            "mae": mae,
            "mape": mape,
            "mean_percentage_error": pct_errors.mean(),
            "sd_estimates": estimates.std(ddof=1),
            "overestimation_rate": np.mean(errors > 0),
            "underestimation_rate": np.mean(errors < 0),
            "median_absolute_error": np.median(abs_errors),
            "mcse_bias": mcse_bias,
            "mcse_mape": mcse_mape,
            "mcse_mae": mcse_mae,
            "bias_ci_lower": bias - z_value * mcse_bias,
            "bias_ci_upper": bias + z_value * mcse_bias,
            "mape_ci_lower": max(0.0, mape - z_value * mcse_mape),
            "mape_ci_upper": mape + z_value * mcse_mape,
            "mae_ci_lower": max(0.0, mae - z_value * mcse_mae),
            "mae_ci_upper": mae + z_value * mcse_mae,
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


def compare_methods_to_baseline(
    results_df: pd.DataFrame,
    baseline: str = "classical",
) -> pd.DataFrame:
    baseline_df = (
        results_df.loc[results_df["method"] == baseline, ["scenario", "replica", "true_ibnr", "estimated_ibnr"]]
        .rename(columns={"estimated_ibnr": "baseline_estimated_ibnr"})
        .copy()
    )
    comparison_df = results_df.loc[results_df["method"] != baseline].merge(
        baseline_df,
        on=["scenario", "replica", "true_ibnr"],
        how="inner",
        validate="many_to_one",
    )
    method_errors = comparison_df["estimated_ibnr"] - comparison_df["true_ibnr"]
    baseline_errors = comparison_df["baseline_estimated_ibnr"] - comparison_df["true_ibnr"]

    comparison_df["delta_squared_error"] = np.square(method_errors) - np.square(baseline_errors)
    comparison_df["delta_absolute_error"] = np.abs(method_errors) - np.abs(baseline_errors)
    comparison_df["delta_absolute_percentage_error"] = np.abs(method_errors / comparison_df["true_ibnr"]) - np.abs(
        baseline_errors / comparison_df["true_ibnr"]
    )

    rows = []
    z_value = 1.96
    for (scenario, method), group in comparison_df.groupby(["scenario", "method"], sort=False):
        row = {"scenario": scenario, "method": method, "baseline": baseline, "n_replicas": len(group)}
        for source_col, prefix in [
            ("delta_squared_error", "delta_mse"),
            ("delta_absolute_error", "delta_mae"),
            ("delta_absolute_percentage_error", "delta_mape"),
        ]:
            values = group[source_col].to_numpy()
            mean_value = float(values.mean())
            se_value = float(values.std(ddof=1) / np.sqrt(len(values)))
            row[f"{prefix}_mean"] = mean_value
            row[f"{prefix}_se"] = se_value
            row[f"{prefix}_ci_lower"] = mean_value - z_value * se_value
            row[f"{prefix}_ci_upper"] = mean_value + z_value * se_value
            row[f"{prefix}_improves"] = bool(row[f"{prefix}_ci_upper"] < 0)
            row[f"{prefix}_worsens"] = bool(row[f"{prefix}_ci_lower"] > 0)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["scenario", "method"]).reset_index(drop=True)
