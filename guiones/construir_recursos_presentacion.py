from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

RAIZ = Path(__file__).resolve().parents[1]
FUENTE = RAIZ / "fuente"
if str(FUENTE) not in sys.path:
    sys.path.append(str(FUENTE))

from proyecto_ibnr.evaluacion import resumir_resultados_familia

DIRECTORIO_RESULTADOS = RAIZ / "resultados"
DIRECTORIO_FIGURAS = RAIZ / "presentacion" / "figuras"
DIRECTORIO_FIGURAS.mkdir(parents=True, exist_ok=True)

AZUL_PRINCIPAL = "#20384F"
AZUL_SECUNDARIO = "#5C6F82"
GRIS_OSCURO = "#4B5563"
GRIS_SUAVE = "#D9E2EC"
FONDO_SUAVE = "#F7F9FB"
COLOR_MEDIANA = "#1E6A86"
COLOR_CLASICO = "#8E96A1"
COLOR_PONDERADO = "#67808F"
COLOR_TRUNCADA = "#C8CED6"
COLOR_OUTLIER = "#CC7A5C"


def leer_csv(nombre_archivo: str) -> pd.DataFrame:
    return pd.read_csv(DIRECTORIO_RESULTADOS / nombre_archivo)


def _texto_victorias(fila: pd.Series) -> str:
    return f"{fila['metodo_con_mas_victorias']} ({fila['frecuencia_ganadora']})"


def guardar_triangulo_ibnr() -> None:
    figura, eje = plt.subplots(figsize=(12, 7), dpi=150)
    eje.set_xlim(0, 12)
    eje.set_ylim(0, 10)
    eje.axis("off")

    for fila in range(10):
        for columna in range(10):
            x = columna + 1
            y = 9 - fila
            if columna <= 9 - fila:
                color = "#D9EEF6"
                if (fila, columna) in [(2, 2), (5, 1)]:
                    color = "#F3C7B8"
                eje.add_patch(Rectangle((x, y), 0.9, 0.9, facecolor=color, edgecolor="white"))
            else:
                eje.add_patch(Rectangle((x, y), 0.9, 0.9, facecolor="#E8EAED", edgecolor="white"))

    eje.text(2.2, 9.5, "Información\nobservada", color=AZUL_PRINCIPAL, fontsize=17, fontweight="bold", ha="left", va="center")
    eje.text(8.4, 4.4, "Zona futura\nque se estima", color=GRIS_OSCURO, fontsize=17, fontweight="bold", ha="center", va="center")
    eje.text(3.3, 6.1, "Celdas con\noutliers", color=COLOR_OUTLIER, fontsize=14, fontweight="bold", ha="left")
    eje.annotate("", xy=(3.45, 6.95), xytext=(4.1, 6.35), arrowprops=dict(arrowstyle="->", color=COLOR_OUTLIER, lw=2))
    eje.annotate("", xy=(2.45, 3.95), xytext=(3.2, 5.7), arrowprops=dict(arrowstyle="->", color=COLOR_OUTLIER, lw=2))
    eje.text(1.0, 0.55, "Año de ocurrencia", fontsize=13, color=GRIS_OSCURO)
    eje.text(9.9, 9.55, "Desarrollo", fontsize=13, color=GRIS_OSCURO, ha="right")
    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "triangulo_ibnr.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_linea_tiempo() -> None:
    figura, eje = plt.subplots(figsize=(14, 5), dpi=150)
    eje.set_xlim(0, 10)
    eje.set_ylim(0, 1)
    eje.axis("off")
    eje.plot([0.8, 9.2], [0.5, 0.5], color=AZUL_SECUNDARIO, lw=3)

    puntos = [1.1, 2.8, 4.6, 6.4, 8.3]
    desplazamientos = [0.73, 0.28, 0.73, 0.28, 0.73]
    etiquetas = [
        ("1993", "Mack", "Base estocástica\ndel Chain-Ladder"),
        ("2002", "England y Verrall", "Reserving\nestocástico"),
        ("2009", "Verdonck et al.", "Robustificación\ndel Chain-Ladder"),
        ("2011-2018", "Verdonck, Pitselis,\nPeremans y Harnau", "Influencia, bootstrap\ny sensibilidad"),
        ("2023-2024", "Avanzi y coautores", "Outliers en\nreserving moderno"),
    ]

    for x, y, (anio, autores, descripcion) in zip(puntos, desplazamientos, etiquetas):
        eje.scatter([x], [0.5], s=260, color=AZUL_PRINCIPAL, zorder=3)
        eje.text(x, y, anio, ha="center", va="bottom" if y > 0.5 else "top", fontsize=13, color=AZUL_PRINCIPAL, fontweight="bold")
        eje.text(x, y + (0.10 if y > 0.5 else -0.10), autores, ha="center", va="bottom" if y > 0.5 else "top", fontsize=12, color="#222222", fontweight="bold")
        eje.text(x, y + (0.22 if y > 0.5 else -0.22), descripcion, ha="center", va="bottom" if y > 0.5 else "top", fontsize=11, color=GRIS_OSCURO)

    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "linea_tiempo_antecedentes.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_diseno_experimental() -> None:
    figura, eje = plt.subplots(figsize=(14, 7), dpi=150)
    eje.set_xlim(0, 14)
    eje.set_ylim(0, 8)
    eje.axis("off")

    eje.add_patch(Rectangle((0.4, 4.5), 4.0, 2.7, facecolor=FONDO_SUAVE, edgecolor=GRIS_SUAVE, lw=1.5))
    eje.text(2.4, 6.8, "Base del experimento", ha="center", fontsize=16, color=AZUL_PRINCIPAL, fontweight="bold")
    lineas_base = [
        "Triángulos 10 × 10",
        "1000 réplicas",
        "Gamma como caso base",
        "Lognormal como sensibilidad",
    ]
    for indice, linea in enumerate(lineas_base):
        eje.text(0.8, 6.2 - 0.55 * indice, f"• {linea}", fontsize=13, color="#222222")

    tarjetas = [
        (5.1, 4.5, "Proporción", ["5%", "10%", "20%"]),
        (8.2, 4.5, "Magnitud", ["×2", "×5", "×10"]),
        (11.3, 4.5, "Ubicación", ["Temprana", "Tardía", "Aleatoria"]),
    ]
    for x, y, titulo, items in tarjetas:
        eje.add_patch(Rectangle((x, y), 2.5, 2.7, facecolor="white", edgecolor=GRIS_SUAVE, lw=1.5))
        eje.text(x + 1.25, 6.8, titulo, ha="center", fontsize=16, color=AZUL_PRINCIPAL, fontweight="bold")
        for indice, item in enumerate(items):
            eje.text(x + 1.25, 6.05 - 0.62 * indice, item, ha="center", fontsize=13, color="#222222")

    for indice, (titulo, zona) in enumerate([("Temprana", "temprana"), ("Tardía", "tardia"), ("Aleatoria", "aleatoria")]):
        x_inicial = 1.0 + indice * 4.2
        eje.text(x_inicial + 1.0, 3.1, titulo, ha="center", fontsize=13, color=GRIS_OSCURO, fontweight="bold")
        for fila in range(4):
            for columna in range(4):
                if columna <= 3 - fila:
                    color = "#D9EEF6"
                    if zona == "temprana" and columna == 0:
                        color = "#F3C7B8"
                    elif zona == "tardia" and columna == 3 - fila:
                        color = "#F3C7B8"
                    elif zona == "aleatoria" and (fila, columna) in [(0, 0), (2, 1), (3, 0)]:
                        color = "#F3C7B8"
                    eje.add_patch(Rectangle((x_inicial + columna * 0.45, 0.5 + (3 - fila) * 0.45), 0.4, 0.4, facecolor=color, edgecolor="white"))

    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "diseno_experimental.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_rmse_global() -> None:
    resumen = leer_csv("resumen_global_gamma_1000replicas.csv").set_index("metodo").loc[["clasico", "mediana", "ponderado", "truncada"]].reset_index()
    etiquetas = ["Clásico", "Mediana", "Ponderado", "Truncada"]
    colores = [COLOR_CLASICO, COLOR_MEDIANA, COLOR_PONDERADO, COLOR_TRUNCADA]

    figura, eje = plt.subplots(figsize=(10, 6), dpi=150)
    valores = resumen["rmse_promedio"].round(0)
    eje.bar(etiquetas, valores, color=colores, width=0.65)
    for indice, valor in enumerate(valores):
        eje.text(indice, valor + 80, f"{int(valor):,}".replace(",", "."), ha="center", fontsize=11, color="#222222")
    eje.set_ylabel("RMSE promedio", color=GRIS_OSCURO)
    eje.set_title("Desempeño global bajo Gamma", color=AZUL_PRINCIPAL, fontsize=16, fontweight="bold")
    eje.spines[["top", "right"]].set_visible(False)
    eje.grid(axis="y", alpha=0.18)
    eje.tick_params(axis="x", labelsize=11)
    eje.tick_params(axis="y", labelsize=10, colors=GRIS_OSCURO)
    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "rmse_global.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_resumen_resultado_global() -> None:
    clasificacion = leer_csv("clasificacion_gamma_1000replicas.csv")
    victorias_contaminadas = (
        clasificacion.query("escenario != 'base_sin_contaminacion' and rango == 1")
        .groupby("metodo")
        .size()
        .sort_values(ascending=False)
    )
    ganador_global = leer_csv("resumen_global_gamma_1000replicas.csv").iloc[0]["metodo"]

    filas = [
        ("Escenario limpio", "Gana el clásico"),
        ("Escenarios contaminados", "Gana la mediana"),
        ("Ganador global", "Mediana" if ganador_global == "mediana" else ganador_global.title()),
        ("Escenarios contaminados\nganados por la mediana", f"{int(victorias_contaminadas.get('mediana', 0))} de 27"),
    ]

    figura, eje = plt.subplots(figsize=(8, 4.5), dpi=150)
    eje.axis("off")
    eje.text(0.02, 0.92, "Lectura rápida de resultados", fontsize=15, color=AZUL_PRINCIPAL, fontweight="bold", transform=eje.transAxes)

    for indice, (texto_izquierdo, texto_derecho) in enumerate(filas):
        y = 0.75 - indice * 0.18
        eje.add_patch(Rectangle((0.02, y - 0.08), 0.46, 0.12, facecolor=FONDO_SUAVE, edgecolor="white", transform=eje.transAxes))
        eje.add_patch(Rectangle((0.50, y - 0.08), 0.46, 0.12, facecolor="white", edgecolor=GRIS_SUAVE, lw=0.8, transform=eje.transAxes))
        eje.text(0.04, y, texto_izquierdo, fontsize=11.5, color="#222222", va="center", transform=eje.transAxes)
        eje.text(0.52, y, texto_derecho, fontsize=11.5, color=AZUL_PRINCIPAL, va="center", fontweight="bold", transform=eje.transAxes)

    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "resumen_resultado_global.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_rmse_lognormal() -> None:
    resumen = leer_csv("resumen_global_lognormal_400replicas.csv").set_index("metodo").loc[["clasico", "mediana", "ponderado", "truncada"]].reset_index()
    etiquetas = ["Clásico", "Mediana", "Ponderado", "Truncada"]
    colores = [COLOR_CLASICO, COLOR_MEDIANA, COLOR_PONDERADO, COLOR_TRUNCADA]

    figura, eje = plt.subplots(figsize=(10, 6), dpi=150)
    valores = resumen["rmse_promedio"].round(0)
    eje.bar(etiquetas, valores, color=colores, width=0.65)
    for indice, valor in enumerate(valores):
        eje.text(indice, valor + 80, f"{int(valor):,}".replace(",", "."), ha="center", fontsize=11, color="#222222")
    eje.set_ylabel("RMSE promedio", color=GRIS_OSCURO)
    eje.set_title("Sensibilidad Lognormal", color=AZUL_PRINCIPAL, fontsize=16, fontweight="bold")
    eje.spines[["top", "right"]].set_visible(False)
    eje.grid(axis="y", alpha=0.18)
    eje.tick_params(axis="x", labelsize=11)
    eje.tick_params(axis="y", labelsize=10, colors=GRIS_OSCURO)
    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "rmse_lognormal.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_resultados_familia() -> None:
    metricas = leer_csv("metricas_gamma_1000replicas.csv")
    clasificacion = leer_csv("clasificacion_gamma_1000replicas.csv")
    resumen_familias = resumir_resultados_familia(metricas, clasificacion)
    familias = [
        "Sin contaminación",
        "Contaminación del 5%",
        "Contaminación del 10%",
        "Contaminación del 20%",
        "Outliers x2",
        "Outliers x5",
        "Outliers x10",
    ]
    tabla = resumen_familias[resumen_familias["familia"].isin(familias)].set_index("familia").loc[familias].reset_index()
    colores = {
        "Clásico": COLOR_CLASICO,
        "Mediana": COLOR_MEDIANA,
        "Ponderado robusto": COLOR_PONDERADO,
        "Media truncada": COLOR_TRUNCADA,
    }

    figura, eje = plt.subplots(figsize=(9.2, 5.2), dpi=150)
    eje.axis("off")
    eje.text(0.02, 0.94, "Resultados por familias de escenarios", fontsize=15, color=AZUL_PRINCIPAL, fontweight="bold", transform=eje.transAxes)

    encabezados = ["Familia", "Mayor frecuencia de menor RMSE"]
    posiciones_x = [0.02, 0.52]
    anchos = [0.44, 0.42]
    for x, ancho, encabezado in zip(posiciones_x, anchos, encabezados):
        eje.add_patch(Rectangle((x, 0.82), ancho, 0.10, facecolor=FONDO_SUAVE, edgecolor="white", transform=eje.transAxes))
        eje.text(x + 0.02, 0.87, encabezado, fontsize=12.5, color="#222222", fontweight="bold", va="center", transform=eje.transAxes)

    for indice, fila in tabla.iterrows():
        y = 0.72 - indice * 0.11
        eje.add_patch(Rectangle((0.02, y - 0.045), 0.44, 0.085, facecolor="white", edgecolor=GRIS_SUAVE, lw=0.8, transform=eje.transAxes))
        eje.text(0.04, y, fila["familia"], fontsize=11.5, color="#222222", va="center", transform=eje.transAxes)

        ganador = _texto_victorias(fila)
        color = colores.get(fila["metodo_con_mas_victorias"], COLOR_CLASICO)
        eje.add_patch(Rectangle((0.52, y - 0.045), 0.42, 0.085, facecolor=color, edgecolor="white", transform=eje.transAxes))
        eje.text(0.54, y, ganador, fontsize=11.5, color="white", va="center", fontweight="bold", transform=eje.transAxes)

    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "familias_resultados.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_metodos_metricas() -> None:
    figura, eje = plt.subplots(figsize=(12, 6), dpi=150)
    eje.set_xlim(0, 12)
    eje.set_ylim(0, 6)
    eje.axis("off")

    eje.text(0.4, 5.3, "Idea central del método", fontsize=15, color=AZUL_PRINCIPAL, fontweight="bold")
    secuencia = [
        (0.5, 3.8, 2.2, 0.9, "Ratios\nde desarrollo"),
        (3.2, 3.8, 2.2, 0.9, "Factores por\nperíodo"),
        (5.9, 3.8, 2.2, 0.9, "IBNR\nestimado"),
    ]
    for x, y, ancho, alto, texto in secuencia:
        eje.add_patch(Rectangle((x, y), ancho, alto, facecolor="white", edgecolor=GRIS_SUAVE, lw=1.6))
        eje.text(x + ancho / 2, y + alto / 2, texto, ha="center", va="center", fontsize=13, color="#222222")
    eje.annotate("", xy=(3.15, 4.25), xytext=(2.75, 4.25), arrowprops=dict(arrowstyle="->", color=AZUL_PRINCIPAL, lw=1.8))
    eje.annotate("", xy=(5.85, 4.25), xytext=(5.45, 4.25), arrowprops=dict(arrowstyle="->", color=AZUL_PRINCIPAL, lw=1.8))
    eje.text(0.65, 2.95, "Todos los métodos parten de los mismos ratios.\nLo que cambia es cómo los resumen.", fontsize=11.5, color=GRIS_OSCURO)

    eje.text(8.5, 5.3, "Comparación del estudio", fontsize=15, color=AZUL_PRINCIPAL, fontweight="bold")
    eje.add_patch(Rectangle((8.1, 3.5), 3.2, 1.4, facecolor=FONDO_SUAVE, edgecolor="white"))
    eje.text(8.3, 4.55, "Métodos", fontsize=12.5, color="#222222", fontweight="bold")
    eje.text(8.3, 4.15, "• Clásico\n• Mediana\n• Truncada\n• Ponderado robusto", fontsize=11.5, color="#222222", va="top")

    eje.add_patch(Rectangle((8.1, 1.5), 3.2, 1.5, facecolor="white", edgecolor=GRIS_SUAVE, lw=1.2))
    eje.text(8.3, 2.65, "Métricas", fontsize=12.5, color="#222222", fontweight="bold")
    eje.text(8.3, 2.25, "• Sesgo\n• RMSE\n• MAPE\n• Desviación estándar", fontsize=11.5, color="#222222", va="top")

    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "metodos_metricas.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_lista_validacion() -> None:
    figura, eje = plt.subplots(figsize=(10, 5), dpi=150)
    eje.axis("off")
    eje.text(0.02, 0.92, "Validación previa del simulador", fontsize=16, color=AZUL_PRINCIPAL, fontweight="bold", transform=eje.transAxes)
    items = [
        "La media simulada se aproxima a la estructura teórica",
        "El acumulado es consistente con el incremental",
        "La máscara observada define correctamente la zona futura",
        "La contaminación se aplica solo sobre la parte observada",
        "Sin ruido, los métodos recuperan el IBNR esperado",
    ]
    for indice, item in enumerate(items):
        y = 0.78 - indice * 0.14
        eje.add_patch(Rectangle((0.03, y - 0.04), 0.04, 0.06, facecolor="#D9EEF6", edgecolor=GRIS_SUAVE, lw=1.0, transform=eje.transAxes))
        eje.text(0.045, y - 0.005, "✓", fontsize=16, color=AZUL_PRINCIPAL, fontweight="bold", transform=eje.transAxes)
        eje.text(0.09, y, item, fontsize=12, color="#222222", va="center", transform=eje.transAxes)

    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "lista_validacion.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_resumen_estabilidad() -> None:
    metricas = leer_csv("metricas_gamma_1000replicas.csv")
    limpio = metricas[metricas["escenario"] == "base_sin_contaminacion"][["metodo", "desviacion_estandar_estimaciones"]].set_index("metodo")
    contaminados = (
        metricas[metricas["escenario"] != "base_sin_contaminacion"]
        .groupby("metodo", as_index=False)["desviacion_estandar_estimaciones"]
        .mean()
        .set_index("metodo")
        .loc[["clasico", "mediana", "ponderado", "truncada"]]
        .reset_index()
    )
    tabla = metricas.pivot(index="escenario", columns="metodo", values="desviacion_estandar_estimaciones")
    tabla_contaminada = tabla[tabla.index != "base_sin_contaminacion"].copy()
    mediana_mas_estable = int((tabla_contaminada["mediana"] < tabla_contaminada["clasico"]).sum())
    total_escenarios = int(len(tabla_contaminada))

    etiquetas = ["Clásico", "Mediana", "Ponderado", "Truncada"]
    colores = [COLOR_CLASICO, COLOR_MEDIANA, COLOR_PONDERADO, COLOR_TRUNCADA]

    figura, (eje_izquierdo, eje_derecho) = plt.subplots(1, 2, figsize=(13.2, 5.4), dpi=150, gridspec_kw={"width_ratios": [1.15, 0.85]})

    valores = contaminados["desviacion_estandar_estimaciones"].round(0)
    eje_izquierdo.bar(etiquetas, valores, color=colores, width=0.65)
    for indice, valor in enumerate(valores):
        eje_izquierdo.text(indice, valor + 70, f"{int(valor):,}".replace(",", "."), ha="center", fontsize=11, color="#222222")
    eje_izquierdo.set_ylabel("Desviación estándar promedio", color=GRIS_OSCURO)
    eje_izquierdo.set_title("Estabilidad en escenarios contaminados", color=AZUL_PRINCIPAL, fontsize=16, fontweight="bold")
    eje_izquierdo.spines[["top", "right"]].set_visible(False)
    eje_izquierdo.grid(axis="y", alpha=0.18)
    eje_izquierdo.tick_params(axis="x", labelsize=11)
    eje_izquierdo.tick_params(axis="y", labelsize=10, colors=GRIS_OSCURO)

    eje_derecho.axis("off")
    eje_derecho.text(0.02, 0.92, "Lectura rápida de estabilidad", fontsize=15, color=AZUL_PRINCIPAL, fontweight="bold", transform=eje_derecho.transAxes)
    filas = [
        ("Escenario limpio", f"Clásico ({limpio.loc['clasico', 'desviacion_estandar_estimaciones']:.0f})"),
        ("Contaminados en promedio", f"Mediana ({contaminados.loc[contaminados['metodo'] == 'mediana', 'desviacion_estandar_estimaciones'].iloc[0]:.0f})"),
        ("Mediana vs clásico", f"{mediana_mas_estable} de {total_escenarios}"),
    ]
    for indice, (texto_izquierdo, texto_derecho) in enumerate(filas):
        y = 0.74 - indice * 0.22
        eje_derecho.add_patch(Rectangle((0.02, y - 0.08), 0.48, 0.12, facecolor=FONDO_SUAVE, edgecolor="white", transform=eje_derecho.transAxes))
        eje_derecho.add_patch(Rectangle((0.52, y - 0.08), 0.42, 0.12, facecolor="white", edgecolor=GRIS_SUAVE, lw=0.8, transform=eje_derecho.transAxes))
        eje_derecho.text(0.04, y, texto_izquierdo, fontsize=11.5, color="#222222", va="center", transform=eje_derecho.transAxes)
        eje_derecho.text(0.54, y, texto_derecho, fontsize=11.5, color=AZUL_PRINCIPAL, va="center", fontweight="bold", transform=eje_derecho.transAxes)
    eje_derecho.text(0.02, 0.08, "La mediana presentó menor desviación estándar que el clásico\nen la mayoría de los escenarios contaminados.", fontsize=11.5, color=GRIS_OSCURO, transform=eje_derecho.transAxes)

    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "desviacion_estabilidad.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def guardar_resumen_lognormal() -> None:
    clasificacion = leer_csv("clasificacion_lognormal_400replicas.csv")
    resumen = leer_csv("resumen_global_lognormal_400replicas.csv")
    victorias = clasificacion.query("rango == 1").groupby("metodo").size().sort_values(ascending=False)
    ganador_global = resumen.iloc[0]["metodo"]

    filas = [
        ("Ganador global", "Mediana" if ganador_global == "mediana" else ganador_global.title()),
        ("Escenarios ganados por la mediana", str(int(victorias.get("mediana", 0)))),
        ("Patrón principal", "Se mantiene"),
    ]

    figura, eje = plt.subplots(figsize=(8, 4.2), dpi=150)
    eje.axis("off")
    eje.text(0.02, 0.90, "Lectura rápida de la sensibilidad", fontsize=15, color=AZUL_PRINCIPAL, fontweight="bold", transform=eje.transAxes)
    for indice, (texto_izquierdo, texto_derecho) in enumerate(filas):
        y = 0.72 - indice * 0.20
        eje.add_patch(Rectangle((0.02, y - 0.08), 0.46, 0.12, facecolor=FONDO_SUAVE, edgecolor="white", transform=eje.transAxes))
        eje.add_patch(Rectangle((0.50, y - 0.08), 0.40, 0.12, facecolor="white", edgecolor=GRIS_SUAVE, lw=0.8, transform=eje.transAxes))
        eje.text(0.04, y, texto_izquierdo, fontsize=11.5, color="#222222", va="center", transform=eje.transAxes)
        eje.text(0.52, y, texto_derecho, fontsize=11.5, color=AZUL_PRINCIPAL, va="center", fontweight="bold", transform=eje.transAxes)

    figura.tight_layout()
    figura.savefig(DIRECTORIO_FIGURAS / "resumen_lognormal.png", bbox_inches="tight", facecolor="white")
    plt.close(figura)


def main() -> None:
    guardar_triangulo_ibnr()
    guardar_linea_tiempo()
    guardar_diseno_experimental()
    guardar_rmse_global()
    guardar_resumen_resultado_global()
    guardar_rmse_lognormal()
    guardar_resultados_familia()
    guardar_metodos_metricas()
    guardar_lista_validacion()
    guardar_resumen_estabilidad()
    guardar_resumen_lognormal()
    print(f"Figuras creadas en {DIRECTORIO_FIGURAS}")


if __name__ == "__main__":
    main()
