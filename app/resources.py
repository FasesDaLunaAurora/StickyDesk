"""Resolução de caminhos de recursos (assets), compatível com PyInstaller.

Em modo desenvolvimento (`python main.py`), os arquivos em `assets/`
vivem ao lado do código-fonte. Quando o app é compilado com PyInstaller
no modo `-F` (onefile), o executável extrai seus arquivos para uma pasta
temporária em tempo de execução, referenciada por `sys._MEIPASS` — os
caminhos calculados a partir de `__file__` deixam de ser válidos nesse
cenário. Esta função detecta o ambiente e resolve o caminho corretamente
nos dois casos.

Importante: arquivos referenciados aqui também precisam ser explicitamente
incluídos no build via `--add-data "assets;assets"` no `build.bat` (no
Windows; seria `assets:assets` em Linux/Mac) — caso contrário, eles nunca
entram no pacote do PyInstaller e este resolvedor não tem o que encontrar.
"""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(*relative_parts: str) -> Path:
    """Resolve o caminho absoluto de um recurso em `assets/`.

    Args:
        *relative_parts: Partes do caminho relativo dentro de `assets/`,
            por exemplo `resource_path("logo.png")` ou
            `resource_path("icons", "settings.png")`.

    Returns:
        Caminho absoluto para o recurso, válido tanto em modo
        desenvolvimento quanto dentro de um executável compilado.
    """
    base_dir = getattr(sys, "_MEIPASS", None)
    if base_dir is not None:
        # Rodando como .exe empacotado: os arquivos foram extraídos
        # para uma pasta temporária apontada por sys._MEIPASS.
        return Path(base_dir) / "assets" / Path(*relative_parts)

    # Modo desenvolvimento: assets/ vive na raiz do projeto,
    # dois níveis acima deste arquivo (app/resources.py -> app/ -> raiz/).
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "assets" / Path(*relative_parts)
