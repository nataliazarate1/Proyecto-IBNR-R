from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.append(str(SRC))

from ibnr_project.config import build_default_config, build_default_scenarios  # noqa: E402
from ibnr_project.diagnostics import summarize_method_dominance  # noqa: E402
from ibnr_project.evaluation import (  # noqa: E402
    assess_primary_hypothesis,
    compare_methods_to_baseline,
    compute_method_metrics,
    rank_methods_within_scenario,
    summarize_family_results,
)
from ibnr_project.experiment import build_global_summary, run_experiment  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the IBNR simulation study and export CSV summaries.")
    parser.add_argument("--replicas", type=int, default=1000, help="Number of replicas per scenario.")
    parser.add_argument("--distribution", choices=["gamma", "lognormal"], default="gamma")
    parser.add_argument("--output-dir", default="results", help="Directory for exported CSV files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_default_config(distribution=args.distribution)
    scenarios = build_default_scenarios()
    results = run_experiment(config, scenarios, n_replicas=args.replicas)
    metrics = compute_method_metrics(results)
    ranking = rank_methods_within_scenario(metrics, metric="rmse")
    comparisons = compare_methods_to_baseline(results, baseline="classical")
    dominance = summarize_method_dominance(ranking)
    global_summary = build_global_summary(metrics)
    family_results = summarize_family_results(metrics, ranking)
    _, robust_sd_summary, hypothesis_table = assess_primary_hypothesis(metrics, family_results)

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = f"{args.distribution}_{args.replicas}rep"
    results.to_csv(output_dir / f"raw_results_{suffix}.csv", index=False)
    metrics.to_csv(output_dir / f"metrics_{suffix}.csv", index=False)
    ranking.to_csv(output_dir / f"ranking_{suffix}.csv", index=False)
    comparisons.to_csv(output_dir / f"comparisons_vs_classical_{suffix}.csv", index=False)
    dominance.to_csv(output_dir / f"method_dominance_{suffix}.csv", index=False)
    global_summary.to_csv(output_dir / f"global_summary_{suffix}.csv", index=False)
    family_results.to_csv(output_dir / f"family_results_{suffix}.csv", index=False)
    robust_sd_summary.to_csv(output_dir / f"robust_sd_summary_{suffix}.csv", index=False)
    hypothesis_table.to_csv(output_dir / f"hypothesis_assessment_{suffix}.csv", index=False)

    print(f"Results exported to {output_dir}")


if __name__ == "__main__":
    main()
