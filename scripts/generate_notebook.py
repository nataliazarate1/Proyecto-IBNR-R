from __future__ import annotations

import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks" / "ibnr_chain_ladder_robusto.ipynb"


def markdown_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": textwrap.dedent(text).strip("\n"),
    }


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": textwrap.dedent(text).strip("\n"),
    }


def build_notebook() -> dict:
    cells = [
        markdown_cell(
            """
            # Evaluacion comparativa del Chain-Ladder clasico y robusto en la estimacion del IBNR

            **Proyecto de grado - Estadistica**

            Este notebook implementa, documenta y ejecuta un experimento de simulacion para comparar el metodo Chain-Ladder clasico con tres variantes robustas frente a valores atipicos controlados. La logica estadistica se distribuye en modulos dentro de `src/ibnr_project`, mientras que este notebook funciona como documento reproducible, interpretable y listo para GitHub.
            """
        ),
        markdown_cell(
            """
            ## Hoja de ruta

            El flujo sigue una secuencia metodologica explicita:

            1. Definir el proceso generador de datos y sus parametros.
            2. Validar que la simulacion reproduce la estructura teorica propuesta.
            3. Construir triangulos observados y contaminar solo la parte visible.
            4. Estimar el IBNR con Chain-Ladder clasico, mediana, media truncada y ponderacion robusta.
            5. Repetir el experimento en multiples replicas y escenarios.
            6. Comparar precision, estabilidad y sesgo sistematico.

            Esta separacion mejora la trazabilidad metodologica: cada bloque responde a una pregunta estadistica concreta y se puede auditar por separado.
            """
        ),
        markdown_cell(
            """
            ## Por que esta version mejora la metodologia original

            La metodologia base era buena, pero aqui se refuerza en cinco puntos importantes:

            - **Escenarios balanceados**: en lugar de unos pocos escenarios ilustrativos, se usa una matriz factorial completa con 27 escenarios contaminados y 1 base. Eso permite separar el efecto de la proporcion, la magnitud y la ubicacion del outlier.
            - **Heterogeneidad controlada entre anos de ocurrencia**: los ultimates esperados `mu_i` no son constantes; siguen una tendencia suave. Esto evita un experimento demasiado artificial y se acerca mejor a datos actuariales.
            - **Version robusta ponderada mejor escalada**: las ponderaciones se construyen con desviacion absoluta mediana (MAD), no con distancia cruda. Esto hace comparable la penalizacion de outliers entre periodos de desarrollo con distinta variabilidad.
            - **Validacion interna del simulador**: no basta con correr replicas. Se verifica que las medias simuladas respeten la esperanza teorica, que el triangulo acumulado sea coherente, que el IBNR real este bien definido y que los metodos recuperen el valor correcto en el caso sin ruido.
            - **Repositorio mas reproducible**: la simulacion usa `numpy` como motor principal, lo que reduce dependencias y facilita la ejecucion en GitHub o en otros equipos.
            """
        ),
        markdown_cell(
            """
            ## Librerias y justificacion

            - `numpy`: es el nucleo numerico del proyecto. Se usa para simulacion Gamma y Lognormal, algebra matricial, mascaras del triangulo y operaciones vectorizadas. Se elige porque ofrece velocidad, estabilidad numerica y reproducibilidad con `Generator`.
            - `pandas`: organiza las replicas, escenarios y metricas en tablas limpias. Esto facilita resumir resultados, exportarlos y construir comparaciones defendibles.
            - `matplotlib`: provee control fino de las figuras. Es util para graficos academicos donde queremos decidir exactamente que mostrar.
            - `seaborn`: simplifica visualizaciones comparativas como boxplots y heatmaps. Se usa sobre `matplotlib` para ganar legibilidad.
            - `pathlib`: ayuda a trabajar con rutas del repositorio de forma portable.

            Nota importante: `scipy` aparece con frecuencia en estudios de simulacion, pero en esta entrega no es una dependencia obligatoria porque `numpy` ya ofrece los generadores Gamma y Lognormal que necesitamos. Eso mejora la portabilidad sin sacrificar correccion estadistica.
            """
        ),
        code_cell(
            """
            from pathlib import Path
            import sys

            ROOT = Path.cwd()
            if not (ROOT / "src").exists() and (ROOT.parent / "src").exists():
                ROOT = ROOT.parent
            SRC = ROOT / "src"
            if str(SRC) not in sys.path:
                sys.path.append(str(SRC))
            """
        ),
        code_cell(
            """
            import numpy as np
            import pandas as pd
            import matplotlib.pyplot as plt
            import seaborn as sns

            from ibnr_project.config import build_default_config, build_default_scenarios, clone_config
            from ibnr_project.experiment import build_global_summary, run_experiment
            from ibnr_project.simulation import simulate_single_triangle
            from ibnr_project.methods import estimate_ibnr_all_methods
            from ibnr_project.evaluation import compute_method_metrics, rank_methods_within_scenario
            from ibnr_project.validation import run_validation_suite

            pd.set_option("display.max_columns", None)
            pd.set_option("display.float_format", lambda x: f"{x:,.4f}")
            sns.set_theme(style="whitegrid", context="talk")
            rng = np.random.default_rng(20260429)
            """
        ),
        markdown_cell(
            """
            ## Modulo 1. Configuracion experimental

            La configuracion separa los supuestos del resto del codigo. Esto es importante por dos razones:

            1. Permite documentar claramente los parametros del estudio.
            2. Facilita hacer analisis de sensibilidad sin reescribir funciones.

            En particular, usamos:

            - un triangulo de dimension `10 x 10`,
            - un patron acumulado decreciente en terminos incrementales,
            - una tendencia suave en `mu_i` para introducir heterogeneidad,
            - `phi = 0.30` como dispersion del escenario base,
            - 28 escenarios en total: 1 limpio y 27 contaminados.
            """
        ),
        code_cell(
            """
            config = build_default_config(random_seed=20260429, distribution="gamma")
            scenarios = build_default_scenarios()

            print("Numero de periodos:", config.n_periods)
            print("Patron acumulado:", config.development_cumulative)
            print("Patron incremental:", np.round(config.development_incremental, 4))
            print("Ultimates esperados por ano:", np.round(config.ultimate_means, 2))
            print("Numero de escenarios:", len(scenarios))
            pd.DataFrame([scenario.__dict__ for scenario in scenarios]).head()
            """
        ),
        markdown_cell(
            """
            ### Lectura estadistica del proceso generador

            Si `U_i = mu_i` representa el ultimate esperado del ano de ocurrencia `i` y `d_j` la proporcion incremental esperada del periodo `j`, entonces:

            \[
            E[X_{i,j}] = \mu_i d_j, \qquad Var(X_{i,j}) = \phi (\mu_i d_j)^2.
            \]

            Bajo distribucion Gamma, esta especificacion es conveniente porque mantiene positividad y asimetria, dos rasgos muy razonables para montos de siniestros. Ademas, al fijar la forma mediante `phi`, se controla la dispersion relativa en todos los periodos sin perder interpretabilidad.
            """
        ),
        markdown_cell(
            """
            ## Modulo 2. Validacion del simulador

            Antes de comparar metodos, comprobamos que el mecanismo de simulacion esta bien implementado. Este paso es clave en un proyecto de grado: si la simulacion es incorrecta, cualquier conclusion posterior queda debilitada.

            La validacion incluye cinco controles:

            - la media simulada debe aproximar la media teorica,
            - el acumulado debe ser monotono por fila,
            - la mascara observada debe tener exactamente `n(n+1)/2` celdas,
            - el IBNR real debe coincidir con la suma de la parte no observada,
            - en un triangulo sin ruido y sin contaminacion, todos los metodos deben recuperar el IBNR exacto.
            """
        ),
        code_cell(
            """
            validation_df = run_validation_suite(config)
            validation_df
            """
        ),
        markdown_cell(
            """
            ### Como comprobamos que las simulaciones estan bien

            Esta es una de las preguntas mas importantes del trabajo. La respuesta correcta no es solo "porque el codigo corre", sino porque pasa pruebas que conectan la implementacion con la teoria:

            - **Consistencia de medias**: si al promediar miles de triangulos las medias muestrales no se acercan a `mu_i d_j`, entonces el generador no representa el modelo definido.
            - **Consistencia estructural**: el acumulado debe crecer o mantenerse, nunca disminuir, porque es una suma parcial de incrementales positivos.
            - **Consistencia del IBNR real**: el benchmark de evaluacion se define con la parte futura verdadera del triangulo. Esa identidad debe verificarse exactamente.
            - **Prueba de caso determinista**: cuando eliminamos el ruido y usamos el triangulo esperado, los ratios de desarrollo son identicos entre anos. En ese contexto, cualquier metodo correcto debe reconstruir el IBNR sin error numerico.

            En otras palabras, validamos la simulacion tanto desde la **teoria probabilistica** como desde la **logica del algoritmo**.
            """
        ),
        markdown_cell(
            """
            ## Modulo 3. Inspeccion de una replica

            Antes de correr 1000 replicas por escenario, conviene inspeccionar una sola replica para entender visualmente el objeto de estudio.
            """
        ),
        code_cell(
            """
            example = simulate_single_triangle(config, scenarios[4], rng)

            fig, axes = plt.subplots(1, 3, figsize=(18, 5))
            sns.heatmap(example.incremental_full, ax=axes[0], cmap="YlOrBr")
            axes[0].set_title("Incremental completo")
            sns.heatmap(example.observed_cumulative, ax=axes[1], cmap="Blues")
            axes[1].set_title("Acumulado observado contaminado")
            mask_future = ~example.observed_mask
            sns.heatmap(np.where(mask_future, example.incremental_full, np.nan), ax=axes[2], cmap="Reds")
            axes[2].set_title("Zona futura = IBNR real")
            for ax in axes:
                ax.set_xlabel("Periodo de desarrollo")
                ax.set_ylabel("Ano de ocurrencia")
            plt.tight_layout()
            plt.show()

            print("IBNR real de la replica:", round(example.true_ibnr, 2))
            print("Celdas contaminadas:", example.contamination_metadata["selected_cells"][:10])
            """
        ),
        markdown_cell(
            """
            ## Modulo 4. Metodos de estimacion

            Los cuatro estimadores comparados son:

            - **Clasico**: usa el factor volumen-ponderado `sum C_{i,j+1} / sum C_{i,j}`.
            - **Mediana**: usa la mediana de los link ratios individuales; es muy resistente a observaciones extremas aisladas.
            - **Media truncada**: elimina el 10% inferior y superior antes de promediar; ofrece un compromiso entre robustez y eficiencia.
            - **Ponderado robusto**: usa pesos tipo Huber basados en la desviacion absoluta mediana. No elimina observaciones, pero reduce la influencia de las mas extremas.

            La mejora metodologica importante aqui es que la version ponderada no usa una constante fija en escala cruda, sino una escala robusta por periodo. Eso la hace mas defendible estadisticamente.
            """
        ),
        code_cell(
            """
            estimates = estimate_ibnr_all_methods(example.observed_cumulative, config)
            method_preview = pd.DataFrame(
                {
                    name: {
                        "estimated_ibnr": result.estimated_ibnr,
                        "first_factor": result.factors[0],
                        "last_factor": result.factors[-1],
                    }
                    for name, result in estimates.items()
                }
            ).T
            method_preview
            """
        ),
        markdown_cell(
            """
            ## Modulo 5. Motor Monte Carlo del experimento

            El motor Monte Carlo vive en `ibnr_project.experiment.run_experiment` y ejecuta la metodologia completa replica por replica. El diseno se mantiene fiel al planteamiento de investigacion:

            1. generar triangulo completo,
            2. definir IBNR real,
            3. contaminar solo lo observado,
            4. estimar con cada metodo,
            5. guardar resultados para analisis global.

            Para una entrega academica, es importante dejar el numero de replicas explicitamente parametrizado. Aqui fijamos `1000` como valor final y mantenemos la posibilidad de bajar el numero durante pruebas rapidas.
            """
        ),
        markdown_cell(
            """
            ## Modulo 6. Ejecucion principal

            Si estas en una primera revision del notebook, puedes correr con 200 replicas para inspeccion. Para el analisis final del proyecto de grado, la configuracion recomendada es de 1000 replicas por escenario.
            """
        ),
        code_cell(
            """
            N_REPLICAS = 1000
            results_df = run_experiment(config, scenarios, n_replicas=N_REPLICAS)
            results_df.head()
            """
        ),
        markdown_cell(
            """
            ## Modulo 7. Metricas de precision y estabilidad

            Las metricas se calculan por escenario y metodo. Ademas de las metricas planteadas inicialmente, incluyo `RMSE`, que suele ser mas interpretable que `MSE` porque vuelve a la escala original del IBNR.

            Tambien es importante interpretar `MAPE` con cuidado: aunque aqui el IBNR real siempre es positivo, en escenarios con IBNR pequeno un error relativo puede crecer mucho. Por eso conviene leer `MAPE` junto con `bias` y `RMSE`.
            """
        ),
        code_cell(
            """
            metrics_df = compute_method_metrics(results_df)
            metrics_df.head(12)
            """
        ),
        code_cell(
            """
            ranking_df = rank_methods_within_scenario(metrics_df, metric="rmse")
            ranking_df.head(12)
            """
        ),
        markdown_cell(
            """
            ## Modulo 8. Lecturas globales del desempeno

            A continuacion resumimos el comportamiento agregado por metodo. Esto no reemplaza el analisis por escenario, pero ayuda a detectar patrones generales.
            """
        ),
        code_cell(
            """
            global_summary = build_global_summary(metrics_df)
            global_summary
            """
        ),
        code_cell(
            """
            plt.figure(figsize=(12, 6))
            sns.barplot(data=global_summary, x="method", y="mean_rmse", hue="method", palette="crest", legend=False)
            plt.title("RMSE promedio por metodo")
            plt.xlabel("Metodo")
            plt.ylabel("RMSE promedio")
            plt.tight_layout()
            plt.show()
            """
        ),
        markdown_cell(
            """
            ## Modulo 9. Sensibilidad por escenario

            Para responder la pregunta de investigacion, necesitamos mirar como cambian las metricas cuando aumentan la proporcion, la magnitud y la ubicacion de la contaminacion.
            """
        ),
        code_cell(
            """
            selected_scenarios = [
                "base_sin_contaminacion",
                "p5_m2_random",
                "p5_m10_late",
                "p10_m5_random",
                "p10_m10_late",
                "p20_m5_early",
                "p20_m10_random",
            ]

            plt.figure(figsize=(16, 7))
            sns.boxplot(
                data=results_df.query("scenario in @selected_scenarios"),
                x="scenario",
                y="estimated_ibnr",
                hue="method",
            )
            plt.title("Distribucion del IBNR estimado en escenarios representativos")
            plt.xlabel("Escenario")
            plt.ylabel("IBNR estimado")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.show()
            """
        ),
        code_cell(
            """
            heatmap_data = (
                metrics_df.query("scenario != 'base_sin_contaminacion'")
                .pivot_table(index="scenario", columns="method", values="rmse")
                .sort_index()
            )

            plt.figure(figsize=(12, 10))
            sns.heatmap(heatmap_data, cmap="YlGnBu", annot=False)
            plt.title("RMSE por escenario y metodo")
            plt.xlabel("Metodo")
            plt.ylabel("Escenario")
            plt.tight_layout()
            plt.show()
            """
        ),
        markdown_cell(
            """
            ## Modulo 10. Respuesta analitica a las hipotesis

            Con la tabla siguiente puedes revisar, escenario por escenario, cual metodo minimiza el `RMSE`. Esta es una forma directa de evaluar las hipotesis H1-H5.
            """
        ),
        code_cell(
            """
            best_by_scenario = (
                ranking_df.loc[ranking_df["rank"] == 1, ["scenario", "method", "rmse", "mape", "bias"]]
                .sort_values("scenario")
                .reset_index(drop=True)
            )
            best_by_scenario.head(15)
            """
        ),
        markdown_cell(
            """
            ### Guia de interpretacion

            - Si el metodo clasico domina en el escenario base, eso respalda la idea de que la robustificacion tiene un costo cuando los datos estan limpios.
            - Si al aumentar proporcion o magnitud de contaminacion el clasico empeora en `RMSE` o `MAPE`, eso respalda la sensibilidad esperada del estimador tradicional.
            - Si la mediana mejora especialmente en escenarios con `magnitude = 10`, eso es coherente con su alta resistencia a outliers severos.
            - Si la media truncada mantiene buen `RMSE` en contaminacion moderada, se confirma su papel de compromiso entre robustez y eficiencia.
            - Si el ponderado robusto evita resultados extremos y mantiene baja variabilidad, eso apoya su valor como opcion flexible.
            """
        ),
        markdown_cell(
            """
            ## Modulo 11. Extension opcional: sensibilidad a colas mas pesadas

            La metodologia original propone usar Lognormal como analisis complementario. El siguiente bloque te deja listo para correr ese analisis sin reescribir el proyecto. No lo ejecuto por defecto porque duplica el tiempo total de simulacion, pero esta preparado para el capitulo de sensibilidad.
            """
        ),
        code_cell(
            """
            # config_lognormal = clone_config(config, distribution="lognormal", random_seed=20260430)
            # results_lognormal = run_experiment(config_lognormal, scenarios, n_replicas=500)
            # metrics_lognormal = compute_method_metrics(results_lognormal)
            # metrics_lognormal.head()
            """
        ),
        markdown_cell(
            """
            ## Conclusiones metodologicas

            Este notebook deja el estudio en una forma mas fuerte para un trabajo de grado porque:

            - separa claramente modelo, simulacion, estimacion, validacion y analisis;
            - documenta por que cada libreria y cada variante metodologica fueron elegidas;
            - incorpora pruebas que justifican que la simulacion esta bien implementada;
            - y produce un flujo reproducible, facil de versionar y directamente subible a GitHub.

            En un capitulo metodologico, eso es valioso porque no solo presentas resultados: demuestras control del experimento y criterio estadistico en el diseno.
            """
        ),
    ]

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    notebook = build_notebook()
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Notebook generated at {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
