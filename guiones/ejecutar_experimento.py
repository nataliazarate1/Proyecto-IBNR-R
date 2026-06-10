from __future__ import annotations

import argparse
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
FUENTE = RAIZ / "fuente"
if str(FUENTE) not in sys.path:
    sys.path.append(str(FUENTE))

from proyecto_ibnr.configuracion import construir_configuracion_base, construir_escenarios_base  # noqa: E402
from proyecto_ibnr.diagnosticos import resumir_dominancia_metodos  # noqa: E402
from proyecto_ibnr.evaluacion import (  # noqa: E402
    calcular_metricas_metodos,
    clasificar_metodos_en_escenario,
    comparar_metodos_con_base,
    evaluar_hipotesis_principal,
    resumir_resultados_familia,
)
from proyecto_ibnr.experimento import construir_resumen_global, ejecutar_experimento  # noqa: E402


def interpretar_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecuta el estudio de simulacion del IBNR y exporta los resumenes en CSV."
    )
    parser.add_argument("--replicas", type=int, default=1000, help="Numero de replicas por escenario.")
    parser.add_argument("--distribucion", choices=["gamma", "lognormal"], default="gamma")
    parser.add_argument(
        "--directorio-salida",
        dest="directorio_salida",
        default="resultados",
        help="Directorio para exportar los archivos CSV.",
    )
    return parser.parse_args()


def main() -> None:
    argumentos = interpretar_argumentos()
    configuracion = construir_configuracion_base(distribucion=argumentos.distribucion)
    escenarios = construir_escenarios_base()

    resultados = ejecutar_experimento(configuracion, escenarios, n_replicas=argumentos.replicas)
    metricas = calcular_metricas_metodos(resultados)
    clasificacion = clasificar_metodos_en_escenario(metricas, metrica="rmse")
    comparaciones = comparar_metodos_con_base(resultados, base="clasico")
    dominancia = resumir_dominancia_metodos(clasificacion)
    resumen_global = construir_resumen_global(metricas)
    resultados_familia = resumir_resultados_familia(metricas, clasificacion)
    _, resumen_desviacion_robusta, tabla_hipotesis = evaluar_hipotesis_principal(metricas, resultados_familia)

    directorio_salida = RAIZ / argumentos.directorio_salida
    directorio_salida.mkdir(parents=True, exist_ok=True)

    sufijo = f"{argumentos.distribucion}_{argumentos.replicas}replicas"
    resultados.to_csv(directorio_salida / f"resultados_crudos_{sufijo}.csv", index=False)
    metricas.to_csv(directorio_salida / f"metricas_{sufijo}.csv", index=False)
    clasificacion.to_csv(directorio_salida / f"clasificacion_{sufijo}.csv", index=False)
    comparaciones.to_csv(directorio_salida / f"comparaciones_con_clasico_{sufijo}.csv", index=False)
    dominancia.to_csv(directorio_salida / f"dominancia_metodos_{sufijo}.csv", index=False)
    resumen_global.to_csv(directorio_salida / f"resumen_global_{sufijo}.csv", index=False)
    resultados_familia.to_csv(directorio_salida / f"resultados_familia_{sufijo}.csv", index=False)
    resumen_desviacion_robusta.to_csv(directorio_salida / f"resumen_desviacion_robusta_{sufijo}.csv", index=False)
    tabla_hipotesis.to_csv(directorio_salida / f"evaluacion_hipotesis_{sufijo}.csv", index=False)

    print(f"Resultados exportados en {directorio_salida}")


if __name__ == "__main__":
    main()
