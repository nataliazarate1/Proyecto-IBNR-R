from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .config import ContaminationScenario, SimulationConfig


@dataclass
class TriangleSimulation:
    incremental_full: np.ndarray
    cumulative_full: np.ndarray
    observed_incremental: np.ndarray
    observed_cumulative: np.ndarray
    observed_mask: np.ndarray
    true_ibnr: float
    contamination_metadata: dict[str, Any]


def observed_mask(n_periods: int) -> np.ndarray:
    i, j = np.indices((n_periods, n_periods))
    return (i + j) <= (n_periods - 1)


def generate_incremental_triangle(config: SimulationConfig, rng: np.random.Generator) -> np.ndarray:
    means = np.outer(config.ultimate_means, config.development_incremental)
    if config.distribution == "gamma":
        shape = 1.0 / config.dispersion_phi
        scale = config.dispersion_phi * means
        incremental = rng.gamma(shape=shape, scale=scale)
    elif config.distribution == "lognormal":
        sigma2 = np.log1p(config.dispersion_phi)
        sigma = np.sqrt(sigma2)
        mu_log = np.log(means) - 0.5 * sigma2
        incremental = rng.lognormal(mean=mu_log, sigma=sigma)
    else:
        raise ValueError(f"Distribucion no soportada: {config.distribution}")
    return incremental


def incremental_to_cumulative(incremental_triangle: np.ndarray) -> np.ndarray:
    return incremental_triangle.cumsum(axis=1)


def build_observed_triangle(triangle: np.ndarray, mask: np.ndarray) -> np.ndarray:
    observed = triangle.copy().astype(float)
    observed[~mask] = np.nan
    return observed


def true_ibnr(incremental_triangle: np.ndarray, mask: np.ndarray) -> float:
    return float(np.where(mask, 0.0, incremental_triangle).sum())


def _eligible_cells(mask: np.ndarray, location: str) -> np.ndarray:
    coords = np.argwhere(mask)
    if location == "random":
        return coords
    if location == "early":
        selected = []
        for row in range(mask.shape[0]):
            observed_cols = np.where(mask[row])[0]
            if observed_cols.size == 0:
                continue
            n_local = max(1, int(np.ceil(observed_cols.size / 3)))
            selected.extend((row, int(col)) for col in observed_cols[:n_local])
        return np.array(selected, dtype=int)
    if location == "late":
        selected = []
        for row in range(mask.shape[0]):
            observed_cols = np.where(mask[row])[0]
            if observed_cols.size == 0:
                continue
            n_local = max(1, int(np.ceil(observed_cols.size / 3)))
            selected.extend((row, int(col)) for col in observed_cols[-n_local:])
        return np.array(selected, dtype=int)
    if location == "none":
        return np.empty((0, 2), dtype=int)
    raise ValueError(f"Ubicacion no soportada: {location}")


def contaminate_incremental_triangle(
    incremental_triangle: np.ndarray,
    mask: np.ndarray,
    scenario: ContaminationScenario,
    rng: np.random.Generator,
) -> tuple[np.ndarray, dict[str, Any]]:
    contaminated = incremental_triangle.copy().astype(float)
    if scenario.is_clean():
        return contaminated, {"selected_cells": [], "n_selected": 0, "eligible_cells": 0}

    eligible = _eligible_cells(mask, scenario.location)
    if eligible.size == 0:
        return contaminated, {"selected_cells": [], "n_selected": 0, "eligible_cells": 0}

    n_select = int(np.round(scenario.proportion * len(eligible)))
    n_select = max(1, min(len(eligible), n_select))
    selected_idx = rng.choice(len(eligible), size=n_select, replace=False)
    selected_cells = eligible[selected_idx]

    for row, col in selected_cells:
        contaminated[row, col] *= scenario.magnitude

    metadata = {
        "selected_cells": [tuple(map(int, cell)) for cell in selected_cells],
        "n_selected": int(n_select),
        "eligible_cells": int(len(eligible)),
    }
    return contaminated, metadata


def simulate_single_triangle(
    config: SimulationConfig,
    scenario: ContaminationScenario,
    rng: np.random.Generator,
) -> TriangleSimulation:
    mask = observed_mask(config.n_periods)
    incremental_full = generate_incremental_triangle(config, rng)
    cumulative_full = incremental_to_cumulative(incremental_full)
    ibnr_real = true_ibnr(incremental_full, mask)

    contaminated_incremental, metadata = contaminate_incremental_triangle(incremental_full, mask, scenario, rng)
    contaminated_cumulative = incremental_to_cumulative(contaminated_incremental)

    observed_incremental = build_observed_triangle(contaminated_incremental, mask)
    observed_cumulative = build_observed_triangle(contaminated_cumulative, mask)

    return TriangleSimulation(
        incremental_full=incremental_full,
        cumulative_full=cumulative_full,
        observed_incremental=observed_incremental,
        observed_cumulative=observed_cumulative,
        observed_mask=mask,
        true_ibnr=ibnr_real,
        contamination_metadata=metadata,
    )
