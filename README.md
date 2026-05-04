# Evaluacion del Chain-Ladder clasico y robusto bajo contaminacion

Este repositorio contiene una implementacion reproducible en Python para comparar el metodo Chain-Ladder clasico con tres variantes robustas en la estimacion del IBNR bajo escenarios simulados con valores atipicos controlados.

## Estructura

- `notebooks/ibnr_chain_ladder_robusto.ipynb`: notebook principal con explicacion metodologica, ejecucion del experimento y analisis.
- `scripts/generate_notebook.py`: generador del notebook en formato `.ipynb`.
- `scripts/run_experiment.py`: ejecucion por linea de comandos con exportacion de resultados a CSV.
- `src/ibnr_project/config.py`: configuraciones y escenarios.
- `src/ibnr_project/simulation.py`: generacion del triangulo, mascara observada y contaminacion.
- `src/ibnr_project/experiment.py`: motor Monte Carlo y resumen global.
- `src/ibnr_project/diagnostics.py`: diagnosticos de estructura, convergencia y dominancia de metodos.
- `src/ibnr_project/methods.py`: estimadores Chain-Ladder clasico y robustos.
- `src/ibnr_project/evaluation.py`: metricas de desempeno y tablas resumen.
- `src/ibnr_project/validation.py`: pruebas de coherencia estadistica y logica.

## Instalacion

```bash
pip install -r requirements.txt
```

## Ejecucion

1. Abre `notebooks/ibnr_chain_ladder_robusto.ipynb`.
2. Ejecuta las celdas en orden.
3. Si deseas una corrida rapida, reduce `N_REPLICAS` en la seccion de configuracion.

## Ejecucion por script

```bash
python scripts/run_experiment.py --replicas 1000 --distribution gamma
```

## Resultados exportados

La corrida principal exporta, entre otros, los siguientes archivos a `results/`:

- `metrics_<distribucion>_<replicas>rep.csv`
- `ranking_<distribucion>_<replicas>rep.csv`
- `comparisons_vs_classical_<distribucion>_<replicas>rep.csv`
- `method_dominance_<distribucion>_<replicas>rep.csv`
- `global_summary_<distribucion>_<replicas>rep.csv`

## Nota metodologica

La simulacion base usa `numpy.random.Generator.gamma` y `numpy.random.Generator.lognormal`. Se evita `scipy` como dependencia obligatoria para simplificar la reproducibilidad del repositorio sin sacrificar el modelo probabilistico propuesto.
