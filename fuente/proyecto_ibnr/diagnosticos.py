from __future__ import annotations

import numpy as np
import pandas as pd


def construir_tabla_conteo_ratios(mascara_observada: np.ndarray) -> pd.DataFrame:
    conteos = []
    n_periodos = mascara_observada.shape[1]
    for periodo in range(n_periodos - 1):
        pares_validos = mascara_observada[:, periodo] & mascara_observada[:, periodo + 1]
        conteos.append(
            {
                "periodo_desarrollo": periodo + 1,
                "n_ratios_individuales": int(pares_validos.sum()),
            }
        )
    return pd.DataFrame(conteos)


def calcular_estadisticas_acumuladas(resultados_df: pd.DataFrame, escenario: str, metodo: str) -> pd.DataFrame:
    subconjunto = (
        resultados_df.loc[(resultados_df["escenario"] == escenario) & (resultados_df["metodo"] == metodo)]
        .sort_values("replica")
        .reset_index(drop=True)
    )
    errores = subconjunto["ibnr_estimado"].to_numpy() - subconjunto["ibnr_real"].to_numpy()
    errores_porcentuales_absolutos = np.abs(errores / subconjunto["ibnr_real"].to_numpy())
    replicas = np.arange(1, len(subconjunto) + 1)

    error_cuadratico_acumulado = np.cumsum(np.square(errores))
    sesgo_acumulado = np.cumsum(errores)
    mape_acumulado = np.cumsum(errores_porcentuales_absolutos)

    salida = subconjunto.loc[:, ["escenario", "metodo", "replica"]].copy()
    salida["sesgo_acumulado"] = sesgo_acumulado / replicas
    salida["rmse_acumulado"] = np.sqrt(error_cuadratico_acumulado / replicas)
    salida["mape_acumulado"] = mape_acumulado / replicas
    return salida


def resumir_dominancia_metodos(clasificacion_df: pd.DataFrame) -> pd.DataFrame:
    ganadores = clasificacion_df.loc[clasificacion_df["rango"] == 1]
    return (
        ganadores.groupby("metodo", as_index=False)
        .agg(escenarios_ganados=("escenario", "count"))
        .sort_values("escenarios_ganados", ascending=False)
        .reset_index(drop=True)
    )
