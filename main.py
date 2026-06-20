"""Ponto de entrada da aplicação StickyDesk."""


import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.services.note_service import NoteService
from app.storage.json_storage import JsonStorage
from app.ui.main_window import MainWindow

import os

# Define o caminho na pasta AppData/Roaming do usuário do Windows
_APPDATA_DIR = Path(os.environ["APPDATA"]) / "StickyDesk"
_NOTES_PATH = _APPDATA_DIR / "notes.json"

# Garante que a pasta StickyDesk exista antes de tentar criar o arquivo
_APPDATA_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Inicializa e executa o StickyDesk."""
    app = QApplication(sys.argv)
    app.setApplicationName("StickyDesk")
    app.setQuitOnLastWindowClosed(False)  # Mantém rodando sem janelas abertas


    # Composição das dependências (DI manual)
    storage = JsonStorage(filepath=str(_NOTES_PATH))
    service = NoteService(storage=storage)
    window = MainWindow(service=service, app=app)  # noqa: F841 — mantém referência viva
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
