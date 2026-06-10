from __future__ import annotations

import numpy as np
import pandas as pd

from .configuracion import ConfiguracionSimulacion, EscenarioContaminacion
from .metodos import estimar_ibnr_todos_metodos
from .simulacion import simular_un_triangulo


def ejecutar_experimento(
    configuracion: ConfiguracionSimulacion,
    escenarios: list[EscenarioContaminacion],
    n_replicas: int = 1000,
) -> pd.DataFrame:
    generador_maestro = np.random.default_rng(configuracion.semilla_aleatoria)
    filas = []

    for escenario in escenarios:
        for replica in range(1, n_replicas + 1):
            generador_replica = np.random.default_rng(generador_maestro.integers(0, 2**32 - 1))
            triangulo = simular_un_triangulo(configuracion, escenario, generador_replica)
            estimaciones = estimar_ibnr_todos_metodos(triangulo.acumulado_observado, configuracion)
            for nombre_metodo, resultado in estimaciones.items():
                filas.append(
                    {
                        "escenario": escenario.nombre,
                        "replica": replica,
                        "metodo": nombre_metodo,
                        "ibnr_real": triangulo.ibnr_real,
                        "ibnr_estimado": resultado.ibnr_estimado,
                        "proporcion_contaminacion": escenario.proporcion,
                        "magnitud_contaminacion": escenario.magnitud,
                        "ubicacion_contaminacion": escenario.ubicacion,
                    }
                )

    return pd.DataFrame(filas)


def construir_resumen_global(metricas_df: pd.DataFrame) -> pd.DataFrame:
    return (
        metricas_df.groupby("metodo", as_index=False)
        .agg(
            rmse_promedio=("rmse", "mean"),
            mape_promedio=("mape", "mean"),
            sesgo_absoluto_promedio=("sesgo", lambda serie: np.mean(np.abs(serie))),
            desviacion_estandar_promedio=("desviacion_estandar_estimaciones", "mean"),
        )
        .sort_values("rmse_promedio")
        .reset_index(drop=True)
    )
