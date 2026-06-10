# Evaluación del método Chain-Ladder clásico y variantes robustas para estimar el IBNR

Este repositorio contiene el trabajo final sobre estimación del IBNR bajo datos contaminados. El estudio compara el método Chain-Ladder clásico con tres variantes robustas mediante simulación controlada, validación previa del simulador y análisis de resultados por escenario y por familias de escenarios.

## Objetivo del proyecto

Identificar en qué condiciones los métodos robustos mejoran la estimación del IBNR cuando la parte observada del triángulo contiene valores atípicos.

Los métodos comparados son:

- Chain-Ladder clásico
- Variante con mediana
- Variante con media truncada
- Variante ponderada robusta

## Estructura del repositorio

- `cuadernos/`
  - `estudio_ibnr_chain_ladder_robusto.ipynb`: cuaderno principal del estudio, con metodología, resultados, tablas y gráficas.
  - `validacion_simulador_ibnr.ipynb`: cuaderno de validación del simulador.
- `fuente/proyecto_ibnr/`
  - `configuracion.py`: configuración base y definición de escenarios.
  - `simulacion.py`: generación del triángulo incremental, acumulado y región observada.
  - `metodos.py`: implementación de los métodos comparados.
  - `experimento.py`: ejecución Monte Carlo del estudio.
  - `evaluacion.py`: métricas, comparaciones y resúmenes.
  - `diagnosticos.py`: diagnósticos complementarios y tablas de apoyo.
  - `validacion.py`: verificaciones previas del simulador.
- `guiones/`
  - `ejecutar_experimento.py`: corre el experimento y exporta resultados.
- `resultados/`: archivos CSV con las salidas del estudio.
- `requirements.txt`: dependencias principales del proyecto.

## Herramientas utilizadas

- Python 3
- Jupyter Notebook
- NumPy
- pandas
- matplotlib
- seaborn
- nbformat

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución principal

Para correr el caso base Gamma con 1000 réplicas:

```bash
python guiones/ejecutar_experimento.py --replicas 1000 --distribucion gamma
```

Para correr la sensibilidad Lognormal con 400 réplicas:

```bash
python guiones/ejecutar_experimento.py --replicas 400 --distribucion lognormal
```

## Resultados exportados

Cada corrida genera archivos como los siguientes en `resultados/`:

- `resultados_crudos_gamma_1000replicas.csv`
- `metricas_gamma_1000replicas.csv`
- `clasificacion_gamma_1000replicas.csv`
- `comparaciones_con_clasico_gamma_1000replicas.csv`
- `dominancia_metodos_gamma_1000replicas.csv`
- `resumen_global_gamma_1000replicas.csv`
- `resultados_familia_gamma_1000replicas.csv`
- `tabla_familias_rmse_gamma_1000replicas.csv`
- `tabla_familias_desviacion_gamma_1000replicas.csv`
- `resumen_desviacion_robusta_gamma_1000replicas.csv`
- `evaluacion_hipotesis_gamma_1000replicas.csv`

También se generan los archivos análogos para la sensibilidad Lognormal.

## Nota metodológica

La simulación base utiliza una distribución Gamma y la sensibilidad se evalúa con una distribución Lognormal. La contaminación se introduce de manera positiva, multiplicativa y controlada solo en la región observada del triángulo, de modo que el IBNR real de la zona futura permanezca intacto y sirva como referencia para medir error y estabilidad.

## Fuentes principales

### Base actuarial y estocástica

- Mack, T. (1993). *Distribution-Free Calculation of the Standard Error of Chain-Ladder Reserve Estimates*.
- England, P. D. y Verrall, R. J. (2002). *Stochastic Claims Reserving in General Insurance*.
- Wüthrich, M. V. y Merz, M. (2008). *Stochastic Claims Reserving Methods in Insurance*.
- Harnau, J. (2018). *Misspecification Tests for Log-Normal and Over-Dispersed Poisson Chain-Ladder Models*.

### Robustez y outliers

- Verdonck, T., Van Wouwe, M. y Dhaene, J. (2009). *Robustification of the Chain-Ladder Method*.
- Verdonck, T. y Debruyne, M. (2011). *The Influence of Individual Claims on the Chain-Ladder Estimates*.
- Pitselis, G., Grigoriadou, V. y Badounas, I. (2015). *Robust Loss Reserving in a Log-Linear Model*.
- Peremans, K., Van Aelst, S. y Verdonck, T. (2018). *A Robust General Multivariate Chain Ladder Method*.
- Avanzi, B., Richman, R. y Wong, B. (2023). *Detection and Treatment of Outliers for Multivariate Robust Loss Reserving*.
- Avanzi, B., Lavender, A., Taylor, G. y Wong, B. (2024). *On the Impact of Outliers in Loss Reserving*.
