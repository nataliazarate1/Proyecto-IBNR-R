from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbformat import NotebookNode

RAIZ = Path(__file__).resolve().parents[1]
FUENTE_PREDETERMINADA = RAIZ / "cuadernos" / "estudio_ibnr_chain_ladder_robusto.ipynb"
SALIDA_PREDETERMINADA = FUENTE_PREDETERMINADA


def interpretar_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normaliza el cuaderno principal del proyecto. "
            "Este guion permite reescribirlo con o sin salidas y dejar una codificacion estable."
        )
    )
    parser.add_argument("--fuente", default=str(FUENTE_PREDETERMINADA), help="Ruta del cuaderno de origen.")
    parser.add_argument("--salida", default=str(SALIDA_PREDETERMINADA), help="Ruta del cuaderno de salida.")
    parser.add_argument(
        "--limpiar-salidas",
        action="store_true",
        help="Elimina salidas y execution_count para generar una copia limpia.",
    )
    return parser.parse_args()


def _limpiar_salidas(cuaderno: NotebookNode) -> NotebookNode:
    for celda in cuaderno.cells:
        if celda.get("cell_type") == "code":
            celda["outputs"] = []
            celda["execution_count"] = None
    return cuaderno


def main() -> None:
    argumentos = interpretar_argumentos()
    fuente = Path(argumentos.fuente)
    salida = Path(argumentos.salida)

    cuaderno = nbformat.read(fuente, as_version=4)
    if argumentos.limpiar_salidas:
        cuaderno = _limpiar_salidas(cuaderno)

    salida.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(cuaderno, salida)
    print(f"Cuaderno escrito en {salida}")


if __name__ == "__main__":
    main()
