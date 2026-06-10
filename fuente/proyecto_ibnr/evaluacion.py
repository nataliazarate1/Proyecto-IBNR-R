from __future__ import annotations

import numpy as np
import pandas as pd

COLUMNAS_METADATOS_ESCENARIO = (
    "proporcion_contaminacion",
    "magnitud_contaminacion",
    "ubicacion_contaminacion",
)

ETIQUETAS_METODOS = {
    "clasico": "Clásico",
    "mediana": "Mediana",
    "truncada": "Media truncada",
    "ponderado": "Ponderado robusto",
}


def _fila_metricas(grupo: pd.DataFrame) -> pd.Series:
    errores = grupo["ibnr_estimado"] - grupo["ibnr_real"]
    errores_absolutos = np.abs(errores)
    errores_porcentuales = errores / grupo["ibnr_real"]
    errores_porcentuales_absolutos = np.abs(errores_porcentuales)
    estimaciones = grupo["ibnr_estimado"]
    n = len(grupo)
    valor_z = 1.96

    sesgo = errores.mean()
    mape = errores_porcentuales_absolutos.mean()
    mae = errores_absolutos.mean()
    error_estandar_monte_carlo_sesgo = errores.std(ddof=1) / np.sqrt(n)
    error_estandar_monte_carlo_mape = errores_porcentuales_absolutos.std(ddof=1) / np.sqrt(n)
    error_estandar_monte_carlo_mae = errores_absolutos.std(ddof=1) / np.sqrt(n)

    return pd.Series(
        {
            "n_replicas": n,
            "sesgo": sesgo,
            "mse": np.mean(np.square(errores)),
            "rmse": np.sqrt(np.mean(np.square(errores))),
            "mae": mae,
            "mape": mape,
            "error_porcentual_promedio": errores_porcentuales.mean(),
            "desviacion_estandar_estimaciones": estimaciones.std(ddof=1),
            "tasa_sobreestimacion": np.mean(errores > 0),
            "tasa_subestimacion": np.mean(errores < 0),
            "error_absoluto_mediano": np.median(errores_absolutos),
            "error_estandar_monte_carlo_sesgo": error_estandar_monte_carlo_sesgo,
            "error_estandar_monte_carlo_mape": error_estandar_monte_carlo_mape,
            "error_estandar_monte_carlo_mae": error_estandar_monte_carlo_mae,
            "sesgo_ic_inferior": sesgo - valor_z * error_estandar_monte_carlo_sesgo,
            "sesgo_ic_superior": sesgo + valor_z * error_estandar_monte_carlo_sesgo,
            "mape_ic_inferior": max(0.0, mape - valor_z * error_estandar_monte_carlo_mape),
            "mape_ic_superior": mape + valor_z * error_estandar_monte_carlo_mape,
            "mae_ic_inferior": max(0.0, mae - valor_z * error_estandar_monte_carlo_mae),
            "mae_ic_superior": mae + valor_z * error_estandar_monte_carlo_mae,
        }
    )


def calcular_metricas_metodos(resultados_df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    agrupado = resultados_df.groupby(["escenario", "metodo"], sort=False)
    for (escenario, metodo), grupo in agrupado:
        fila = {"escenario": escenario, "metodo": metodo}
        for columna in COLUMNAS_METADATOS_ESCENARIO:
            if columna in grupo.columns:
                fila[columna] = grupo[columna].iloc[0]
        fila.update(_fila_metricas(grupo).to_dict())
        filas.append(fila)
    resumen = pd.DataFrame(filas)
    return resumen.sort_values(["escenario", "metodo"]).reset_index(drop=True)


def resumir_resultados_por_escenario(metricas_df: pd.DataFrame, metrica: str = "rmse") -> pd.DataFrame:
    tabla = metricas_df.pivot(index="escenario", columns="metodo", values=metrica)
    return tabla.sort_index()


def clasificar_metodos_en_escenario(metricas_df: pd.DataFrame, metrica: str = "rmse") -> pd.DataFrame:
    clasificacion = metricas_df.copy()
    clasificacion["rango"] = clasificacion.groupby("escenario")[metrica].rank(method="dense")
    return clasificacion.sort_values(["escenario", "rango", "metodo"]).reset_index(drop=True)


def comparar_metodos_con_base(
    resultados_df: pd.DataFrame,
    base: str = "clasico",
) -> pd.DataFrame:
    base_df = (
        resultados_df.loc[resultados_df["metodo"] == base, ["escenario", "replica", "ibnr_real", "ibnr_estimado"]]
        .rename(columns={"ibnr_estimado": "ibnr_estimado_base"})
        .copy()
    )
    comparacion_df = resultados_df.loc[resultados_df["metodo"] != base].merge(
        base_df,
        on=["escenario", "replica", "ibnr_real"],
        how="inner",
        validate="many_to_one",
    )
    errores_metodo = comparacion_df["ibnr_estimado"] - comparacion_df["ibnr_real"]
    errores_base = comparacion_df["ibnr_estimado_base"] - comparacion_df["ibnr_real"]

    comparacion_df["delta_error_cuadratico"] = np.square(errores_metodo) - np.square(errores_base)
    comparacion_df["delta_error_absoluto"] = np.abs(errores_metodo) - np.abs(errores_base)
    comparacion_df["delta_error_porcentual_absoluto"] = np.abs(errores_metodo / comparacion_df["ibnr_real"]) - np.abs(
        errores_base / comparacion_df["ibnr_real"]
    )

    filas = []
    valor_z = 1.96
    for (escenario, metodo), grupo in comparacion_df.groupby(["escenario", "metodo"], sort=False):
        fila = {"escenario": escenario, "metodo": metodo, "base": base, "n_replicas": len(grupo)}
        for columna_origen, prefijo in [
            ("delta_error_cuadratico", "delta_mse"),
            ("delta_error_absoluto", "delta_mae"),
            ("delta_error_porcentual_absoluto", "delta_mape"),
        ]:
            valores = grupo[columna_origen].to_numpy()
            promedio = float(valores.mean())
            error_estandar = float(valores.std(ddof=1) / np.sqrt(len(valores)))
            fila[f"{prefijo}_promedio"] = promedio
            fila[f"{prefijo}_error_estandar"] = error_estandar
            fila[f"{prefijo}_ic_inferior"] = promedio - valor_z * error_estandar
            fila[f"{prefijo}_ic_superior"] = promedio + valor_z * error_estandar
            fila[f"{prefijo}_mejora"] = bool(fila[f"{prefijo}_ic_superior"] < 0)
            fila[f"{prefijo}_empeora"] = bool(fila[f"{prefijo}_ic_inferior"] > 0)
        filas.append(fila)
    return pd.DataFrame(filas).sort_values(["escenario", "metodo"]).reset_index(drop=True)


def resumir_resultados_familia(
    metricas_df: pd.DataFrame,
    clasificacion_df: pd.DataFrame,
    etiquetas_metodos: dict[str, str] | None = None,
) -> pd.DataFrame:
    etiquetas = ETIQUETAS_METODOS if etiquetas_metodos is None else etiquetas_metodos
    especificaciones = [
        ("Sin contaminación", metricas_df["escenario"].eq("base_sin_contaminacion"), clasificacion_df["escenario"].eq("base_sin_contaminacion")),
        ("Contaminación del 5%", metricas_df["proporcion_contaminacion"].eq(0.05), clasificacion_df["proporcion_contaminacion"].eq(0.05)),
        ("Contaminación del 10%", metricas_df["proporcion_contaminacion"].eq(0.10), clasificacion_df["proporcion_contaminacion"].eq(0.10)),
        ("Contaminación del 20%", metricas_df["proporcion_contaminacion"].eq(0.20), clasificacion_df["proporcion_contaminacion"].eq(0.20)),
        ("Outliers x2", metricas_df["magnitud_contaminacion"].eq(2.0), clasificacion_df["magnitud_contaminacion"].eq(2.0)),
        ("Outliers x5", metricas_df["magnitud_contaminacion"].eq(5.0), clasificacion_df["magnitud_contaminacion"].eq(5.0)),
        ("Outliers x10", metricas_df["magnitud_contaminacion"].eq(10.0), clasificacion_df["magnitud_contaminacion"].eq(10.0)),
        ("Contaminación temprana", metricas_df["ubicacion_contaminacion"].eq("temprana"), clasificacion_df["ubicacion_contaminacion"].eq("temprana")),
        ("Contaminación tardía", metricas_df["ubicacion_contaminacion"].eq("tardia"), clasificacion_df["ubicacion_contaminacion"].eq("tardia")),
        ("Contaminación aleatoria", metricas_df["ubicacion_contaminacion"].eq("aleatoria"), clasificacion_df["ubicacion_contaminacion"].eq("aleatoria")),
    ]

    filas = []
    for nombre_familia, filtro_metricas, filtro_clasificacion in especificaciones:
        resumen_metricas = (
            metricas_df.loc[filtro_metricas]
            .groupby("metodo", as_index=False)[["rmse", "mape", "desviacion_estandar_estimaciones"]]
            .mean()
            .sort_values("rmse")
        )
        resumen_victorias = (
            clasificacion_df.loc[filtro_clasificacion & clasificacion_df["rango"].eq(1)]
            .groupby("metodo")
            .size()
            .sort_values(ascending=False)
        )

        mejor_promedio = resumen_metricas.iloc[0]
        codigo_ganador = resumen_victorias.index[0]
        victorias = int(resumen_victorias.iloc[0])
        total_escenarios = int(resumen_victorias.sum())

        filas.append(
            {
                "familia": nombre_familia,
                "codigo_metodo_mejor_promedio": mejor_promedio["metodo"],
                "metodo_mejor_promedio": etiquetas[mejor_promedio["metodo"]],
                "rmse_promedio": round(float(mejor_promedio["rmse"]), 2),
                "mape_promedio": round(float(mejor_promedio["mape"]), 3),
                "desviacion_estandar_promedio": round(float(mejor_promedio["desviacion_estandar_estimaciones"]), 2),
                "codigo_metodo_mas_victorias": codigo_ganador,
                "metodo_con_mas_victorias": etiquetas[codigo_ganador],
                "victorias_escenario": victorias,
                "total_escenarios": total_escenarios,
                "frecuencia_ganadora": f"{victorias}/{total_escenarios}",
            }
        )

    return pd.DataFrame(filas)


def evaluar_hipotesis_principal(
    metricas_df: pd.DataFrame,
    resultados_familia_df: pd.DataFrame,
    etiquetas_metodos: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    etiquetas = ETIQUETAS_METODOS if etiquetas_metodos is None else etiquetas_metodos
    metricas_clasicas = metricas_df.query("escenario != 'base_sin_contaminacion' and metodo == 'clasico'").copy()
    metricas_clasicas["log_magnitud"] = np.log(metricas_clasicas["magnitud_contaminacion"])
    tabla_correlacion = metricas_clasicas[
        ["proporcion_contaminacion", "magnitud_contaminacion", "log_magnitud", "rmse", "mape", "desviacion_estandar_estimaciones"]
    ].corr(method="spearman")

    apoyo_desviacion = (
        metricas_df.query("escenario != 'base_sin_contaminacion'")
        .pivot(index="escenario", columns="metodo", values="desviacion_estandar_estimaciones")
        .assign(
            mediana_menor_que_clasico=lambda df: df["mediana"] < df["clasico"],
            truncada_menor_que_clasico=lambda df: df["truncada"] < df["clasico"],
            ponderado_menor_que_clasico=lambda df: df["ponderado"] < df["clasico"],
        )
    )

    resumen_desviacion_robusta = pd.DataFrame(
        {
            "metodo_robusto": ["mediana", "truncada", "ponderado"],
            "escenarios_con_menor_sd_que_clasico": [
                int(apoyo_desviacion["mediana_menor_que_clasico"].sum()),
                int(apoyo_desviacion["truncada_menor_que_clasico"].sum()),
                int(apoyo_desviacion["ponderado_menor_que_clasico"].sum()),
            ],
        }
    )
    resumen_desviacion_robusta["total_escenarios_contaminados"] = len(apoyo_desviacion)
    resumen_desviacion_robusta["proporcion_favorable"] = (
        resumen_desviacion_robusta["escenarios_con_menor_sd_que_clasico"]
        / resumen_desviacion_robusta["total_escenarios_contaminados"]
    )
    resumen_desviacion_robusta["etiqueta_metodo_robusto"] = resumen_desviacion_robusta["metodo_robusto"].map(etiquetas)

    mejor_fila_estabilidad = resumen_desviacion_robusta.sort_values(
        "escenarios_con_menor_sd_que_clasico",
        ascending=False,
    ).iloc[0]
    familias_contaminadas = resultados_familia_df.query("familia != 'Sin contaminación'")
    conteo_lideres = (
        familias_contaminadas.groupby("codigo_metodo_mejor_promedio").size().sort_values(ascending=False)
    )
    metodo_lider = conteo_lideres.index[0]
    cantidad_familias = int(conteo_lideres.iloc[0])

    tabla_hipotesis = pd.DataFrame(
        [
            {
                "hipotesis": "H1",
                "evidencia_principal": (
                    f"Correlacion de Spearman del RMSE clasico con proporcion = "
                    f"{tabla_correlacion.loc['proporcion_contaminacion', 'rmse']:.3f}, "
                    f"con magnitud = {tabla_correlacion.loc['magnitud_contaminacion', 'rmse']:.3f}. "
                    f"En la lectura por familias, {etiquetas[metodo_lider]} lidera "
                    f"{cantidad_familias} de {len(familias_contaminadas)} familias contaminadas segun RMSE promedio. "
                    f"En estabilidad, el metodo robusto con mejor resultado es "
                    f"{mejor_fila_estabilidad['etiqueta_metodo_robusto']}, que mejora al clasico en "
                    f"{int(mejor_fila_estabilidad['escenarios_con_menor_sd_que_clasico'])} de {len(apoyo_desviacion)} escenarios contaminados."
                ),
                "dictamen": (
                    "Apoyada"
                    if (
                        tabla_correlacion.loc["proporcion_contaminacion", "rmse"] > 0
                        and tabla_correlacion.loc["magnitud_contaminacion", "rmse"] > 0
                        and metodo_lider != "clasico"
                        and int(mejor_fila_estabilidad["escenarios_con_menor_sd_que_clasico"]) >= len(apoyo_desviacion) / 2
                    )
                    else "Parcialmente apoyada"
                ),
            }
        ]
    )
    return tabla_correlacion, resumen_desviacion_robusta, tabla_hipotesis
