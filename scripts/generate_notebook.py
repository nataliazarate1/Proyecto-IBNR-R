from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbformat import NotebookNode


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "notebooks" / "ibnr_chain_ladder_robusto.ipynb"
DEFAULT_OUTPUT = DEFAULT_SOURCE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normaliza el notebook principal del proyecto. "
            "El cuaderno actual funciona como fuente canónica y este script permite "
            "reescribirlo con o sin salidas, manteniendo una codificación estable."
        )
    )
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SOURCE),
        help="Ruta del notebook de origen.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Ruta del notebook de salida.",
    )
    parser.add_argument(
        "--strip-outputs",
        action="store_true",
        help="Elimina salidas y execution_count para generar una copia limpia.",
    )
    return parser.parse_args()


def _strip_outputs(notebook: NotebookNode) -> NotebookNode:
    for cell in notebook.cells:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
    return notebook


def main() -> None:
    args = parse_args()
    source = Path(args.source)
    output = Path(args.output)

    notebook = nbformat.read(source, as_version=4)
    if args.strip_outputs:
        notebook = _strip_outputs(notebook)

    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output)
    print(f"Notebook escrito en {output}")


if __name__ == "__main__":
    main()
