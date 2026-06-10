from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import product
from typing import Literal

import numpy as np

NombreDistribucion = Literal["gamma", "lognormal"]
NombreUbicacion = Literal["ninguna", "aleatoria", "temprana", "tardia"]


@dataclass(frozen=True)
class ConfiguracionSimulacion:
    n_periodos: int
    desarrollo_acumulado: np.ndarray
    medias_ultimas: np.ndarray
    dispersion_phi: float
    semilla_aleatoria: int
    distribucion: NombreDistribucion = "gamma"
    fraccion_recorte_contaminacion: float = 0.10
    umbral_pesos: float = 1.5
    epsilon: float = 1e-8

    @property
    def desarrollo_incremental(self) -> np.ndarray:
        acumulado = self.desarrollo_acumulado
        incremental = np.diff(np.concatenate(([0.0], acumulado)))
        if not np.isclose(incremental.sum(), 1.0):
            raise ValueError("Las proporciones incrementales deben sumar 1.")
        return incremental


@dataclass(frozen=True)
class EscenarioContaminacion:
    nombre: str
    proporcion: float
    magnitud: float
    ubicacion: NombreUbicacion

    def es_limpio(self) -> bool:
        return self.proporcion == 0.0 or self.magnitud == 1.0 or self.ubicacion == "ninguna"


def construir_configuracion_base(
    semilla_aleatoria: int = 20260429,
    distribucion: NombreDistribucion = "gamma",
) -> ConfiguracionSimulacion:
    patron_acumulado = np.array([0.45, 0.70, 0.82, 0.90, 0.95, 0.97, 0.985, 0.993, 0.998, 1.00], dtype=float)
    if not np.all(np.diff(patron_acumulado) > 0):
        raise ValueError("El patron acumulado debe ser estrictamente creciente.")

    # Tendencia suave por ano de ocurrencia para introducir heterogeneidad
    # sin romper la comparabilidad entre escenarios.
    base_ultimos = 1200.0
    crecimiento = 0.035
    indices = np.arange(patron_acumulado.size)
    medias_ultimas = base_ultimos * np.exp(crecimiento * (indices - indices.mean()))

    return ConfiguracionSimulacion(
        n_periodos=10,
        desarrollo_acumulado=patron_acumulado,
        medias_ultimas=medias_ultimas,
        dispersion_phi=0.30,
        semilla_aleatoria=semilla_aleatoria,
        distribucion=distribucion,
        fraccion_recorte_contaminacion=0.10,
        umbral_pesos=1.5,
        epsilon=1e-8,
    )


def construir_escenarios_base() -> list[EscenarioContaminacion]:
    limpio = [
        EscenarioContaminacion(
            nombre="base_sin_contaminacion",
            proporcion=0.0,
            magnitud=1.0,
            ubicacion="ninguna",
        )
    ]
    contaminados = []
    proporciones = [0.05, 0.10, 0.20]
    magnitudes = [2.0, 5.0, 10.0]
    ubicaciones = ["aleatoria", "temprana", "tardia"]

    for proporcion, magnitud, ubicacion in product(proporciones, magnitudes, ubicaciones):
        contaminados.append(
            EscenarioContaminacion(
                nombre=f"p{int(proporcion * 100)}_m{int(magnitud)}_{ubicacion}",
                proporcion=proporcion,
                magnitud=magnitud,
                ubicacion=ubicacion,
            )
        )
    return limpio + contaminados


def clonar_configuracion(configuracion: ConfiguracionSimulacion, **cambios) -> ConfiguracionSimulacion:
    return replace(configuracion, **cambios)
