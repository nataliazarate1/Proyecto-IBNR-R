from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import SimulationConfig


@dataclass
class MethodEstimate:
    method: str
    factors: np.ndarray
    projected_cumulative: np.ndarray
    estimated_ibnr: float


def _individual_link_ratios(observed_cumulative: np.ndarray, period: int) -> np.ndarray:
    current_col = observed_cumulative[:, period]
    next_col = observed_cumulative[:, period + 1]
    valid = (~np.isnan(current_col)) & (~np.isnan(next_col)) & (current_col > 0)
    return next_col[valid] / current_col[valid]


def _classical_factor(observed_cumulative: np.ndarray, period: int) -> float:
    current_col = observed_cumulative[:, period]
    next_col = observed_cumulative[:, period + 1]
    valid = (~np.isnan(current_col)) & (~np.isnan(next_col)) & (current_col > 0)
    if not np.any(valid):
        return 1.0
    return float(next_col[valid].sum() / current_col[valid].sum())


def _trimmed_mean(values: np.ndarray, trim_fraction: float) -> float:
    if values.size == 0:
        return 1.0
    sorted_values = np.sort(values)
    k = int(np.floor(trim_fraction * sorted_values.size))
    if 2 * k >= sorted_values.size:
        return float(sorted_values.mean())
    trimmed = sorted_values[k : sorted_values.size - k]
    return float(trimmed.mean())


def _weighted_robust_factor(values: np.ndarray, cutoff: float, epsilon: float) -> float:
    if values.size == 0:
        return 1.0
    center = float(np.median(values))
    mad = float(np.median(np.abs(values - center)))
    scale = 1.4826 * mad + epsilon
    standardized = np.abs(values - center) / scale
    weights = np.minimum(1.0, cutoff / (standardized + epsilon))
    return float((weights * values).sum() / weights.sum())


def estimate_development_factors(observed_cumulative: np.ndarray, config: SimulationConfig) -> dict[str, np.ndarray]:
    n_periods = observed_cumulative.shape[1]
    classical = np.ones(n_periods - 1)
    median = np.ones(n_periods - 1)
    trimmed = np.ones(n_periods - 1)
    weighted = np.ones(n_periods - 1)

    for period in range(n_periods - 1):
        ratios = _individual_link_ratios(observed_cumulative, period)
        classical[period] = _classical_factor(observed_cumulative, period)
        median[period] = float(np.median(ratios)) if ratios.size else 1.0
        trimmed[period] = _trimmed_mean(ratios, config.contamination_trim_fraction)
        weighted[period] = _weighted_robust_factor(ratios, config.weight_cutoff, config.epsilon)

    return {
        "classical": classical,
        "median": median,
        "trimmed": trimmed,
        "weighted": weighted,
    }


def project_cumulative_triangle(observed_cumulative: np.ndarray, factors: np.ndarray) -> np.ndarray:
    projected = observed_cumulative.copy().astype(float)
    n_rows, n_cols = projected.shape

    for row in range(n_rows):
        observed_positions = np.where(~np.isnan(projected[row]))[0]
        if observed_positions.size == 0:
            continue
        last_observed = int(observed_positions.max())
        for period in range(last_observed, n_cols - 1):
            base_value = projected[row, period]
            if np.isnan(base_value):
                break
            projected[row, period + 1] = base_value * factors[period]
    return projected


def estimate_ibnr_from_projection(observed_cumulative: np.ndarray, projected_cumulative: np.ndarray) -> float:
    ibnr = 0.0
    for row in range(observed_cumulative.shape[0]):
        observed_positions = np.where(~np.isnan(observed_cumulative[row]))[0]
        if observed_positions.size == 0:
            continue
        last_observed = int(observed_positions.max())
        observed_latest = observed_cumulative[row, last_observed]
        ultimate = projected_cumulative[row, -1]
        ibnr += float(ultimate - observed_latest)
    return ibnr


def estimate_ibnr_all_methods(observed_cumulative: np.ndarray, config: SimulationConfig) -> dict[str, MethodEstimate]:
    factor_map = estimate_development_factors(observed_cumulative, config)
    estimates: dict[str, MethodEstimate] = {}
    for method_name, factors in factor_map.items():
        projected = project_cumulative_triangle(observed_cumulative, factors)
        ibnr_estimate = estimate_ibnr_from_projection(observed_cumulative, projected)
        estimates[method_name] = MethodEstimate(
            method=method_name,
            factors=factors,
            projected_cumulative=projected,
            estimated_ibnr=ibnr_estimate,
        )
    return estimates
