from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .configuracion import ConfiguracionSimulacion


@dataclass
class EstimacionMetodo:
    metodo: str
    factores: np.ndarray
    acumulado_proyectado: np.ndarray
    ibnr_estimado: float


def _ratios_individuales_desarrollo(acumulado_observado: np.ndarray, periodo: int) -> np.ndarray:
    columna_actual = acumulado_observado[:, periodo]
    columna_siguiente = acumulado_observado[:, periodo + 1]
    validos = (~np.isnan(columna_actual)) & (~np.isnan(columna_siguiente)) & (columna_actual > 0)
    return columna_siguiente[validos] / columna_actual[validos]


def _factor_clasico(acumulado_observado: np.ndarray, periodo: int) -> float:
    columna_actual = acumulado_observado[:, periodo]
    columna_siguiente = acumulado_observado[:, periodo + 1]
    validos = (~np.isnan(columna_actual)) & (~np.isnan(columna_siguiente)) & (columna_actual > 0)
    if not np.any(validos):
        return 1.0
    return float(columna_siguiente[validos].sum() / columna_actual[validos].sum())


def _media_recortada(valores: np.ndarray, fraccion_recorte: float) -> float:
    if valores.size == 0:
        return 1.0
    valores_ordenados = np.sort(valores)
    k = int(np.floor(fraccion_recorte * valores_ordenados.size))
    if 2 * k >= valores_ordenados.size:
        return float(valores_ordenados.mean())
    ventana = valores_ordenados[k : valores_ordenados.size - k]
    return float(ventana.mean())


def _factor_ponderado_robusto(valores: np.ndarray, umbral: float, epsilon: float) -> float:
    if valores.size == 0:
        return 1.0
    centro = float(np.median(valores))
    desviacion_mediana_absoluta = float(np.median(np.abs(valores - centro)))
    escala = 1.4826 * desviacion_mediana_absoluta + epsilon
    distancia_estandarizada = np.abs(valores - centro) / escala
    pesos = np.minimum(1.0, umbral / (distancia_estandarizada + epsilon))
    return float((pesos * valores).sum() / pesos.sum())


def estimar_factores_desarrollo(
    acumulado_observado: np.ndarray,
    configuracion: ConfiguracionSimulacion,
) -> dict[str, np.ndarray]:
    n_periodos = acumulado_observado.shape[1]
    clasico = np.ones(n_periodos - 1)
    mediana = np.ones(n_periodos - 1)
    truncada = np.ones(n_periodos - 1)
    ponderado = np.ones(n_periodos - 1)

    for periodo in range(n_periodos - 1):
        ratios = _ratios_individuales_desarrollo(acumulado_observado, periodo)
        clasico[periodo] = _factor_clasico(acumulado_observado, periodo)
        mediana[periodo] = float(np.median(ratios)) if ratios.size else 1.0
        truncada[periodo] = _media_recortada(ratios, configuracion.fraccion_recorte_contaminacion)
        ponderado[periodo] = _factor_ponderado_robusto(ratios, configuracion.umbral_pesos, configuracion.epsilon)

    return {
        "clasico": clasico,
        "mediana": mediana,
        "truncada": truncada,
        "ponderado": ponderado,
    }


def proyectar_triangulo_acumulado(acumulado_observado: np.ndarray, factores: np.ndarray) -> np.ndarray:
    proyectado = acumulado_observado.copy().astype(float)
    n_filas, n_columnas = proyectado.shape

    for fila in range(n_filas):
        posiciones_observadas = np.where(~np.isnan(proyectado[fila]))[0]
        if posiciones_observadas.size == 0:
            continue
        ultimo_observado = int(posiciones_observadas.max())
        for periodo in range(ultimo_observado, n_columnas - 1):
            valor_base = proyectado[fila, periodo]
            if np.isnan(valor_base):
                break
            proyectado[fila, periodo + 1] = valor_base * factores[periodo]
    return proyectado


def estimar_ibnr_desde_proyeccion(acumulado_observado: np.ndarray, acumulado_proyectado: np.ndarray) -> float:
    ibnr = 0.0
    for fila in range(acumulado_observado.shape[0]):
        posiciones_observadas = np.where(~np.isnan(acumulado_observado[fila]))[0]
        if posiciones_observadas.size == 0:
            continue
        ultimo_observado = int(posiciones_observadas.max())
        valor_observado_final = acumulado_observado[fila, ultimo_observado]
        ultimo = acumulado_proyectado[fila, -1]
        ibnr += float(ultimo - valor_observado_final)
    return ibnr


def estimar_ibnr_todos_metodos(
    acumulado_observado: np.ndarray,
    configuracion: ConfiguracionSimulacion,
) -> dict[str, EstimacionMetodo]:
    mapa_factores = estimar_factores_desarrollo(acumulado_observado, configuracion)
    estimaciones: dict[str, EstimacionMetodo] = {}
    for nombre_metodo, factores in mapa_factores.items():
        acumulado_proyectado = proyectar_triangulo_acumulado(acumulado_observado, factores)
        estimacion_ibnr = estimar_ibnr_desde_proyeccion(acumulado_observado, acumulado_proyectado)
        estimaciones[nombre_metodo] = EstimacionMetodo(
            metodo=nombre_metodo,
            factores=factores,
            acumulado_proyectado=acumulado_proyectado,
            ibnr_estimado=estimacion_ibnr,
        )
    return estimaciones
