"""Coordenador principal: ícone na bandeja do sistema e ciclo de vida das notas."""

from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QPolygon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app.models.note import Note
from app.services.note_service import NoteService
from app.ui.sticky_note import StickyNoteWidget


class MainWindow:
    """Gerencia o ícone da bandeja e o ciclo de vida de todos os widgets de nota.

    Não é uma QMainWindow — a aplicação roda inteiramente via systray +
    janelas flutuantes (Tool windows), sem janela principal visível.

    Args:
        service: Serviço de domínio das notas.
        app: Instância da QApplication (necessária para o ciclo de vida).
    """

    def __init__(self, service: NoteService, app: QApplication) -> None:
        self._service = service
        self._app = app
        self._widgets: dict[int, StickyNoteWidget] = {}

        self._tray = self._build_tray()
        self._load_existing_notes()

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def _build_tray(self) -> QSystemTrayIcon:
        """Cria e exibe o ícone na bandeja do sistema."""
        icon = self._make_tray_icon()
        tray = QSystemTrayIcon(icon, self._app)
        tray.setToolTip("StickyDesk — Notas na área de trabalho")
        tray.setContextMenu(self._build_menu())
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        return tray

    def _build_menu(self) -> QMenu:
        """Constrói o menu de contexto do ícone na bandeja."""
        menu = QMenu()
        menu.setStyleSheet(
            """
            QMenu {
                background: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 4px;
                font-family: Segoe UI;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #444;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 4px 8px;
            }
            """
        )
        menu.addAction("✚  Nova nota", self._create_note)
        menu.addAction("👁  Mostrar todas as notas", self._show_all_notes)
        menu.addSeparator()
        menu.addAction("✕  Fechar StickyDesk", self._quit)
        return menu

    def _load_existing_notes(self) -> None:
        """Recria os widgets de todas as notas salvas e marcadas como visíveis."""
        for note in self._service.get_all():
            if note.visible:
                self._spawn_widget(note)

    # ------------------------------------------------------------------
    # Criação de notas
    # ------------------------------------------------------------------

    def _create_note(self) -> None:
        """Cria uma nova nota com posição escalonada e abre o widget."""
        offset = len(self._widgets) * 30
        x = 120 + offset
        y = 120 + offset
        note = self._service.create(x=x, y=y)
        self._spawn_widget(note)

    def _spawn_widget(self, note: Note) -> None:
        """Instancia e exibe o StickyNoteWidget para uma nota."""
        widget = StickyNoteWidget(
            note=note,
            on_content_change=self._on_content_change,
            on_title_change=self._on_title_change,
            on_position_change=self._on_position_change,
            on_color_change=self._on_color_change,
            on_close=self._on_note_close,
            on_delete=self._on_delete,
        )
        self._widgets[note.id] = widget
        widget.show()

    def _show_all_notes(self) -> None:
        """Reabre todas as notas salvas (inclusive as que estavam ocultas)."""
        for note in self._service.get_all():
            self._service.set_visibility(note.id, True)
            if note.id not in self._widgets:
                self._spawn_widget(note)
            else:
                self._widgets[note.id].show()
                self._widgets[note.id].raise_()

    # ------------------------------------------------------------------
    # Callbacks vindos dos widgets
    # ------------------------------------------------------------------

    def _on_content_change(self, note_id: int, content: str) -> None:
        self._service.update_content(note_id, content)

    def _on_title_change(self, note_id: int, title: str) -> None:
        self._service.update_title(note_id, title)

    def _on_position_change(self, note_id: int, x: int, y: int) -> None:
        self._service.update_position(note_id, x, y)

    def _on_color_change(self, note_id: int, color: str) -> None:
        self._service.update_color(note_id, color)

    def _on_note_close(self, note_id: int) -> None:
        """Marca a nota como oculta, mas mantém os dados salvos."""
        self._service.set_visibility(note_id, False)
        self._widgets.pop(note_id, None)

    def _on_delete(self, note_id: int) -> None:
        """Remove a nota permanentemente."""
        self._service.delete(note_id)
        self._widgets.pop(note_id, None)

    # ------------------------------------------------------------------
    # Eventos da bandeja
    # ------------------------------------------------------------------

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Duplo clique no ícone da bandeja reabre todas as notas salvas."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_all_notes()

    def _quit(self) -> None:
        """Encerra a aplicação garantindo que todas as notas fiquem salvas."""
        for note_id, widget in list(self._widgets.items()):
            # A posição mais recente já foi salva a cada drag; aqui garantimos
            # que o conteúdo/título pendentes no debounce também sejam persistidos.
            self._service.update_content(note_id, widget._editor.toPlainText())
            self._service.update_title(note_id, widget._title_field.text())
            widget.close()
        self._app.quit()

    # ------------------------------------------------------------------
    # Ícone da bandeja gerado programaticamente
    # ------------------------------------------------------------------

    @staticmethod
    def _make_tray_icon() -> QIcon:
        """Gera um ícone 32×32 de post-it amarelo para a bandeja."""
        size = 32
        px = QPixmap(size, size)
        px.fill(QColor(0, 0, 0, 0))

        painter = QPainter(px)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Corpo do post-it
        painter.setBrush(QColor("#fff176"))
        painter.setPen(QColor("#c8b400"))
        painter.drawRoundedRect(2, 6, 28, 24, 3, 3)

        # Aba dobrada (canto superior direito)
        painter.setBrush(QColor("#e6d000"))
        painter.setPen(QColor("#c8b400"))
        fold_points = [
            QPoint(30, 6),
            QPoint(22, 6),
            QPoint(30, 14),
        ]
        painter.drawPolygon(QPolygon(fold_points))

        # Linhas de texto simuladas
        painter.setPen(QColor("#b0a000"))
        for y_line in [14, 19, 24]:
            painter.drawLine(7, y_line, 22, y_line)

        painter.end()
        return QIcon(px)
