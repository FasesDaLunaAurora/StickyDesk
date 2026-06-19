"""Camada de persistência: leitura e escrita de notas em JSON."""

import json
from pathlib import Path

from app.models.note import Note


class JsonStorage:
    """Gerencia a persistência das notas em um arquivo JSON local.

    Args:
        filepath: Caminho para o arquivo de armazenamento.
    """

    def __init__(self, filepath: str = "data/notes.json") -> None:
        self._path = Path(filepath)
        self._ensure_file()

    # ------------------------------------------------------------------
    # Público
    # ------------------------------------------------------------------

    def load(self) -> list[Note]:
        """Carrega e retorna todas as notas do arquivo JSON."""
        raw = self._read_raw()
        return [Note.from_dict(item) for item in raw]

    def save(self, notes: list[Note]) -> None:
        """Persiste a lista completa de notas no arquivo JSON."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump([n.to_dict() for n in notes], fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Privado
    # ------------------------------------------------------------------

    def _ensure_file(self) -> None:
        """Cria o arquivo de dados se ele ainda não existir."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("[]", encoding="utf-8")

    def _read_raw(self) -> list[dict]:
        """Lê e retorna o conteúdo bruto do JSON como lista de dicionários."""
        try:
            content = self._path.read_text(encoding="utf-8").strip()
            return json.loads(content) if content else []
        except (json.JSONDecodeError, OSError):
            return []
