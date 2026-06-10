from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .configuracion import ConfiguracionSimulacion, EscenarioContaminacion


@dataclass
class SimulacionTriangulo:
    incremental_completo: np.ndarray
    acumulado_completo: np.ndarray
    incremental_observado: np.ndarray
    acumulado_observado: np.ndarray
    mascara_observada: np.ndarray
    ibnr_real: float
    metadatos_contaminacion: dict[str, Any]


def mascara_observada(n_periodos: int) -> np.ndarray:
    fila, columna = np.indices((n_periodos, n_periodos))
    return (fila + columna) <= (n_periodos - 1)


def generar_triangulo_incremental(
    configuracion: ConfiguracionSimulacion,
    generador: np.random.Generator,
) -> np.ndarray:
    medias = np.outer(configuracion.medias_ultimas, configuracion.desarrollo_incremental)
    if configuracion.distribucion == "gamma":
        forma = 1.0 / configuracion.dispersion_phi
        escala = configuracion.dispersion_phi * medias
        return generador.gamma(shape=forma, scale=escala)
    if configuracion.distribucion == "lognormal":
        sigma_cuadrado = np.log1p(configuracion.dispersion_phi)
        sigma = np.sqrt(sigma_cuadrado)
        media_logaritmica = np.log(medias) - 0.5 * sigma_cuadrado
        return generador.lognormal(mean=media_logaritmica, sigma=sigma)
    raise ValueError(f"Distribucion no soportada: {configuracion.distribucion}")


def incremental_a_acumulado(triangulo_incremental: np.ndarray) -> np.ndarray:
    return triangulo_incremental.cumsum(axis=1)


def construir_triangulo_observado(triangulo: np.ndarray, mascara: np.ndarray) -> np.ndarray:
    observado = triangulo.copy().astype(float)
    observado[~mascara] = np.nan
    return observado


def calcular_ibnr_real(triangulo_incremental: np.ndarray, mascara: np.ndarray) -> float:
    return float(np.where(mascara, 0.0, triangulo_incremental).sum())


def _celdas_elegibles(mascara: np.ndarray, ubicacion: str) -> np.ndarray:
    coordenadas = np.argwhere(mascara)
    if ubicacion == "aleatoria":
        return coordenadas
    if ubicacion == "temprana":
        seleccionadas = []
        for fila in range(mascara.shape[0]):
            columnas_observadas = np.where(mascara[fila])[0]
            if columnas_observadas.size == 0:
                continue
            n_local = max(1, int(np.ceil(columnas_observadas.size / 3)))
            seleccionadas.extend((fila, int(columna)) for columna in columnas_observadas[:n_local])
        return np.array(seleccionadas, dtype=int)
    if ubicacion == "tardia":
        seleccionadas = []
        for fila in range(mascara.shape[0]):
            columnas_observadas = np.where(mascara[fila])[0]
            if columnas_observadas.size == 0:
                continue
            n_local = max(1, int(np.ceil(columnas_observadas.size / 3)))
            seleccionadas.extend((fila, int(columna)) for columna in columnas_observadas[-n_local:])
        return np.array(seleccionadas, dtype=int)
    if ubicacion == "ninguna":
        return np.empty((0, 2), dtype=int)
    raise ValueError(f"Ubicacion no soportada: {ubicacion}")


def contaminar_triangulo_incremental(
    triangulo_incremental: np.ndarray,
    mascara: np.ndarray,
    escenario: EscenarioContaminacion,
    generador: np.random.Generator,
) -> tuple[np.ndarray, dict[str, Any]]:
    contaminado = triangulo_incremental.copy().astype(float)
    if escenario.es_limpio():
        return contaminado, {"celdas_seleccionadas": [], "n_seleccionadas": 0, "celdas_elegibles": 0}

    elegibles = _celdas_elegibles(mascara, escenario.ubicacion)
    if elegibles.size == 0:
        return contaminado, {"celdas_seleccionadas": [], "n_seleccionadas": 0, "celdas_elegibles": 0}

    n_seleccionadas = int(np.round(escenario.proporcion * len(elegibles)))
    n_seleccionadas = max(1, min(len(elegibles), n_seleccionadas))
    indices_seleccionados = generador.choice(len(elegibles), size=n_seleccionadas, replace=False)
    celdas_seleccionadas = elegibles[indices_seleccionados]

    for fila, columna in celdas_seleccionadas:
        contaminado[fila, columna] *= escenario.magnitud

    metadatos = {
        "celdas_seleccionadas": [tuple(map(int, celda)) for celda in celdas_seleccionadas],
        "n_seleccionadas": int(n_seleccionadas),
        "celdas_elegibles": int(len(elegibles)),
    }
    return contaminado, metadatos


def simular_un_triangulo(
    configuracion: ConfiguracionSimulacion,
    escenario: EscenarioContaminacion,
    generador: np.random.Generator,
) -> SimulacionTriangulo:
    mascara = mascara_observada(configuracion.n_periodos)
    incremental_completo = generar_triangulo_incremental(configuracion, generador)
    acumulado_completo = incremental_a_acumulado(incremental_completo)
    valor_ibnr_real = calcular_ibnr_real(incremental_completo, mascara)

    incremental_contaminado, metadatos = contaminar_triangulo_incremental(
        incremental_completo,
        mascara,
        escenario,
        generador,
    )
    acumulado_contaminado = incremental_a_acumulado(incremental_contaminado)

    incremental_observado = construir_triangulo_observado(incremental_contaminado, mascara)
    acumulado_observado = construir_triangulo_observado(acumulado_contaminado, mascara)

    return SimulacionTriangulo(
        incremental_completo=incremental_completo,
        acumulado_completo=acumulado_completo,
        incremental_observado=incremental_observado,
        acumulado_observado=acumulado_observado,
        mascara_observada=mascara,
        ibnr_real=valor_ibnr_real,
        metadatos_contaminacion=metadatos,
    )
