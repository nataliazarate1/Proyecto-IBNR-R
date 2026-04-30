from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ContaminationScenario, SimulationConfig
from .methods import estimate_ibnr_all_methods
from .simulation import (
    contaminate_incremental_triangle,
    generate_incremental_triangle,
    incremental_to_cumulative,
    observed_mask,
    true_ibnr,
)


def _deterministic_triangle(config: SimulationConfig) -> np.ndarray:
    return np.outer(config.ultimate_means, config.development_incremental)


def validate_incremental_mean_structure(config: SimulationConfig, n_draws: int = 3000) -> dict[str, float | bool]:
    rng = np.random.default_rng(config.random_seed)
    expected = np.outer(config.ultimate_means, config.development_incremental)
    draws = np.stack([generate_incremental_triangle(config, rng) for _ in range(n_draws)])
    sample_mean = draws.mean(axis=0)
    relative_error = np.abs(sample_mean - expected) / expected
    return {
        "passed": bool(relative_error.mean() < 0.05),
        "mean_relative_error": float(relative_error.mean()),
        "max_relative_error": float(relative_error.max()),
    }


def validate_cumulative_consistency(config: SimulationConfig) -> dict[str, float | bool]:
    rng = np.random.default_rng(config.random_seed)
    incremental = generate_incremental_triangle(config, rng)
    cumulative = incremental_to_cumulative(incremental)
    monotone = np.all(np.diff(cumulative, axis=1) >= 0)
    reconstruction_error = float(np.abs(cumulative[:, -1] - incremental.sum(axis=1)).max())
    return {
        "passed": bool(monotone and reconstruction_error < 1e-8),
        "monotone_rows": bool(monotone),
        "max_reconstruction_error": reconstruction_error,
    }


def validate_mask_and_ibnr_definition(config: SimulationConfig) -> dict[str, float | bool]:
    mask = observed_mask(config.n_periods)
    incremental = _deterministic_triangle(config)
    ibnr_from_mask = true_ibnr(incremental, mask)
    total = float(incremental.sum())
    observed_total = float(incremental[mask].sum())
    expected_observed_cells = config.n_periods * (config.n_periods + 1) / 2
    return {
        "passed": bool(np.isclose(ibnr_from_mask, total - observed_total) and mask.sum() == expected_observed_cells),
        "observed_cells": int(mask.sum()),
        "expected_observed_cells": int(expected_observed_cells),
        "ibnr_consistency_gap": float(abs(ibnr_from_mask - (total - observed_total))),
    }


def validate_contamination_logic(config: SimulationConfig) -> dict[str, float | bool]:
    rng = np.random.default_rng(config.random_seed)
    mask = observed_mask(config.n_periods)
    incremental = _deterministic_triangle(config)
    scenario = ContaminationScenario(name="prueba", proportion=0.10, magnitude=5.0, location="early")
    contaminated, metadata = contaminate_incremental_triangle(incremental, mask, scenario, rng)
    changed = np.argwhere(np.abs(contaminated - incremental) > 0)
    valid_positions = all(mask[row, col] for row, col in changed)
    multiplicative_ok = True
    for row, col in changed:
        if not np.isclose(contaminated[row, col], incremental[row, col] * scenario.magnitude):
            multiplicative_ok = False
            break
    return {
        "passed": bool(valid_positions and multiplicative_ok and len(changed) == metadata["n_selected"]),
        "n_changed": int(len(changed)),
        "n_selected": int(metadata["n_selected"]),
        "only_observed_cells_changed": bool(valid_positions),
    }


def validate_methods_on_noise_free_triangle(config: SimulationConfig) -> dict[str, float | bool]:
    mask = observed_mask(config.n_periods)
    incremental = _deterministic_triangle(config)
    cumulative = incremental_to_cumulative(incremental)
    observed_cumulative = cumulative.astype(float)
    observed_cumulative[~mask] = np.nan
    true_value = true_ibnr(incremental, mask)
    estimates = estimate_ibnr_all_methods(observed_cumulative, config)
    max_gap = max(abs(result.estimated_ibnr - true_value) for result in estimates.values())
    return {
        "passed": bool(max_gap < 1e-8),
        "max_estimation_gap": float(max_gap),
    }


def run_validation_suite(config: SimulationConfig) -> pd.DataFrame:
    checks = {
        "incremental_mean_structure": validate_incremental_mean_structure(config),
        "cumulative_consistency": validate_cumulative_consistency(config),
        "mask_and_ibnr_definition": validate_mask_and_ibnr_definition(config),
        "contamination_logic": validate_contamination_logic(config),
        "methods_on_noise_free_triangle": validate_methods_on_noise_free_triangle(config),
    }
    rows = []
    for name, result in checks.items():
        row = {"check": name}
        row.update(result)
        rows.append(row)
    return pd.DataFrame(rows)
