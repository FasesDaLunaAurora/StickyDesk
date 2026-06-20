"""Janela painel principal: lista de notas, controle global de minimizar/fechar."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.note import Note
from app.services.note_service import NoteService
from app.services.settings_service import SettingsService
from app.ui.settings_dialog import SettingsDialog
from app.ui.sticky_note import StickyNoteWidget

_PANEL_WIDTH = 240
_PANEL_HEIGHT = 320
_HEADER_HEIGHT = 52
_LOGO_SIZE = 36

# Caminho esperado para a logo da aplicação (fornecida futuramente pelo usuário)
_LOGO_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "logo.png"


class MainWindow(QWidget):
    """Painel de controle: lista todas as notas e permite minimizar/fechar tudo.

    Funciona como o "Bloco de Notas" tradicional: ao abrir o app, todas as
    notas salvas aparecem automaticamente (e uma nota em branco é criada se
    não houver nenhuma). Este painel oferece uma visão geral, acesso às
    configurações de aparência e um ponto único para encerrar a aplicação.

    Args:
        service: Serviço de domínio das notas.
        settings: Serviço de configurações (paleta de cores personalizável).
        app: Instância da QApplication (necessária para encerrar o app).
    """

    def __init__(self, service: NoteService, settings: SettingsService, app: QApplication) -> None:
        super().__init__()
        self._service = service
        self._settings = settings
        self._app = app
        self._widgets: dict[int, StickyNoteWidget] = {}

        # Drag state do painel
        self._drag_active = False
        self._drag_origin = QPoint()

        self._setup_window()
        self._build_ui()
        self._load_or_create_notes()
        self._refresh_list()

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configura a janela do painel: sem bordas pesadas, sempre à mão."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(_PANEL_WIDTH, _PANEL_HEIGHT)
        self.move(40, 40)

    def _build_ui(self) -> None:
        """Constrói o layout do painel: cabeçalho + lista de notas."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(0)

        self._container = QWidget(self)
        self._container.setObjectName("panel_container")
        outer.addWidget(self._container)

        inner = QVBoxLayout(self._container)
        inner.setContentsMargins(0, 0, 0, 8)
        inner.setSpacing(6)

        inner.addWidget(self._build_header())

        list_widget = QListWidget()
        list_widget.setObjectName("notes_list")
        list_widget.itemClicked.connect(self._on_item_clicked)
        self._list_widget = list_widget
        inner.addWidget(list_widget)

        self._apply_style()

    def _build_header(self) -> QWidget:
        """Cria a barra superior do painel (drag handle + logo + ações)."""
        header = QWidget()
        header.setObjectName("panel_header")
        header.setFixedHeight(_HEADER_HEIGHT)
        header.setCursor(Qt.CursorShape.SizeAllCursor)

        header.mousePressEvent = self._header_mouse_press      # type: ignore[method-assign]
        header.mouseMoveEvent = self._header_mouse_move        # type: ignore[method-assign]
        header.mouseReleaseEvent = self._header_mouse_release  # type: ignore[method-assign]

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(6)

        layout.addWidget(self._build_logo())
        layout.addStretch()

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("panel_btn_settings")
        settings_btn.setFixedSize(22, 22)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setToolTip("Configurações")
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        min_btn = QPushButton("—")
        min_btn.setObjectName("panel_btn_min")
        min_btn.setFixedSize(22, 22)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.setToolTip("Minimizar todas as notas")
        min_btn.clicked.connect(self._minimize_all)
        layout.addWidget(min_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("panel_btn_close")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Fechar StickyDesk")
        close_btn.clicked.connect(self._quit)
        layout.addWidget(close_btn)

        return header

    def _build_logo(self) -> QLabel:
        """Cria o label da logo, usando a imagem fornecida ou um placeholder.

        Se `assets/logo.png` existir, ela é exibida com altura fixa e
        largura proporcional (adequado para logos no formato wordmark,
        mais largas que altas). Caso contrário, mostra um placeholder
        textual maior e legível até a logo definitiva ser fornecida.
        """
        logo_label = QLabel()
        logo_label.setObjectName("panel_logo")

        if _LOGO_PATH.exists():
            pixmap = QPixmap(str(_LOGO_PATH))
            scaled = pixmap.scaledToHeight(
                _LOGO_SIZE, Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled)
            logo_label.setFixedHeight(_LOGO_SIZE)
        else:
            # Placeholder até a logo definitiva ser fornecida pelo usuário
            logo_label.setText("📌 StickyDesk")
            logo_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))

        return logo_label

    def _apply_style(self) -> None:
        """Aplica o estilo visual do painel (tema neutro, discreto)."""
        self._container.setStyleSheet(
            """
            QWidget#panel_container {
                background-color: #f3f3f3;
                border-radius: 12px;
            }
            QWidget#panel_header {
                background-color: #e2e2e2;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
            QLabel#panel_logo {
                color: rgba(0,0,0,0.65);
                background: transparent;
            }
            QPushButton#panel_btn_settings {
                background: transparent;
                border: none;
                color: rgba(0,0,0,0.45);
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton#panel_btn_settings:hover {
                background: rgba(0,0,0,0.10);
                color: rgba(0,0,0,0.80);
            }
            QPushButton#panel_btn_min {
                background: transparent;
                border: none;
                color: rgba(0,0,0,0.40);
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton#panel_btn_min:hover {
                background: rgba(0,0,0,0.12);
                color: rgba(0,0,0,0.75);
            }
            QPushButton#panel_btn_close {
                background: transparent;
                border: none;
                color: rgba(0,0,0,0.40);
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton#panel_btn_close:hover {
                background: rgba(200,0,0,0.18);
                color: rgba(150,0,0,0.95);
            }
            QListWidget#notes_list {
                background: transparent;
                border: none;
                padding: 4px 8px;
                font-family: "Segoe UI";
                font-size: 12px;
                color: #333;
            }
            QListWidget#notes_list::item {
                padding: 6px 8px;
                border-radius: 6px;
                margin-bottom: 2px;
            }
            QListWidget#notes_list::item:hover {
                background: rgba(0,0,0,0.06);
            }
            QListWidget#notes_list::item:selected {
                background: rgba(0,0,0,0.10);
                color: #333;
            }
            """
        )

    def paintEvent(self, event) -> None:  # noqa: N802
        """Desenha sombra suave ao redor do painel."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        shadow_color = QColor(0, 0, 0, 35)
        for i in range(6, 0, -1):
            path = QPainterPath()
            rect = self.rect().adjusted(i, i, -i, -i)
            path.addRoundedRect(rect.x(), rect.y() + i, rect.width(), rect.height(), 12, 12)
            painter.setPen(QPen(shadow_color, 0))
            painter.setBrush(shadow_color)
            painter.drawPath(path)

        painter.end()

    # ------------------------------------------------------------------
    # Arrastar painel
    # ------------------------------------------------------------------

    def _header_mouse_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _header_mouse_move(self, event) -> None:
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_origin)

    def _header_mouse_release(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = False

    # ------------------------------------------------------------------
    # Carregamento inicial (comportamento "Bloco de Notas")
    # ------------------------------------------------------------------

    def _load_or_create_notes(self) -> None:
        """Abre todas as notas salvas; cria uma em branco se não houver nenhuma."""
        notes = self._service.get_all()
        if not notes:
            note = self._service.create(x=140, y=140)
            self._spawn_widget(note)
            return

        for note in notes:
            self._spawn_widget(note)

    # ------------------------------------------------------------------
    # Criação / exibição de notas
    # ------------------------------------------------------------------

    def _create_note(self) -> None:
        """Cria uma nova nota com posição escalonada e abre o widget."""
        offset = len(self._widgets) * 30
        x = 140 + offset
        y = 140 + offset
        note = self._service.create(x=x, y=y)
        self._spawn_widget(note)
        self._refresh_list()

    def _spawn_widget(self, note: Note) -> None:
        """Instancia e exibe o StickyNoteWidget para uma nota."""
        widget = StickyNoteWidget(
            note=note,
            on_content_change=self._on_content_change,
            on_title_change=self._on_title_change,
            on_position_change=self._on_position_change,
            on_color_change=self._on_color_change,
            on_new_note=self._create_note,
            on_delete=self._on_delete,
            on_size_change=self._on_size_change,
            palette=self._settings.get_colors(),
        )
        self._widgets[note.id] = widget
        widget.show()

    # ------------------------------------------------------------------
    # Lista de notas no painel
    # ------------------------------------------------------------------

    def _refresh_list(self) -> None:
        """Atualiza a lista de notas exibida no painel."""
        self._list_widget.clear()
        for note_id, widget in self._widgets.items():
            label = widget.current_title().strip() or "(sem título)"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            self._list_widget.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Restaura/foca a nota correspondente ao item clicado na lista."""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        widget = self._widgets.get(note_id)
        if widget is None:
            return
        if widget.isMinimized():
            widget.showNormal()
        widget.raise_()
        widget.activateWindow()

    # ------------------------------------------------------------------
    # Callbacks vindos dos widgets de nota
    # ------------------------------------------------------------------

    def _on_content_change(self, note_id: int, content: str) -> None:
        self._service.update_content(note_id, content)

    def _on_title_change(self, note_id: int, title: str) -> None:
        self._service.update_title(note_id, title)
        self._refresh_list()

    def _on_position_change(self, note_id: int, x: int, y: int) -> None:
        self._service.update_position(note_id, x, y)

    def _on_size_change(self, note_id: int, width: int, height: int) -> None:
        self._service.update_size(note_id, width, height)

    def _on_color_change(self, note_id: int, color: str) -> None:
        self._service.update_color(note_id, color)

    def _on_delete(self, note_id: int) -> None:
        """Remove a nota permanentemente e atualiza a lista."""
        self._service.delete(note_id)
        self._widgets.pop(note_id, None)
        self._refresh_list()

    # ------------------------------------------------------------------
    # Configurações
    # ------------------------------------------------------------------

    def _open_settings(self) -> None:
        """Abre o diálogo de configurações de paleta de cores."""
        dialog = SettingsDialog(
            settings=self._settings,
            on_palette_change=self._on_palette_change,
            parent=self,
        )
        dialog.exec()

    def _on_palette_change(self, colors: list[str]) -> None:
        """Propaga a nova paleta para todas as notas já abertas."""
        for widget in self._widgets.values():
            widget.update_palette(colors)

    # ------------------------------------------------------------------
    # Ações globais do painel
    # ------------------------------------------------------------------

    def _minimize_all(self) -> None:
        """Minimiza o painel e todas as notas abertas."""
        for widget in self._widgets.values():
            widget.showMinimized()
        self.showMinimized()

    def _quit(self) -> None:
        """Encerra a aplicação garantindo que todas as notas fiquem salvas."""
        for widget in list(self._widgets.values()):
            widget.flush_pending_saves()
            widget.close()
        self._app.quit()

    def closeEvent(self, event) -> None:  # noqa: N802
        """Fechar o painel (✕) encerra o app por completo, com tudo salvo."""
        self._quit()
        event.accept()
