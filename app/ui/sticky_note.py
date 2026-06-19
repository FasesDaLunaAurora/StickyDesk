"""Widget visual de uma nota adesiva individual."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.note import Note
from app.services.note_service import NOTE_COLORS

# Debounce para auto-save de conteúdo (ms)
_AUTOSAVE_DELAY_MS = 500
# Tamanho padrão da nota
_NOTE_WIDTH = 240
_NOTE_HEIGHT = 260
# Altura da barra de título
_HEADER_HEIGHT = 34


class StickyNoteWidget(QWidget):
    """Janela flutuante sem moldura que representa uma nota adesiva.

    Args:
        note: Dados iniciais da nota.
        on_content_change: Callback chamado com (note_id, novo_conteúdo).
        on_title_change: Callback chamado com (note_id, novo_título).
        on_position_change: Callback chamado com (note_id, x, y).
        on_color_change: Callback chamado com (note_id, nova_cor).
        on_close: Callback chamado com (note_id) ao apenas ocultar a nota.
        on_delete: Callback chamado com (note_id) ao excluir permanentemente.
    """

    def __init__(
        self,
        note: Note,
        on_content_change: Callable[[int, str], None],
        on_title_change: Callable[[int, str], None],
        on_position_change: Callable[[int, int, int], None],
        on_color_change: Callable[[int, str], None],
        on_close: Callable[[int], None],
        on_delete: Callable[[int], None],
    ) -> None:
        super().__init__()

        self._note_id = note.id
        self._on_content_change = on_content_change
        self._on_title_change = on_title_change
        self._on_position_change = on_position_change
        self._on_color_change = on_color_change
        self._on_close = on_close
        self._on_delete = on_delete

        # Drag state
        self._drag_active = False
        self._drag_origin = QPoint()

        # Debounce timers para auto-save (texto e título)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._flush_content)

        self._title_timer = QTimer(self)
        self._title_timer.setSingleShot(True)
        self._title_timer.timeout.connect(self._flush_title)

        self._setup_window()
        self._build_ui(note)
        self._apply_color(note.color)
        self.move(note.x, note.y)
        self.resize(_NOTE_WIDTH, _NOTE_HEIGHT)

    # ------------------------------------------------------------------
    # Configuração inicial
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configura flags da janela: sem bordas, flutuante, translúcida."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(180, 160)

    def _build_ui(self, note: Note) -> None:
        """Constrói o layout interno da nota."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Container principal com arredondamento (desenhado em paintEvent)
        self._container = QWidget(self)
        self._container.setObjectName("container")
        outer.addWidget(self._container)

        inner = QVBoxLayout(self._container)
        inner.setContentsMargins(0, 0, 0, 8)
        inner.setSpacing(0)

        inner.addWidget(self._build_header(note.title))
        inner.addWidget(self._build_editor(note.content))

    def _build_header(self, title: str) -> QWidget:
        """Cria a barra superior (drag handle + título + botões de ação)."""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(_HEADER_HEIGHT)
        header.setCursor(Qt.CursorShape.SizeAllCursor)

        # Captura eventos de mouse da barra para arrastar
        header.mousePressEvent = self._header_mouse_press      # type: ignore[method-assign]
        header.mouseMoveEvent = self._header_mouse_move        # type: ignore[method-assign]
        header.mouseReleaseEvent = self._header_mouse_release  # type: ignore[method-assign]

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(4)

        # Campo de título editável
        title_field = QLineEdit(title)
        title_field.setObjectName("title_field")
        title_field.setPlaceholderText("Título")
        title_field.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        title_field.textChanged.connect(self._schedule_title_save)
        # Evita que cliques no campo iniciem o drag da janela
        title_field.mousePressEvent = lambda e: QLineEdit.mousePressEvent(title_field, e)  # type: ignore[method-assign]
        self._title_field = title_field
        layout.addWidget(title_field, stretch=1)

        # Botões de cor
        for color in NOTE_COLORS:
            btn = self._make_color_dot(color)
            layout.addWidget(btn)

        layout.addSpacing(6)

        # Botão fechar (oculta, mantém salva)
        close_btn = QPushButton("—")
        close_btn.setObjectName("btn_close")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Fechar (a nota continua salva)")
        close_btn.clicked.connect(self._request_close)
        layout.addWidget(close_btn)

        # Botão excluir permanentemente
        delete_btn = QPushButton("✕")
        delete_btn.setObjectName("btn_delete")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setToolTip("Excluir permanentemente")
        delete_btn.clicked.connect(self._request_delete)
        layout.addWidget(delete_btn)

        return header

    def _make_color_dot(self, color: str) -> QPushButton:
        """Cria um botão circular de seleção de cor."""
        btn = QPushButton()
        btn.setFixedSize(14, 14)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(f"Cor {color}")
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                border-radius: 7px;
                border: 1.5px solid rgba(0,0,0,0.15);
            }}
            QPushButton:hover {{
                border: 2px solid rgba(0,0,0,0.4);
            }}
            """
        )
        btn.clicked.connect(lambda _checked, c=color: self._change_color(c))
        return btn

    def _build_editor(self, content: str) -> QPlainTextEdit:
        """Cria a área de edição de texto."""
        editor = QPlainTextEdit(content)
        editor.setObjectName("editor")
        editor.setFont(QFont("Consolas", 10))
        editor.setPlaceholderText("Escreva sua nota aqui…")
        editor.textChanged.connect(self._schedule_save)
        self._editor = editor
        return editor

    # ------------------------------------------------------------------
    # Aparência
    # ------------------------------------------------------------------

    def _apply_color(self, color: str) -> None:
        """Aplica a cor base da nota em todos os elementos visuais."""
        self._current_color = color
        dark = self._darken(color, factor=0.88)
        darker = self._darken(color, factor=0.75)

        self._container.setStyleSheet(
            f"""
            QWidget#container {{
                background-color: {color};
                border-radius: 10px;
            }}
            QWidget#header {{
                background-color: {dark};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}
            QLineEdit#title_field {{
                color: rgba(0,0,0,0.65);
                background: transparent;
                border: none;
                padding: 0px 2px;
            }}
            QLineEdit#title_field:focus {{
                background: rgba(255,255,255,0.35);
                border-radius: 4px;
            }}
            QPushButton#btn_close {{
                background: transparent;
                border: none;
                color: rgba(0,0,0,0.40);
                font-size: 13px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton#btn_close:hover {{
                background: rgba(0,0,0,0.12);
                color: rgba(0,0,0,0.75);
            }}
            QPushButton#btn_delete {{
                background: transparent;
                border: none;
                color: rgba(0,0,0,0.40);
                font-size: 12px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton#btn_delete:hover {{
                background: rgba(200,0,0,0.18);
                color: rgba(150,0,0,0.95);
            }}
            QPlainTextEdit#editor {{
                background-color: transparent;
                border: none;
                color: #2d2d2d;
                padding: 8px 12px 4px 12px;
                selection-background-color: {darker};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(0,0,0,0.18);
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            """
        )

    def paintEvent(self, event) -> None:  # noqa: N802
        """Desenha sombra suave ao redor da nota."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        shadow_color = QColor(0, 0, 0, 35)
        for i in range(6, 0, -1):
            path = QPainterPath()
            rect = self.rect().adjusted(i, i, -i, -i)
            path.addRoundedRect(rect.x(), rect.y() + i, rect.width(), rect.height(), 10, 10)
            painter.setPen(QPen(shadow_color, 0))
            painter.setBrush(shadow_color)
            painter.drawPath(path)

        painter.end()

    # ------------------------------------------------------------------
    # Arrastar janela
    # ------------------------------------------------------------------

    def _header_mouse_press(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _header_mouse_move(self, event) -> None:
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_origin
            self.move(new_pos)

    def _header_mouse_release(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = False
            pos = self.pos()
            self._on_position_change(self._note_id, pos.x(), pos.y())

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _schedule_save(self) -> None:
        """Reinicia o timer de debounce do conteúdo a cada alteração."""
        self._save_timer.start(_AUTOSAVE_DELAY_MS)

    def _flush_content(self) -> None:
        """Dispara o callback de conteúdo após o debounce."""
        self._on_content_change(self._note_id, self._editor.toPlainText())

    def _schedule_title_save(self) -> None:
        """Reinicia o timer de debounce do título a cada alteração."""
        self._title_timer.start(_AUTOSAVE_DELAY_MS)

    def _flush_title(self) -> None:
        """Dispara o callback de título após o debounce."""
        self._on_title_change(self._note_id, self._title_field.text())

    def _change_color(self, color: str) -> None:
        """Altera a cor da nota e persiste."""
        self._apply_color(color)
        self._on_color_change(self._note_id, color)

    def _request_close(self) -> None:
        """Oculta a janela mas mantém a nota salva para reabrir depois."""
        self._on_close(self._note_id)
        self.hide()

    def _request_delete(self) -> None:
        """Pede confirmação e, se aceito, exclui a nota permanentemente."""
        resposta = QMessageBox.question(
            self,
            "Excluir nota",
            "Excluir esta nota permanentemente?\nEssa ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resposta == QMessageBox.StandardButton.Yes:
            self._on_delete(self._note_id)
            self.close()

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    @staticmethod
    def _darken(hex_color: str, factor: float) -> str:
        """Escurece uma cor hexadecimal pelo fator informado (0-1)."""
        c = QColor(hex_color)
        r = int(c.red() * factor)
        g = int(c.green() * factor)
        b = int(c.blue() * factor)
        return QColor(r, g, b).name()
