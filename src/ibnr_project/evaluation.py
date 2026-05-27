from __future__ import annotations

import numpy as np
import pandas as pd

SCENARIO_METADATA_COLUMNS = (
    "contamination_proportion",
    "contamination_magnitude",
    "contamination_location",
)

METHOD_LABELS = {
    "classical": "Clásico",
    "median": "Mediana",
    "trimmed": "Media truncada",
    "weighted": "Ponderado robusto",
}


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
        for column in SCENARIO_METADATA_COLUMNS:
            if column in group.columns:
                row[column] = group[column].iloc[0]
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


def summarize_family_results(
    metrics_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    method_labels: dict[str, str] | None = None,
) -> pd.DataFrame:
    labels = METHOD_LABELS if method_labels is None else method_labels
    family_specs = [
        (
            "Sin contaminación",
            metrics_df["scenario"].eq("base_sin_contaminacion"),
            ranking_df["scenario"].eq("base_sin_contaminacion"),
        ),
        (
            "Contaminación del 5%",
            metrics_df["contamination_proportion"].eq(0.05),
            ranking_df["contamination_proportion"].eq(0.05),
        ),
        (
            "Contaminación del 10%",
            metrics_df["contamination_proportion"].eq(0.10),
            ranking_df["contamination_proportion"].eq(0.10),
        ),
        (
            "Contaminación del 20%",
            metrics_df["contamination_proportion"].eq(0.20),
            ranking_df["contamination_proportion"].eq(0.20),
        ),
        (
            "Outliers ×2",
            metrics_df["contamination_magnitude"].eq(2.0),
            ranking_df["contamination_magnitude"].eq(2.0),
        ),
        (
            "Outliers ×5",
            metrics_df["contamination_magnitude"].eq(5.0),
            ranking_df["contamination_magnitude"].eq(5.0),
        ),
        (
            "Outliers ×10",
            metrics_df["contamination_magnitude"].eq(10.0),
            ranking_df["contamination_magnitude"].eq(10.0),
        ),
        (
            "Contaminación temprana",
            metrics_df["contamination_location"].eq("early"),
            ranking_df["contamination_location"].eq("early"),
        ),
        (
            "Contaminación tardía",
            metrics_df["contamination_location"].eq("late"),
            ranking_df["contamination_location"].eq("late"),
        ),
        (
            "Contaminación aleatoria",
            metrics_df["contamination_location"].eq("random"),
            ranking_df["contamination_location"].eq("random"),
        ),
    ]

    rows = []
    for family_label, metric_filter, ranking_filter in family_specs:
        metric_summary = (
            metrics_df.loc[metric_filter]
            .groupby("method", as_index=False)[["rmse", "mape", "sd_estimates"]]
            .mean()
            .sort_values("rmse", ascending=True)
        )
        ranking_summary = (
            ranking_df.loc[ranking_filter & ranking_df["rank"].eq(1)]
            .groupby("method")
            .size()
            .sort_values(ascending=False)
        )

        best_mean = metric_summary.iloc[0]
        top_wins_method = ranking_summary.index[0]
        top_wins_count = int(ranking_summary.iloc[0])
        total_scenarios = int(ranking_summary.sum())

        rows.append(
            {
                "familia": family_label,
                "best_mean_method_code": best_mean["method"],
                "metodo_mejor_promedio": labels[best_mean["method"]],
                "rmse_promedio": round(float(best_mean["rmse"]), 2),
                "mape_promedio": round(float(best_mean["mape"]), 3),
                "sd_promedio": round(float(best_mean["sd_estimates"]), 2),
                "top_wins_method_code": top_wins_method,
                "metodo_con_mas_victorias": labels[top_wins_method],
                "victorias_escenario": top_wins_count,
                "total_escenarios": total_scenarios,
                "victorias_dentro_de_la_familia": f"{top_wins_count}/{total_scenarios}",
            }
        )

    return pd.DataFrame(rows)


def assess_primary_hypothesis(
    metrics_df: pd.DataFrame,
    family_results_df: pd.DataFrame,
    method_labels: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    labels = METHOD_LABELS if method_labels is None else method_labels
    classical_metrics = metrics_df.query("scenario != 'base_sin_contaminacion' and method == 'classical'").copy()
    classical_metrics["log_magnitude"] = np.log(classical_metrics["contamination_magnitude"])
    correlation_table = classical_metrics[
        ["contamination_proportion", "contamination_magnitude", "log_magnitude", "rmse", "mape", "sd_estimates"]
    ].corr(method="spearman")

    support_sd = (
        metrics_df.query("scenario != 'base_sin_contaminacion'")
        .pivot(index="scenario", columns="method", values="sd_estimates")
        .assign(
            median_less_than_classical=lambda df: df["median"] < df["classical"],
            trimmed_less_than_classical=lambda df: df["trimmed"] < df["classical"],
            weighted_less_than_classical=lambda df: df["weighted"] < df["classical"],
        )
    )

    robust_sd_summary = pd.DataFrame(
        {
            "metodo_robusto": ["median", "trimmed", "weighted"],
            "escenarios_con_menor_sd_que_clasico": [
                int(support_sd["median_less_than_classical"].sum()),
                int(support_sd["trimmed_less_than_classical"].sum()),
                int(support_sd["weighted_less_than_classical"].sum()),
            ],
        }
    )
    robust_sd_summary["total_escenarios_contaminados"] = len(support_sd)
    robust_sd_summary["proporcion_favorable"] = (
        robust_sd_summary["escenarios_con_menor_sd_que_clasico"] / robust_sd_summary["total_escenarios_contaminados"]
    )
    robust_sd_summary["metodo_robusto_label"] = robust_sd_summary["metodo_robusto"].map(labels)

    best_stability_row = robust_sd_summary.sort_values(
        "escenarios_con_menor_sd_que_clasico",
        ascending=False,
    ).iloc[0]
    contaminated_families = family_results_df.query("familia != 'Sin contaminación'")
    family_leader_counts = (
        contaminated_families.groupby("best_mean_method_code").size().sort_values(ascending=False)
    )
    leading_family_method = family_leader_counts.index[0]
    leading_family_count = int(family_leader_counts.iloc[0])

    hypothesis_table = pd.DataFrame(
        [
            {
                "hipotesis": "H1",
                "evidencia_principal": (
                    f"Correlación de Spearman del RMSE clásico con proporción = "
                    f"{correlation_table.loc['contamination_proportion', 'rmse']:.3f}, "
                    f"con magnitud = {correlation_table.loc['contamination_magnitude', 'rmse']:.3f}. "
                    f"En la lectura por familias, {labels[leading_family_method]} lidera "
                    f"{leading_family_count} de {len(contaminated_families)} familias contaminadas según RMSE promedio. "
                    f"En variabilidad, el método robusto con mejor resultado es "
                    f"{best_stability_row['metodo_robusto_label']}, que mejora al clásico en "
                    f"{int(best_stability_row['escenarios_con_menor_sd_que_clasico'])} de {len(support_sd)} escenarios contaminados."
                ),
                "dictamen": (
                    "Apoyada"
                    if (
                        correlation_table.loc["contamination_proportion", "rmse"] > 0
                        and correlation_table.loc["contamination_magnitude", "rmse"] > 0
                        and leading_family_method != "classical"
                        and int(best_stability_row["escenarios_con_menor_sd_que_clasico"]) >= len(support_sd) / 2
                    )
                    else "Parcialmente apoyada"
                ),
            }
        ]
    )
    return correlation_table, robust_sd_summary, hypothesis_table
