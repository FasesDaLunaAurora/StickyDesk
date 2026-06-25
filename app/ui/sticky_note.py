"""Widget visual de uma nota adesiva individual."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPoint, QRect, QTimer, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from app.models.note import Note
from app.services.note_service import NOTE_COLORS
from app.ui.live_markdown_editor import LiveMarkdownEditor

# Debounce para auto-save de conteúdo (ms)
_AUTOSAVE_DELAY_MS = 500
# Tamanho mínimo da nota
_MIN_WIDTH = 190
_MIN_HEIGHT = 170
# Altura da barra de título
_HEADER_HEIGHT = 38
# Tamanho da dobra do canto (efeito "peeling corner")
_FOLD_SIZE = 26
# Espessura da borda sensível ao redo de resize
_RESIZE_MARGIN = 8
# Tamanho uniforme dos botões de ação do cabeçalho
_ACTION_BTN_SIZE = 22


class SpectrumButton(QPushButton):
    """Botão circular que desenha uma roda de espectro de cores como ícone.

    Usado no cabeçalho da nota para abrir o popup de seleção de cor —
    visualmente mais fiel a uma roda cromática do que um emoji.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFlat(True)
        self.setStyleSheet(
            """
            QPushButton {
                background: rgba(255,255,255,0.30);
                border: none;
                border-radius: 11px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.55);
            }
            """
        )

    def paintEvent(self, event) -> None:  # noqa: N802
        """Desenha uma roda de cores simplificada (6 fatias de matiz)."""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        margin = 4
        size = min(rect.width(), rect.height()) - margin * 2
        cx = rect.width() / 2
        cy = rect.height() / 2
        radius = size / 2

        hues = [0, 60, 120, 180, 240, 300]  # vermelho, amarelo, verde, ciano, azul, magenta
        slice_angle = 360 / len(hues)

        painter.setPen(QPen(QColor(255, 255, 255, 200), 1))
        for i, hue in enumerate(hues):
            color = QColor.fromHsv(hue, 220, 240)
            painter.setBrush(color)
            start_angle = int((i * slice_angle) * 16)
            span_angle = int(slice_angle * 16)
            painter.drawPie(
                int(cx - radius), int(cy - radius), int(size), int(size),
                start_angle, span_angle,
            )

        # Centro branco vazado para lembrar uma roda cromática (não um disco sólido)
        inner_radius = radius * 0.42
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 235))
        painter.drawEllipse(
            int(cx - inner_radius), int(cy - inner_radius),
            int(inner_radius * 2), int(inner_radius * 2),
        )

        painter.end()


class StickyNoteWidget(QWidget):
    """Janela flutuante sem moldura que representa uma nota adesiva.

    Visual: papel com dobra no canto inferior direito, sombra em camadas
    e cantos arredondados — lembra um post-it físico levemente erguido.
    Suporta redimensionamento livre pelas bordas, como uma janela comum.

    Args:
        note: Dados iniciais da nota.
        on_content_change: Callback chamado com (note_id, novo_conteúdo).
        on_title_change: Callback chamado com (note_id, novo_título).
        on_position_change: Callback chamado com (note_id, x, y).
        on_color_change: Callback chamado com (note_id, nova_cor).
        on_new_note: Callback chamado (sem args) para criar uma nova nota.
        on_delete: Callback chamado com (note_id) ao excluir permanentemente.
        on_size_change: Callback chamado com (note_id, width, height) ao redimensionar.
        palette: Lista de cores disponíveis para seleção rápida no cabeçalho.
    """

    def __init__(
        self,
        note: Note,
        on_content_change: Callable[[int, str], None],
        on_title_change: Callable[[int, str], None],
        on_position_change: Callable[[int, int, int], None],
        on_color_change: Callable[[int, str], None],
        on_new_note: Callable[[], None],
        on_delete: Callable[[int], None],
        on_size_change: Callable[[int, int, int], None],
        palette: list[str] | None = None,
    ) -> None:
        super().__init__()

        self._note_id = note.id
        self._on_content_change = on_content_change
        self._on_title_change = on_title_change
        self._on_position_change = on_position_change
        self._on_color_change = on_color_change
        self._on_new_note = on_new_note
        self._on_delete = on_delete
        self._on_size_change = on_size_change
        self._palette = palette or list(NOTE_COLORS)

        # Drag state (mover a janela pela barra superior)
        self._drag_active = False
        self._drag_origin = QPoint()

        # Resize state (arrastar pelas bordas)
        self._resize_active = False
        self._resize_edge: str | None = None
        self._resize_origin_geo = QRect()
        self._resize_origin_mouse = QPoint()

        # Debounce timers para auto-save (texto e título)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._flush_content)

        self._title_timer = QTimer(self)
        self._title_timer.setSingleShot(True)
        self._title_timer.timeout.connect(self._flush_title)

        self._raw_content = note.content

        self._setup_window()
        self._build_ui(note)
        self._apply_color(note.color)
        self.move(note.x, note.y)
        self.resize(note.width, note.height)
        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Configuração inicial
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configura flags da janela: sem bordas, com suporte a minimizar."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(_MIN_WIDTH, _MIN_HEIGHT)

    def _build_ui(self, note: Note) -> None:
        """Constrói o layout interno da nota."""
        outer = QVBoxLayout(self)
        # Margem extra para abrigar a área sensível de resize + sombra
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)

        self._container = QWidget(self)
        self._container.setObjectName("container")
        outer.addWidget(self._container)

        inner = QVBoxLayout(self._container)
        inner.setContentsMargins(0, 0, 0, 10)
        inner.setSpacing(0)

        inner.addWidget(self._build_header(note.title))
        inner.addWidget(self._build_editor(note.content))

    def _build_header(self, title: str) -> QWidget:
        """Cria a barra superior (drag handle + título + botões de ação)."""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(_HEADER_HEIGHT)
        header.setCursor(Qt.CursorShape.SizeAllCursor)

        header.mousePressEvent = self._header_mouse_press      # type: ignore[method-assign]
        header.mouseMoveEvent = self._header_mouse_move        # type: ignore[method-assign]
        header.mouseReleaseEvent = self._header_mouse_release  # type: ignore[method-assign]

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(5)

        title_field = QLineEdit(title)
        title_field.setObjectName("title_field")
        title_field.setPlaceholderText("Título")
        title_field.setFont(QFont("Segoe UI Semibold", 10))
        title_field.textChanged.connect(self._schedule_title_save)
        self._title_field = title_field
        layout.addWidget(title_field, stretch=1)

        self._spectrum_btn = SpectrumButton()
        self._spectrum_btn.setFixedSize(_ACTION_BTN_SIZE, _ACTION_BTN_SIZE)
        self._spectrum_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._spectrum_btn.setToolTip("Trocar cor")
        self._spectrum_btn.clicked.connect(self._open_color_popup)
        layout.addWidget(self._spectrum_btn)

        layout.addSpacing(8)

        self._new_btn = self._make_action_button("+", "Criar nova nota", self._handle_new)
        layout.addWidget(self._new_btn)

        self._min_btn = self._make_action_button("—", "Minimizar", self.showMinimized)
        layout.addWidget(self._min_btn)

        self._delete_btn = self._make_action_button("✕", "Excluir permanentemente", self._request_delete)
        layout.addWidget(self._delete_btn)

        return header

    def _make_action_button(self, label: str, tooltip: str, callback: Callable[[], None]) -> QPushButton:
        """Cria um botão de ação do cabeçalho com tamanho uniforme."""
        btn = QPushButton(label)
        btn.setObjectName("action_btn")
        btn.setFixedSize(_ACTION_BTN_SIZE, _ACTION_BTN_SIZE)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        return btn

    def _handle_new(self) -> None:
        """Encaminha o pedido de criação de nova nota."""
        self._on_new_note()

    def _open_color_popup(self) -> None:
        """Abre um popup leve com as 5 cores disponíveis para escolha rápida."""
        popup = QMenu(self)
        popup.setObjectName("color_popup")
        popup.setStyleSheet(
            """
            QMenu#color_popup {
                background: white;
                border: 1px solid rgba(0,0,0,0.15);
                border-radius: 10px;
                padding: 8px;
            }
            """
        )

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(4, 4, 4, 4)
        row_layout.setSpacing(8)

        for color in self._palette:
            dot = self._make_color_dot(color, size=22)
            dot.clicked.connect(popup.close)
            row_layout.addWidget(dot)

        action = QWidgetAction(popup)
        action.setDefaultWidget(row)
        popup.addAction(action)

        button_pos = self._spectrum_btn.mapToGlobal(
            self._spectrum_btn.rect().bottomLeft()
        )
        popup.exec(button_pos)

    def _make_color_dot(self, color: str, size: int = 15) -> QPushButton:
        """Cria um botão circular de seleção de cor.

        Args:
            color: Cor de fundo do botão, em hexadecimal.
            size: Diâmetro do botão em pixels.
        """
        btn = QPushButton()
        btn.setFixedSize(size, size)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(f"Cor {color}")
        radius = size // 2
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                border-radius: {radius}px;
                border: 1.5px solid rgba(0,0,0,0.18);
            }}
            QPushButton:hover {{
                border: 2px solid rgba(0,0,0,0.45);
            }}
            """
        )
        btn.clicked.connect(lambda _checked, c=color: self._change_color(c))
        return btn

    def _build_editor(self, content: str) -> LiveMarkdownEditor:
        """Cria a área de edição com formatação markdown aplicada ao vivo.

        O conteúdo é carregado como HTML (rich text), já que não existe
        mais markdown bruto separado — a formatação é parte do documento.

        Notas salvas por versões anteriores (markdown bruto em texto puro)
        são carregadas como texto simples, sem perder o conteúdo — apenas
        sem a formatação retroativa, que passa a se aplicar a partir da
        próxima edição.
        """
        editor = LiveMarkdownEditor()
        editor.setObjectName("editor")
        editor.setFont(QFont("Segoe UI", 10))
        editor.setPlaceholderText("Escreva sua nota aqui… (**negrito**, *itálico*, - item, [ ] tarefa)")

        if "<html" in content.lower() or "<!doctype" in content.lower():
            editor.setHtml(content)
        else:
            editor.setPlainText(content)

        editor.textChanged.connect(self._on_text_changed)
        self._editor = editor
        return editor

    def _on_text_changed(self) -> None:
        """Captura o HTML atual do editor e agenda o salvamento."""
        self._raw_content = self._editor.toHtml()
        self._schedule_save()

    # ------------------------------------------------------------------
    # Aparência
    # ------------------------------------------------------------------

    def _apply_color(self, color: str) -> None:
        """Aplica a cor base da nota em todos os elementos visuais."""
        self._current_color = color
        dark = self._darken(color, factor=0.90)
        darker = self._darken(color, factor=0.78)

        self._container.setStyleSheet(
            f"""
            QWidget#container {{
                background-color: {color};
                border-radius: 12px;
            }}
            QWidget#header {{
                background-color: transparent;
                border-top-left-radius: 12px;
            }}
            QLineEdit#title_field {{
                color: rgba(0,0,0,0.70);
                background: transparent;
                border: none;
                padding: 2px 4px;
            }}
            QLineEdit#title_field:focus {{
                background: rgba(255,255,255,0.40);
                border-radius: 5px;
            }}
            QPushButton#action_btn {{
                background: rgba(255,255,255,0.30);
                border: none;
                color: rgba(0,0,0,0.50);
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }}
            QPushButton#action_btn:hover {{
                background: rgba(255,255,255,0.55);
                color: rgba(0,0,0,0.80);
            }}
            QTextEdit#editor {{
                background-color: transparent;
                border: none;
                color: #2b2b2b;
                padding: 6px 14px 4px 14px;
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
        self._fold_color = dark
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        """Desenha sombra em camadas, papel com dobra no canto inferior direito."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 8
        paper_rect = self.rect().adjusted(margin, margin, -margin, -margin)

        self._draw_shadow(painter, paper_rect)
        self._draw_fold(painter, paper_rect)

        painter.end()

    def _draw_shadow(self, painter: QPainter, paper_rect: QRect) -> None:
        """Desenha sombra suave em múltiplas camadas sob o papel."""
        layers = 8
        for i in range(layers, 0, -1):
            alpha = int(6 + (layers - i) * 1.5)
            offset = i
            shadow_rect = paper_rect.adjusted(-offset // 2, offset, offset // 2, offset)
            path = QPainterPath()
            path.addRoundedRect(
                shadow_rect.x(), shadow_rect.y(),
                shadow_rect.width(), shadow_rect.height(),
                12, 12,
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawPath(path)

    def _draw_fold(self, painter: QPainter, paper_rect: QRect) -> None:
        """Desenha o efeito de canto dobrado no rodapé direito do papel.

        A borda inferior é levemente curva (como na referência visual),
        terminando numa pequena dobra triangular erguida no canto.
        """
        fold = _FOLD_SIZE
        x2 = paper_rect.right()
        y2 = paper_rect.bottom()

        path = QPainterPath()
        path.moveTo(x2 - fold, y2)
        path.lineTo(x2, y2 - fold)
        path.lineTo(x2, y2)
        path.closeSubpath()

        gradient = QLinearGradient(x2 - fold, y2, x2, y2 - fold)
        base = QColor(getattr(self, "_fold_color", "#e0e0e0"))
        gradient.setColorAt(0.0, base.darker(112))
        gradient.setColorAt(1.0, base.lighter(108))

        painter.setPen(QPen(QColor(0, 0, 0, 35), 1))
        painter.setBrush(gradient)
        painter.drawPath(path)

    # ------------------------------------------------------------------
    # Arrastar janela (pela barra de título)
    # ------------------------------------------------------------------

    def _header_mouse_press(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _header_mouse_move(self, event: QMouseEvent) -> None:
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_origin)

    def _header_mouse_release(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = False
            pos = self.pos()
            self._on_position_change(self._note_id, pos.x(), pos.y())

    # ------------------------------------------------------------------
    # Redimensionar pelas bordas (estilo janela nativa do Windows)
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._edge_at(event.position().toPoint())
            if edge:
                self._resize_active = True
                self._resize_edge = edge
                self._resize_origin_geo = self.geometry()
                self._resize_origin_mouse = event.globalPosition().toPoint()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._resize_active:
            self._perform_resize(event.globalPosition().toPoint())
            return

        edge = self._edge_at(event.position().toPoint())
        self.setCursor(self._cursor_for_edge(edge) if edge else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._resize_active and event.button() == Qt.MouseButton.LeftButton:
            self._resize_active = False
            self._resize_edge = None
            pos = self.pos()
            self._on_position_change(self._note_id, pos.x(), pos.y())
            self._on_size_change(self._note_id, self.width(), self.height())
            return
        super().mouseReleaseEvent(event)

    def _edge_at(self, pos: QPoint) -> str | None:
        """Identifica se o ponto está sobre uma borda redimensionável."""
        rect = self.rect()
        m = _RESIZE_MARGIN

        on_left = pos.x() <= m
        on_right = pos.x() >= rect.width() - m
        on_top = pos.y() <= m
        on_bottom = pos.y() >= rect.height() - m

        if on_top and on_left:
            return "top_left"
        if on_top and on_right:
            return "top_right"
        if on_bottom and on_left:
            return "bottom_left"
        if on_bottom and on_right:
            return "bottom_right"
        if on_left:
            return "left"
        if on_right:
            return "right"
        if on_top:
            return "top"
        if on_bottom:
            return "bottom"
        return None

    @staticmethod
    def _cursor_for_edge(edge: str) -> Qt.CursorShape:
        """Retorna o cursor apropriado para a borda detectada."""
        mapping = {
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "top_left": Qt.CursorShape.SizeFDiagCursor,
            "bottom_right": Qt.CursorShape.SizeFDiagCursor,
            "top_right": Qt.CursorShape.SizeBDiagCursor,
            "bottom_left": Qt.CursorShape.SizeBDiagCursor,
        }
        return mapping.get(edge, Qt.CursorShape.ArrowCursor)

    def _perform_resize(self, global_pos: QPoint) -> None:
        """Recalcula a geometria da janela durante o arrasto de resize."""
        delta = global_pos - self._resize_origin_mouse
        geo = QRect(self._resize_origin_geo)

        if "left" in self._resize_edge:
            new_left = geo.left() + delta.x()
            if geo.right() - new_left >= _MIN_WIDTH:
                geo.setLeft(new_left)
        if "right" in self._resize_edge:
            new_width = geo.width() + delta.x()
            geo.setWidth(max(new_width, _MIN_WIDTH))
        if "top" in self._resize_edge:
            new_top = geo.top() + delta.y()
            if geo.bottom() - new_top >= _MIN_HEIGHT:
                geo.setTop(new_top)
        if "bottom" in self._resize_edge:
            new_height = geo.height() + delta.y()
            geo.setHeight(max(new_height, _MIN_HEIGHT))

        self.setGeometry(geo)

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _schedule_save(self) -> None:
        """Reinicia o timer de debounce do conteúdo a cada alteração."""
        self._save_timer.start(_AUTOSAVE_DELAY_MS)

    def _flush_content(self) -> None:
        """Dispara o callback de conteúdo após o debounce."""
        self._on_content_change(self._note_id, self._raw_content)

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

    def flush_pending_saves(self) -> None:
        """Força a gravação imediata de conteúdo/título pendentes no debounce."""
        if self._save_timer.isActive():
            self._save_timer.stop()
            self._flush_content()
        if self._title_timer.isActive():
            self._title_timer.stop()
            self._flush_title()

    def current_title(self) -> str:
        """Retorna o título atual exibido no campo (para uso pelo painel)."""
        return self._title_field.text()

    def update_palette(self, colors: list[str]) -> None:
        """Atualiza a paleta de cores disponível no popup de seleção.

        Chamado quando o usuário altera a paleta nas configurações,
        para refletir as novas cores em notas já abertas. Como o popup
        é reconstruído a cada clique no ícone de espectro, basta
        atualizar a lista interna.
        """
        self._palette = list(colors)

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
