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
            # Evaluación comparativa del método Chain-Ladder clásico y sus versiones robustas en la estimación del IBNR bajo escenarios controlados de valores atípicos

            Este cuaderno documenta e implementa un estudio de simulación estadística orientado a comparar el desempeño del método Chain-Ladder clásico con tres variantes robustas en la estimación del IBNR. El análisis se desarrolla bajo un diseño factorial controlado, con verdad conocida por construcción y con procedimientos explícitos de validación interna, de manera que la comparación entre métodos no dependa únicamente de resultados numéricos, sino también de la coherencia estadística del proceso generador de datos y de la trazabilidad del algoritmo de estimación.
            """
        ),
        markdown_cell(
            """
            ## Planteamiento del estudio

            **Pregunta de investigación.** ¿Cuál es el impacto de la presencia de valores atípicos en el desempeño del método Chain-Ladder clásico y de sus versiones robustas en la estimación del IBNR, y bajo qué condiciones los métodos robustos ofrecen mejoras en términos de precisión y estabilidad?

            **Objetivo general.** Evaluar el comportamiento del método Chain-Ladder clásico y de sus versiones robustas en la estimación del IBNR, mediante simulación de triángulos de desarrollo bajo escenarios controlados de contaminación, con el fin de analizar su efecto sobre la precisión y la estabilidad de las estimaciones.

            **Hipótesis de trabajo.**

            - H1. El error del método clásico aumenta a medida que crecen la proporción y la magnitud de la contaminación.
            - H2. Los métodos robustos exhiben menor variabilidad que el método clásico en escenarios contaminados.
            - H3. La versión basada en la mediana presenta ventajas en escenarios con outliers severos y poco numerosos.
            - H4. La media truncada ofrece un equilibrio favorable entre robustez y eficiencia bajo contaminación moderada.
            - H5. La variante ponderada presenta un comportamiento intermedio y estable cuando la contaminación es frecuente y de magnitud media.
            """
        ),
        markdown_cell(
            """
            ## Fundamento teórico y criterio de diseño

            La literatura actuarial establece que el Chain-Ladder clásico es altamente sensible a observaciones atípicas. Mack (1993) formaliza el marco estocástico del método y muestra cómo cuantificar el error de predicción. England y Verrall (2002) destacan que la principal ventaja de los modelos estocásticos de reserving es la disponibilidad de medidas explícitas de precisión. Verdonck et al. (2009) y Verdonck y Debruyne (2011) muestran, desde la perspectiva de robustez e influencia, que incluso una sola observación extrema puede desplazar de forma importante la reserva estimada. Más recientemente, Avanzi et al. (2024) profundizan en la sensibilidad posicional del reserving frente a outliers y documentan que las celdas cercanas a la frontera observada pueden ejercer una influencia particularmente alta.

            A partir de ese marco, el diseño implementado adopta una lógica deliberadamente comparativa: el IBNR real se conoce por construcción, la contaminación se introduce únicamente sobre la región observable y los métodos compiten sobre los mismos triángulos simulados. Esta estructura produce comparaciones pareadas, reduce el ruido Monte Carlo en las diferencias entre métodos y permite una lectura más sólida de la evidencia empírica.
            """
        ),
        markdown_cell(
            """
            ## Refinamientos metodológicos incorporados

            La implementación final introduce varios refinamientos respecto de una formulación básica del experimento:

            1. **Diseño factorial completo.** Se consideran 28 escenarios: un escenario base sin contaminación y 27 combinaciones de proporción, magnitud y ubicación. Esto evita que las conclusiones dependan de unos pocos escenarios ilustrativos.
            2. **Heterogeneidad entre años de ocurrencia.** Los valores esperados últimos no son constantes, sino que siguen una tendencia suave. Esta decisión reduce el carácter artificial del experimento y reproduce mejor una cartera con niveles distintos de siniestralidad.
            3. **Ubicación tardía definida sobre la frontera observada.** La contaminación temprana y tardía se define ahora en términos relativos a las celdas observadas de cada fila. Esta decisión es más fiel a la geometría triangular del problema de reserving que una definición basada en columnas globales.
            4. **Ponderación robusta escalada por MAD.** La versión ponderada utiliza una escala robusta por periodo de desarrollo, de modo que el umbral de ponderación no dependa de la dispersión absoluta de cada conjunto de ratios.
            5. **Evaluación pareada frente al método clásico.** Además de las métricas agregadas por escenario, se calculan diferencias pareadas de error cuadrático y de error porcentual absoluto respecto del método clásico, con intervalos de confianza aproximados.
            6. **Justificación empírica del número de réplicas.** La estabilidad de las métricas se evalúa mediante trayectorias acumuladas, lo que permite verificar si 1000 réplicas son suficientes para estabilizar el experimento.
            7. **Sensibilidad a colas más pesadas.** Se incluye una extensión con distribución Lognormal para verificar si los patrones observados bajo Gamma se conservan cuando la distribución subyacente presenta colas más pesadas.
            """
        ),
        markdown_cell(
            """
            ## Entorno computacional y reproducibilidad

            La implementación se apoya en un conjunto reducido de librerías con funciones bien delimitadas:

            - `numpy`: simulación aleatoria, álgebra matricial y operaciones vectorizadas.
            - `pandas`: organización tabular de réplicas, escenarios y métricas.
            - `matplotlib` y `seaborn`: visualización de resultados.
            - `pathlib`: manejo portable de rutas del repositorio.

            El código reutilizable se encuentra en `src/ibnr_project`, mientras que este cuaderno concentra la narrativa metodológica, la ejecución de los experimentos y la discusión de resultados. La semilla aleatoria se fija de forma explícita para garantizar reproducibilidad.
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

            OUTPUT_DIR = ROOT / "results"
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            """
        ),
        code_cell(
            """
            import numpy as np
            import pandas as pd
            import matplotlib.pyplot as plt
            import seaborn as sns
            from IPython.display import display

            from ibnr_project.config import build_default_config, build_default_scenarios, clone_config
            from ibnr_project.diagnostics import (
                build_link_ratio_count_table,
                compute_running_statistics,
                summarize_method_dominance,
            )
            from ibnr_project.evaluation import (
                compare_methods_to_baseline,
                compute_method_metrics,
                rank_methods_within_scenario,
            )
            from ibnr_project.experiment import build_global_summary, run_experiment
            from ibnr_project.methods import estimate_ibnr_all_methods
            from ibnr_project.simulation import observed_mask, simulate_single_triangle
            from ibnr_project.validation import run_validation_suite

            pd.set_option("display.max_columns", None)
            pd.set_option("display.float_format", lambda x: f"{x:,.4f}")
            sns.set_theme(style="whitegrid", context="notebook")
            plt.rcParams["figure.dpi"] = 120
            plt.rcParams["axes.titleweight"] = "bold"
            """
        ),
        markdown_cell(
            """
            ## Configuración experimental

            El experimento se implementa sobre triángulos de dimensión `10 × 10`. Los montos incrementales se generan con esperanza `E[X_{i,j}] = μ_i d_j` y varianza `Var(X_{i,j}) = ϕ (μ_i d_j)^2`, en concordancia con la formulación propuesta en la metodología. El patrón acumulado se fija exógenamente y de él se derivan las proporciones incrementales esperadas.
            """
        ),
        code_cell(
            """
            SEED = 20260503
            config = build_default_config(random_seed=SEED, distribution="gamma")
            scenarios = build_default_scenarios()
            mask = observed_mask(config.n_periods)

            scenario_df = pd.DataFrame([scenario.__dict__ for scenario in scenarios])
            scenario_df
            """
        ),
        code_cell(
            """
            parameter_overview = pd.DataFrame(
                {
                    "periodo_desarrollo": np.arange(1, config.n_periods + 1),
                    "proporcion_acumulada": config.development_cumulative,
                    "proporcion_incremental": config.development_incremental,
                }
            )

            print("Semilla:", config.random_seed)
            print("Distribución base:", config.distribution)
            print("Dispersión phi:", config.dispersion_phi)
            print("Ultimates esperados por año de ocurrencia:", np.round(config.ultimate_means, 2))
            parameter_overview
            """
        ),
        markdown_cell(
            """
            ## Diagnóstico estructural de los ratios de desarrollo

            Un aspecto importante del problema es que el número de ratios individuales disponibles disminuye con el desarrollo. Esto tiene consecuencias directas sobre la estabilidad de las variantes robustas: en los periodos tardíos hay menos observaciones, de modo que la mediana, la media truncada y las ponderaciones se calculan sobre tamaños muestrales pequeños.
            """
        ),
        code_cell(
            """
            ratio_count_df = build_link_ratio_count_table(mask)
            ratio_count_df
            """
        ),
        code_cell(
            """
            plt.figure(figsize=(8, 4))
            sns.barplot(data=ratio_count_df, x="development_period", y="n_individual_ratios", color="#35608d")
            plt.title("Número de ratios individuales por periodo de desarrollo")
            plt.xlabel("Periodo de desarrollo j")
            plt.ylabel("Número de ratios C(i,j+1) / C(i,j)")
            plt.tight_layout()
            plt.show()
            """
        ),
        markdown_cell(
            """
            ## Validación del simulador

            Antes de comparar métodos se valida el proceso generador de datos. La validación interna cubre cinco dimensiones: consistencia de medias, coherencia del acumulado, definición correcta del IBNR real, lógica de contaminación y recuperación exacta en un caso determinista sin ruido.
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
            Las pruebas anteriores tienen una función metodológica clara. La primera comprueba que la simulación reproduce la esperanza teórica. La segunda verifica que la transformación de incremental a acumulado no introduce inconsistencias. La tercera controla la identidad entre la región no observada y el IBNR real. La cuarta comprueba que la contaminación se aplica únicamente sobre la región observable. La quinta confirma que, en ausencia de ruido, los métodos recuperan el valor correcto del IBNR.
            """
        ),
        markdown_cell(
            """
            ## Inspección de una réplica

            La inspección de una réplica individual permite visualizar simultáneamente el triángulo incremental completo, el triángulo acumulado observado después de la contaminación y la región futura que define el IBNR real.
            """
        ),
        code_cell(
            """
            rng_example = np.random.default_rng(SEED)
            example = simulate_single_triangle(config, scenarios[4], rng_example)

            fig, axes = plt.subplots(1, 3, figsize=(18, 5))
            sns.heatmap(example.incremental_full, ax=axes[0], cmap="YlOrBr")
            axes[0].set_title("Triángulo incremental completo")
            sns.heatmap(example.observed_cumulative, ax=axes[1], cmap="Blues")
            axes[1].set_title("Triángulo acumulado observado contaminado")
            sns.heatmap(np.where(~example.observed_mask, example.incremental_full, np.nan), ax=axes[2], cmap="Reds")
            axes[2].set_title("Región futura: IBNR real")
            for ax in axes:
                ax.set_xlabel("Periodo de desarrollo")
                ax.set_ylabel("Año de ocurrencia")
            plt.tight_layout()
            plt.show()

            print("IBNR real de la réplica:", round(example.true_ibnr, 2))
            print("Primeras celdas contaminadas:", example.contamination_metadata["selected_cells"][:10])
            """
        ),
        markdown_cell(
            """
            ## Métodos de estimación

            Se comparan cuatro estimadores:

            - **Clásico**: factor volumen-ponderado.
            - **Mediana**: mediana de los ratios individuales.
            - **Media truncada**: promedio después de eliminar el 10% inferior y superior de los ratios.
            - **Ponderado robusto**: promedio ponderado mediante pesos tipo Huber, con escala robusta por MAD.

            La literatura de robustez sugiere que la media posee función de influencia no acotada, mientras que estimadores basados en mediana o ponderaciones robustas pueden limitar el efecto de observaciones extremas. En este estudio esas ideas se trasladan al cálculo de factores de desarrollo.
            """
        ),
        code_cell(
            """
            estimate_preview = estimate_ibnr_all_methods(example.observed_cumulative, config)
            method_preview = pd.DataFrame(
                {
                    name: {
                        "ibnr_estimado": result.estimated_ibnr,
                        "primer_factor": result.factors[0],
                        "ultimo_factor": result.factors[-1],
                    }
                    for name, result in estimate_preview.items()
                }
            ).T
            method_preview
            """
        ),
        markdown_cell(
            """
            ## Diseño Monte Carlo y estructura pareada

            Para cada escenario se generan `N` triángulos independientes y, sobre cada triángulo, se calculan las cuatro estimaciones del IBNR. Este diseño implica que las comparaciones entre métodos se realizan sobre la misma réplica. En consecuencia, las diferencias de error entre métodos son comparaciones pareadas, más informativas que una comparación entre muestras independientes.
            """
        ),
        code_cell(
            """
            N_REPLICAS = 1000
            results_df = run_experiment(config, scenarios, n_replicas=N_REPLICAS)

            scenario_meta = (
                results_df.groupby("scenario", as_index=False)
                .agg(
                    contamination_proportion=("contamination_proportion", "first"),
                    contamination_magnitude=("contamination_magnitude", "first"),
                    contamination_location=("contamination_location", "first"),
                )
                .sort_values("scenario")
                .reset_index(drop=True)
            )

            results_df.head()
            """
        ),
        markdown_cell(
            """
            ## Métricas principales

            El desempeño se resume mediante sesgo, MSE, RMSE, MAE, MAPE, error porcentual medio y desviación estándar de las estimaciones. Para las métricas basadas en promedios también se reporta una aproximación al error estándar Monte Carlo y un intervalo de confianza normal aproximado. El RMSE permanece como métrica principal de comparación, por su lectura directa en la escala del IBNR.
            """
        ),
        code_cell(
            """
            metrics_df = compute_method_metrics(results_df).merge(scenario_meta, on="scenario", how="left")
            metrics_df.head(12)
            """
        ),
        code_cell(
            """
            ranking_df = rank_methods_within_scenario(metrics_df, metric="rmse")
            dominance_df = summarize_method_dominance(ranking_df)
            global_summary = build_global_summary(metrics_df)

            print("Método ganador por número de escenarios:")
            display(dominance_df)
            print("Resumen global por método:")
            display(global_summary)
            """
        ),
        code_cell(
            """
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))

            sns.barplot(data=global_summary, x="method", y="mean_rmse", hue="method", palette="crest", legend=False, ax=axes[0])
            axes[0].set_title("RMSE promedio por método")
            axes[0].set_xlabel("Método")
            axes[0].set_ylabel("RMSE promedio")

            heatmap_data = (
                metrics_df.pivot_table(index="scenario", columns="method", values="rmse")
                .reindex(sorted(metrics_df["scenario"].unique()))
            )
            sns.heatmap(heatmap_data, cmap="YlGnBu", ax=axes[1], cbar_kws={"label": "RMSE"})
            axes[1].set_title("RMSE por escenario y método")
            axes[1].set_xlabel("Método")
            axes[1].set_ylabel("Escenario")

            plt.tight_layout()
            plt.show()
            """
        ),
        markdown_cell(
            """
            ## Comparaciones pareadas frente al método clásico

            La evaluación anterior resume el desempeño medio por escenario. Sin embargo, dado que los métodos se aplican sobre las mismas réplicas, es posible comparar sus errores en forma pareada. Una diferencia negativa en `delta_mse_mean` indica que el método robusto presenta menor error cuadrático medio que el método clásico en el mismo conjunto de réplicas.
            """
        ),
        code_cell(
            """
            comparisons_df = compare_methods_to_baseline(results_df, baseline="classical")
            comparisons_df = comparisons_df.merge(scenario_meta, on="scenario", how="left")
            comparisons_df.head(12)
            """
        ),
        code_cell(
            """
            comparison_summary = (
                comparisons_df.groupby("method", as_index=False)
                .agg(
                    escenarios_con_mejora_mse=("delta_mse_improves", "sum"),
                    escenarios_con_deterioro_mse=("delta_mse_worsens", "sum"),
                    escenarios_con_mejora_mape=("delta_mape_improves", "sum"),
                    delta_mse_promedio=("delta_mse_mean", "mean"),
                    delta_mape_promedio=("delta_mape_mean", "mean"),
                )
                .sort_values("escenarios_con_mejora_mse", ascending=False)
            )
            comparison_summary
            """
        ),
        markdown_cell(
            """
            ## Sensibilidad por escenario representativo

            La combinación de gráficos de distribución y tablas de ranking permite identificar de forma concreta dónde se produce el deterioro del método clásico y bajo qué tipos de contaminación aparecen ventajas robustas.
            """
        ),
        code_cell(
            """
            selected_scenarios = [
                "base_sin_contaminacion",
                "p5_m2_random",
                "p5_m10_late",
                "p10_m5_random",
                "p10_m10_early",
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
            plt.title("Distribución del IBNR estimado en escenarios seleccionados")
            plt.xlabel("Escenario")
            plt.ylabel("IBNR estimado")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.show()
            """
        ),
        markdown_cell(
            """
            ## Justificación empírica del número de réplicas

            El número de réplicas no se adopta únicamente por convención. La trayectoria acumulada del RMSE muestra si la estimación del desempeño se estabiliza conforme aumenta el tamaño de la simulación. La evidencia siguiente se presenta para dos situaciones contrastantes: el escenario base con el método clásico y un escenario severamente contaminado con la mediana.
            """
        ),
        code_cell(
            """
            running_base = compute_running_statistics(results_df, "base_sin_contaminacion", "classical")
            running_severe = compute_running_statistics(results_df, "p20_m10_random", "median")

            fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
            sns.lineplot(data=running_base, x="replica", y="running_rmse", color="#1b4965", ax=axes[0])
            axes[0].set_title("Convergencia del RMSE acumulado | Escenario base - Método clásico")
            axes[0].set_xlabel("Número de réplicas")
            axes[0].set_ylabel("RMSE acumulado")

            sns.lineplot(data=running_severe, x="replica", y="running_rmse", color="#9c2f2f", ax=axes[1])
            axes[1].set_title("Convergencia del RMSE acumulado | Escenario p20_m10_random - Mediana")
            axes[1].set_xlabel("Número de réplicas")
            axes[1].set_ylabel("RMSE acumulado")

            plt.tight_layout()
            plt.show()
            """
        ),
        markdown_cell(
            """
            ## Evaluación de hipótesis

            La evaluación de las hipótesis se apoya en tres fuentes de evidencia: métricas globales, rankings por escenario y comparaciones pareadas frente al método clásico.
            """
        ),
        code_cell(
            """
            classical_metrics = metrics_df.query("scenario != 'base_sin_contaminacion' and method == 'classical'").copy()
            classical_metrics["log_magnitude"] = np.log(classical_metrics["contamination_magnitude"])
            correlation_table = classical_metrics[
                ["contamination_proportion", "contamination_magnitude", "log_magnitude", "rmse", "mape", "sd_estimates"]
            ].corr(method="spearman")

            support_h2 = (
                metrics_df.query("scenario != 'base_sin_contaminacion'")
                .pivot(index="scenario", columns="method", values="sd_estimates")
                .assign(
                    median_less_than_classical=lambda df: df["median"] < df["classical"],
                    trimmed_less_than_classical=lambda df: df["trimmed"] < df["classical"],
                    weighted_less_than_classical=lambda df: df["weighted"] < df["classical"],
                )
            )

            severe_rare = ranking_df.query(
                "contamination_proportion == 0.05 and contamination_magnitude == 10 and rank == 1"
            )
            moderate_subset = ranking_df.query(
                "contamination_proportion in [0.05, 0.10] and contamination_magnitude in [2.0, 5.0]"
            )
            frequent_medium = ranking_df.query(
                "contamination_proportion == 0.20 and contamination_magnitude == 5.0"
            )
            trimmed_rank_moderate = moderate_subset.loc[moderate_subset["method"] == "trimmed", "rank"].mean()
            weighted_rank_frequent_medium = frequent_medium.loc[frequent_medium["method"] == "weighted", "rank"].mean()
            severe_rare_winner = severe_rare["method"].value_counts().idxmax()
            severe_rare_median_share = severe_rare["method"].eq("median").mean()

            hypothesis_table = pd.DataFrame(
                [
                    {
                        "hipotesis": "H1",
                        "evidencia_principal": (
                            f"Correlación de Spearman del RMSE clásico con proporción = "
                            f"{correlation_table.loc['contamination_proportion', 'rmse']:.3f}; "
                            f"con magnitud = {correlation_table.loc['contamination_magnitude', 'rmse']:.3f}."
                        ),
                        "dictamen": "Apoyada" if (
                            correlation_table.loc["contamination_proportion", "rmse"] > 0
                            and correlation_table.loc["contamination_magnitude", "rmse"] > 0
                        ) else "No concluyente",
                    },
                    {
                        "hipotesis": "H2",
                        "evidencia_principal": (
                            f"La mediana presenta menor desviación estándar que el clásico en "
                            f"{int(support_h2['median_less_than_classical'].sum())} de {len(support_h2)} escenarios contaminados."
                        ),
                        "dictamen": "Parcialmente apoyada",
                    },
                    {
                        "hipotesis": "H3",
                        "evidencia_principal": (
                            f"En escenarios con proporción 5% y magnitud 10, el método ganador es "
                            f"{severe_rare_winner}."
                        ),
                        "dictamen": "Apoyada" if severe_rare_median_share >= 2 / 3 else "No apoyada",
                    },
                    {
                        "hipotesis": "H4",
                        "evidencia_principal": (
                            f"Rango promedio de la media truncada en contaminación moderada: "
                            f"{trimmed_rank_moderate:.2f}."
                        ),
                        "dictamen": "No apoyada" if trimmed_rank_moderate > 2 else "Parcialmente apoyada",
                    },
                    {
                        "hipotesis": "H5",
                        "evidencia_principal": (
                            f"Rango promedio del método ponderado en escenarios con 20% de contaminación y magnitud 5: "
                            f"{weighted_rank_frequent_medium:.2f}."
                        ),
                        "dictamen": "No apoyada" if weighted_rank_frequent_medium > 2 else "Parcialmente apoyada",
                    },
                ]
            )

            print("Correlaciones de Spearman para el método clásico en escenarios contaminados:")
            display(correlation_table)
            print("Evaluación sintética de hipótesis:")
            display(hypothesis_table)
            """
        ),
        markdown_cell(
            """
            La evidencia obtenida muestra un patrón robusto. En datos limpios o con contaminación leve, el método clásico conserva ventajas de eficiencia. Sin embargo, conforme aumentan la magnitud y la frecuencia de la contaminación, la mediana se convierte en la opción más estable y precisa. En esta implementación, la media truncada no confirma la hipótesis de equilibrio robustez-eficiencia y la versión ponderada no domina de forma sistemática. Ese resultado no invalida el diseño; por el contrario, aporta una conclusión empírica relevante: no toda robustificación heurística resulta efectiva en triángulos con tamaños muestrales decrecientes por periodo de desarrollo.
            """
        ),
        markdown_cell(
            """
            ## Sensibilidad a colas más pesadas

            Como extensión prevista en la metodología, se repite el experimento bajo una distribución Lognormal. Con el fin de mantener un tiempo de ejecución razonable dentro del cuaderno, esta sensibilidad se evalúa con 400 réplicas por escenario. Su propósito es verificar si el orden relativo entre métodos cambia cuando la generación de incrementales presenta colas más pesadas.
            """
        ),
        code_cell(
            """
            N_REPLICAS_LOGNORMAL = 400
            config_lognormal = clone_config(config, distribution="lognormal", random_seed=SEED + 1)
            results_lognormal = run_experiment(config_lognormal, scenarios, n_replicas=N_REPLICAS_LOGNORMAL)
            metrics_lognormal = compute_method_metrics(results_lognormal)
            ranking_lognormal = rank_methods_within_scenario(metrics_lognormal, metric="rmse")
            global_summary_lognormal = build_global_summary(metrics_lognormal)
            dominance_lognormal = summarize_method_dominance(ranking_lognormal)

            print("Resumen global bajo Lognormal:")
            display(global_summary_lognormal)
            print("Dominancia por escenarios bajo Lognormal:")
            display(dominance_lognormal)
            """
        ),
        markdown_cell(
            """
            ## Exportación de resultados

            Con fines de trazabilidad y documentación del repositorio, los principales resultados se exportan a la carpeta `results`. Esto permite desacoplar la ejecución del cuaderno del uso posterior de tablas y figuras en el documento escrito.
            """
        ),
        code_cell(
            """
            export_map = {
                "metrics_gamma_1000rep.csv": metrics_df,
                "ranking_gamma_1000rep.csv": ranking_df,
                "comparisons_vs_classical_gamma_1000rep.csv": comparisons_df,
                "global_summary_gamma_1000rep.csv": global_summary,
                "method_dominance_gamma_1000rep.csv": dominance_df,
                "hypothesis_assessment_gamma_1000rep.csv": hypothesis_table,
                "global_summary_lognormal_400rep.csv": global_summary_lognormal,
                "method_dominance_lognormal_400rep.csv": dominance_lognormal,
            }

            exported = []
            skipped = []
            for filename, dataframe in export_map.items():
                output_path = OUTPUT_DIR / filename
                try:
                    dataframe.to_csv(output_path, index=False)
                    exported.append(filename)
                except PermissionError:
                    skipped.append(filename)

            print("Archivos exportados correctamente:")
            for filename in exported:
                print("-", filename)
            if skipped:
                print("Archivos no sobrescritos por encontrarse en uso:")
                for filename in skipped:
                    print("-", filename)
            """
        ),
        markdown_cell(
            """
            ## Limitaciones y alcance

            El estudio aísla de forma deliberada el efecto de los valores atípicos sobre la estimación del IBNR. En consecuencia, no incorpora factores de cola, efectos calendario, dependencia entre años de ocurrencia, ajustes de exposición ni un modelo estocástico completo del tipo Mack o bootstrap para todas las variantes robustas. Estas omisiones son coherentes con el objetivo principal del trabajo, que consiste en comparar sensibilidad, precisión y estabilidad bajo contaminación controlada. No obstante, constituyen líneas naturales de extensión hacia un trabajo aplicado más amplio.
            """
        ),
        markdown_cell(
            """
            ## Referencias

            - Mack, T. (1993). *Distribution-free Calculation of the Standard Error of Chain Ladder Reserve Estimates*. ASTIN Bulletin. [Cambridge](https://www.cambridge.org/core/journals/astin-bulletin-journal-of-the-iaa/article/distributionfree-calculation-of-the-standard-error-of-chain-ladder-reserve-estimates/E8D207F9A4DCE30300A76780FE510437)
            - England, P. D., y Verrall, R. J. (2002). *Stochastic Claims Reserving in General Insurance*. British Actuarial Journal. [Cambridge](https://www.cambridge.org/core/journals/british-actuarial-journal/article/stochastic-claims-reserving-in-general-insurance/60026990B6A88E8A6DDEECABD6506C65)
            - Verdonck, T., Van Wouwe, M., y Dhaene, J. (2009). *A Robustification of the Chain-Ladder Method*. North American Actuarial Journal. [DOI](https://doi.org/10.1080/10920277.2009.10597555)
            - Verdonck, T., y Debruyne, M. (2011). *The influence of individual claims on the chain-ladder estimates: Analysis and diagnostic tool*. Insurance: Mathematics and Economics. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167668710001071)
            - Avanzi, B., Lavender, M., Taylor, G., y Wong, B. (2024). *On the impact of outliers in loss reserving*. European Actuarial Journal. [Springer](https://link.springer.com/article/10.1007/s13385-023-00356-2)
            - Avanzi, B., Lavender, M., Taylor, G., y Wong, B. (2023). *Detection and treatment of outliers for multivariate robust loss reserving*. Annals of Actuarial Science. [DOI](https://doi.org/10.1017/S1748499523000155)
            - `chainladder` para Python, documentación oficial de `MackChainladder`. [Read the Docs](https://chainladder-python.readthedocs.io/en/stable/library/generated/chainladder.MackChainladder.html)
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
