from __future__ import annotations

import numpy as np
import pandas as pd

from .configuracion import ConfiguracionSimulacion, EscenarioContaminacion
from .metodos import estimar_ibnr_todos_metodos
from .simulacion import (
    calcular_ibnr_real,
    contaminar_triangulo_incremental,
    generar_triangulo_incremental,
    incremental_a_acumulado,
    mascara_observada,
)


def _triangulo_deterministico(configuracion: ConfiguracionSimulacion) -> np.ndarray:
    return np.outer(configuracion.medias_ultimas, configuracion.desarrollo_incremental)


def validar_estructura_media_incremental(
    configuracion: ConfiguracionSimulacion,
    n_muestras: int = 3000,
) -> dict[str, float | bool]:
    generador = np.random.default_rng(configuracion.semilla_aleatoria)
    media_esperada = np.outer(configuracion.medias_ultimas, configuracion.desarrollo_incremental)
    muestras = np.stack([generar_triangulo_incremental(configuracion, generador) for _ in range(n_muestras)])
    media_muestral = muestras.mean(axis=0)
    error_relativo = np.abs(media_muestral - media_esperada) / media_esperada
    return {
        "passed": bool(error_relativo.mean() < 0.05),
        "mean_relative_error": float(error_relativo.mean()),
        "max_relative_error": float(error_relativo.max()),
    }


def validar_consistencia_acumulada(configuracion: ConfiguracionSimulacion) -> dict[str, float | bool]:
    generador = np.random.default_rng(configuracion.semilla_aleatoria)
    incremental = generar_triangulo_incremental(configuracion, generador)
    acumulado = incremental_a_acumulado(incremental)
    filas_monotonas = np.all(np.diff(acumulado, axis=1) >= 0)
    error_reconstruccion = float(np.abs(acumulado[:, -1] - incremental.sum(axis=1)).max())
    return {
        "passed": bool(filas_monotonas and error_reconstruccion < 1e-8),
        "monotone_rows": bool(filas_monotonas),
        "max_reconstruction_error": error_reconstruccion,
    }


def validar_mascara_e_ibnr(configuracion: ConfiguracionSimulacion) -> dict[str, float | bool]:
    mascara = mascara_observada(configuracion.n_periodos)
    incremental = _triangulo_deterministico(configuracion)
    ibnr_desde_mascara = calcular_ibnr_real(incremental, mascara)
    total = float(incremental.sum())
    total_observado = float(incremental[mascara].sum())
    celdas_observadas_esperadas = configuracion.n_periodos * (configuracion.n_periodos + 1) / 2
    return {
        "passed": bool(np.isclose(ibnr_desde_mascara, total - total_observado) and mascara.sum() == celdas_observadas_esperadas),
        "observed_cells": int(mascara.sum()),
        "expected_observed_cells": int(celdas_observadas_esperadas),
        "ibnr_consistency_gap": float(abs(ibnr_desde_mascara - (total - total_observado))),
    }


def validar_logica_contaminacion(configuracion: ConfiguracionSimulacion) -> dict[str, float | bool]:
    generador = np.random.default_rng(configuracion.semilla_aleatoria)
    mascara = mascara_observada(configuracion.n_periodos)
    incremental = _triangulo_deterministico(configuracion)
    escenario = EscenarioContaminacion(nombre="prueba", proporcion=0.10, magnitud=5.0, ubicacion="temprana")
    contaminado, metadatos = contaminar_triangulo_incremental(incremental, mascara, escenario, generador)
    celdas_cambiadas = np.argwhere(np.abs(contaminado - incremental) > 0)
    solo_observadas = all(mascara[fila, columna] for fila, columna in celdas_cambiadas)
    multiplicacion_correcta = True
    for fila, columna in celdas_cambiadas:
        if not np.isclose(contaminado[fila, columna], incremental[fila, columna] * escenario.magnitud):
            multiplicacion_correcta = False
            break
    return {
        "passed": bool(solo_observadas and multiplicacion_correcta and len(celdas_cambiadas) == metadatos["n_seleccionadas"]),
        "n_changed": int(len(celdas_cambiadas)),
        "n_seleccionadas": int(metadatos["n_seleccionadas"]),
        "only_observed_cells_changed": bool(solo_observadas),
    }


def validar_metodos_en_triangulo_sin_ruido(configuracion: ConfiguracionSimulacion) -> dict[str, float | bool]:
    mascara = mascara_observada(configuracion.n_periodos)
    incremental = _triangulo_deterministico(configuracion)
    acumulado = incremental_a_acumulado(incremental)
    acumulado_observado = acumulado.astype(float)
    acumulado_observado[~mascara] = np.nan
    ibnr_real = calcular_ibnr_real(incremental, mascara)
    estimaciones = estimar_ibnr_todos_metodos(acumulado_observado, configuracion)
    brecha_maxima = max(abs(resultado.ibnr_estimado - ibnr_real) for resultado in estimaciones.values())
    return {
        "passed": bool(brecha_maxima < 1e-8),
        "max_estimation_gap": float(brecha_maxima),
    }


def ejecutar_validacion_completa(configuracion: ConfiguracionSimulacion) -> pd.DataFrame:
    validaciones = {
        "incremental_mean_structure": validar_estructura_media_incremental(configuracion),
        "cumulative_consistency": validar_consistencia_acumulada(configuracion),
        "mask_and_ibnr_definition": validar_mascara_e_ibnr(configuracion),
        "contamination_logic": validar_logica_contaminacion(configuracion),
        "methods_on_noise_free_triangle": validar_metodos_en_triangulo_sin_ruido(configuracion),
    }
    filas = []
    for nombre, resultado in validaciones.items():
        fila = {"check": nombre}
        fila.update(resultado)
        filas.append(fila)
    return pd.DataFrame(filas)
