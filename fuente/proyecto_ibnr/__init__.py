from .configuracion import (
    ConfiguracionSimulacion,
    EscenarioContaminacion,
    clonar_configuracion,
    construir_configuracion_base,
    construir_escenarios_base,
)
from .diagnosticos import (
    calcular_estadisticas_acumuladas,
    construir_tabla_conteo_ratios,
    resumir_dominancia_metodos,
)
from .evaluacion import (
    ETIQUETAS_METODOS,
    calcular_metricas_metodos,
    clasificar_metodos_en_escenario,
    comparar_metodos_con_base,
    evaluar_hipotesis_principal,
    resumir_resultados_familia,
    resumir_resultados_por_escenario,
)
from .experimento import construir_resumen_global, ejecutar_experimento
from .metodos import estimar_ibnr_todos_metodos
from .simulacion import (
    calcular_ibnr_real,
    contaminar_triangulo_incremental,
    construir_triangulo_observado,
    generar_triangulo_incremental,
    incremental_a_acumulado,
    mascara_observada,
    simular_un_triangulo,
)
from .validacion import ejecutar_validacion_completa

__all__ = [
    "ConfiguracionSimulacion",
    "EscenarioContaminacion",
    "clonar_configuracion",
    "construir_configuracion_base",
    "construir_escenarios_base",
    "calcular_estadisticas_acumuladas",
    "construir_tabla_conteo_ratios",
    "resumir_dominancia_metodos",
    "ETIQUETAS_METODOS",
    "calcular_metricas_metodos",
    "clasificar_metodos_en_escenario",
    "comparar_metodos_con_base",
    "evaluar_hipotesis_principal",
    "resumir_resultados_familia",
    "resumir_resultados_por_escenario",
    "construir_resumen_global",
    "ejecutar_experimento",
    "estimar_ibnr_todos_metodos",
    "calcular_ibnr_real",
    "contaminar_triangulo_incremental",
    "construir_triangulo_observado",
    "generar_triangulo_incremental",
    "incremental_a_acumulado",
    "mascara_observada",
    "simular_un_triangulo",
    "ejecutar_validacion_completa",
]
