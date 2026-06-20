"""Serviço de configurações do app: paleta de cores personalizável."""

import json
from pathlib import Path

# Paleta padrão de fábrica — usada também pela restauração de configurações
DEFAULT_COLORS: list[str] = [
    "#fff176",  # amarelo suave
    "#ffcc80",  # laranja suave
    "#a5d6a7",  # verde suave
    "#90caf9",  # azul suave
    "#ce93d8",  # lilás suave
]

# A quantidade de slots de cor é sempre fixa em 5
PALETTE_SIZE = 5


class SettingsService:
    """Gerencia a paleta de cores personalizável das notas.

    Mantém sempre exatamente `PALETTE_SIZE` cores. Persiste em um arquivo
    JSON próprio, separado de `notes.json`, para não acoplar preferências
    de aparência aos dados das notas.

    Args:
        filepath: Caminho do arquivo de configurações.
    """

    def __init__(self, filepath: str) -> None:
        self._path = Path(filepath)
        self._colors: list[str] = self._load()

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def get_colors(self) -> list[str]:
        """Retorna a paleta atual de 5 cores."""
        return list(self._colors)

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------

    def set_color(self, index: int, color: str) -> None:
        """Substitui a cor de um slot específico (0 a 4).

        Args:
            index: Posição do slot na paleta.
            color: Nova cor em formato hexadecimal (ex: '#ff8800').
        """
        if not 0 <= index < PALETTE_SIZE:
            raise ValueError(f"Índice de cor inválido: {index}")
        self._colors[index] = color
        self._persist()

    def restore_defaults(self) -> None:
        """Restaura a paleta para as cores originais de fábrica."""
        self._colors = list(DEFAULT_COLORS)
        self._persist()

    # ------------------------------------------------------------------
    # Privado
    # ------------------------------------------------------------------

    def _load(self) -> list[str]:
        """Carrega a paleta salva, ou retorna a padrão se ausente/corrompida."""
        try:
            content = self._path.read_text(encoding="utf-8")
            data = json.loads(content)
            colors = data.get("colors", [])
            if isinstance(colors, list) and len(colors) == PALETTE_SIZE:
                return colors
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
        return list(DEFAULT_COLORS)

    def _persist(self) -> None:
        """Salva a paleta atual no arquivo de configurações."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump({"colors": self._colors}, fh, ensure_ascii=False, indent=2)
