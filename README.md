# Evaluación del método Chain-Ladder clásico y variantes robustas para estimar el IBNR

Este repositorio contiene el trabajo final sobre estimación del IBNR bajo datos contaminados. El estudio compara el método Chain-Ladder clásico con tres variantes robustas mediante simulación controlada, validación previa del simulador y análisis de resultados por escenario y por familias de escenarios.

## Objetivo del proyecto

Analizar en qué condiciones los métodos robustos mejoran la estimación del IBNR cuando la parte observada del triángulo contiene valores atípicos. Para ello se comparan cuatro métodos sobre los mismos escenarios simulados:

- Chain-Ladder clásico
- variante con mediana
- variante con media truncada
- variante ponderada robusta

## Estructura del repositorio

- `cuadernos/`
  - `estudio_ibnr_chain_ladder_robusto.ipynb`: cuaderno principal del estudio.
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
  - `generar_cuaderno.py`: limpia o normaliza los cuadernos.
  - `construir_recursos_presentacion.py`: genera las figuras usadas en la sustentación.
- `resultados/`: salidas del estudio en formato CSV.
- `presentacion/`
  - `sustentacion_ibnr_usta.tex`: presentación en Beamer.
  - `figuras/`: recursos gráficos usados en la sustentación.
- `recursos/`: material gráfico base del proyecto.

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

También se generan los análogos para la sensibilidad Lognormal.

## Recursos para la presentación

Para regenerar las figuras de la sustentación:

```bash
python guiones/construir_recursos_presentacion.py
```

Las imágenes se guardan en `presentacion/figuras/`.

## Cuadernos

Si deseas dejar un cuaderno limpio, sin salidas:

```bash
python guiones/generar_cuaderno.py --limpiar-salidas
```

## Nota metodológica

La simulación base utiliza una distribución Gamma y la sensibilidad se evalúa con una distribución Lognormal. La contaminación se introduce de manera positiva, multiplicativa y controlada solo en la región observada del triángulo, de modo que el IBNR real de la zona futura permanezca intacto y sirva como referencia para medir error, precisión y estabilidad.
