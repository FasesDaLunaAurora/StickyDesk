"""Ponto de entrada da aplicação StickyDesk."""

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.services.note_service import NoteService
from app.services.settings_service import SettingsService
from app.storage.json_storage import JsonStorage
from app.ui.main_window import MainWindow

# Define o caminho na pasta AppData/Roaming do usuário do Windows.
# Necessário porque o app é instalado em Program Files (somente leitura
# para usuários comuns), então os dados não podem ficar ao lado do .exe.
_APPDATA_DIR = Path(os.environ["APPDATA"]) / "StickyDesk"
_NOTES_PATH = _APPDATA_DIR / "notes.json"
_SETTINGS_PATH = _APPDATA_DIR / "settings.json"

# Garante que a pasta StickyDesk exista antes de tentar criar os arquivos
_APPDATA_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Inicializa e executa o StickyDesk.

    Comportamento estilo "Bloco de Notas": ao abrir, todas as notas salvas
    aparecem automaticamente. Se não houver nenhuma, uma nota em branco é
    criada. Não há ícone de bandeja — todo o controle do app passa pelo
    painel principal (MainWindow) e pelos botões de cada nota.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("StickyDesk")
    app.setQuitOnLastWindowClosed(False)  # O painel controla o encerramento

    # Composição das dependências (DI manual)
    storage = JsonStorage(filepath=str(_NOTES_PATH))
    settings = SettingsService(filepath=str(_SETTINGS_PATH))
    service = NoteService(storage=storage, settings=settings)
    window = MainWindow(service=service, settings=settings, app=app)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
