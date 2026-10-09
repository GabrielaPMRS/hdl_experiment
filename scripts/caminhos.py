"""Raiz compartilhada dos dados, independente do diretorio de execucao."""
import os
from pathlib import Path


def raiz_dados():
    """HDL_DATA_ROOT tem precedencia sobre o repositorio irmao."""
    configurado = os.environ.get("HDL_DATA_ROOT")
    if configurado:
        return Path(configurado).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "HDL-Experiment-Data"
