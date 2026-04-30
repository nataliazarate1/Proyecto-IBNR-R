from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import product
from typing import Literal

import numpy as np

DistributionName = Literal["gamma", "lognormal"]
LocationName = Literal["none", "random", "early", "late"]


@dataclass(frozen=True)
class SimulationConfig:
    n_periods: int
    development_cumulative: np.ndarray
    ultimate_means: np.ndarray
    dispersion_phi: float
    random_seed: int
    distribution: DistributionName = "gamma"
    contamination_trim_fraction: float = 0.10
    weight_cutoff: float = 1.5
    epsilon: float = 1e-8

    @property
    def development_incremental(self) -> np.ndarray:
        cumulative = self.development_cumulative
        incremental = np.diff(np.concatenate(([0.0], cumulative)))
        if not np.isclose(incremental.sum(), 1.0):
            raise ValueError("Las proporciones incrementales deben sumar 1.")
        return incremental


@dataclass(frozen=True)
class ContaminationScenario:
    name: str
    proportion: float
    magnitude: float
    location: LocationName

    def is_clean(self) -> bool:
        return self.proportion == 0.0 or self.magnitude == 1.0 or self.location == "none"


def build_default_config(random_seed: int = 20260429, distribution: DistributionName = "gamma") -> SimulationConfig:
    cumulative_pattern = np.array([0.45, 0.70, 0.82, 0.90, 0.95, 0.97, 0.985, 0.993, 0.998, 1.00], dtype=float)
    if not np.all(np.diff(cumulative_pattern) > 0):
        raise ValueError("El patron acumulado debe ser estrictamente creciente.")

    # Tendencia suave por ano de ocurrencia: introduce heterogeneidad sin romper la comparabilidad.
    base_ultimate = 1200.0
    growth = 0.035
    idx = np.arange(cumulative_pattern.size)
    ultimate_means = base_ultimate * np.exp(growth * (idx - idx.mean()))

    return SimulationConfig(
        n_periods=10,
        development_cumulative=cumulative_pattern,
        ultimate_means=ultimate_means,
        dispersion_phi=0.30,
        random_seed=random_seed,
        distribution=distribution,
        contamination_trim_fraction=0.10,
        weight_cutoff=1.5,
        epsilon=1e-8,
    )


def build_default_scenarios() -> list[ContaminationScenario]:
    clean = [ContaminationScenario(name="base_sin_contaminacion", proportion=0.0, magnitude=1.0, location="none")]
    contaminated = []
    proportions = [0.05, 0.10, 0.20]
    magnitudes = [2.0, 5.0, 10.0]
    locations = ["random", "early", "late"]

    for proportion, magnitude, location in product(proportions, magnitudes, locations):
        contaminated.append(
            ContaminationScenario(
                name=f"p{int(proportion * 100)}_m{int(magnitude)}_{location}",
                proportion=proportion,
                magnitude=magnitude,
                location=location,
            )
        )
    return clean + contaminated


def clone_config(config: SimulationConfig, **changes) -> SimulationConfig:
    return replace(config, **changes)
