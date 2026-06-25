"""Painel base reutilizável para janelas sem moldura nativa.

Replica exatamente o visual do painel principal (MainWindow): container
arredondado com sombra em camadas, cabeçalho com título e botão de fechar,
e suporte a arrastar a janela pela barra superior. Usado por qualquer
diálogo do app que precise do mesmo design (configurações, seletor de cor).
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

_HEADER_HEIGHT = 38
_CORNER_RADIUS = 12


class FramelessPanel(QWidget):
    """Container base com cabeçalho customizado, usado como casca visual.

    Subclasses (ou código que o instancia diretamente) devem adicionar seu
    conteúdo a `self.content_layout`, que já vive dentro do container com
    cantos arredondados e abaixo do cabeçalho arrastável.

    Args:
        title: Texto exibido no cabeçalho.
        on_close: Callback chamado ao clicar no botão de fechar (✕).
    """

    def __init__(self, title: str, on_close: Callable[[], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_active = False
        self._drag_origin = QPoint()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)

        self._container = QWidget(self)
        self._container.setObjectName("frameless_container")
        outer.addWidget(self._container)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 14)
        container_layout.setSpacing(0)
        container_layout.addWidget(self._build_header(title, on_close))

        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(20, 14, 20, 0)
        self.content_layout.setSpacing(14)
        container_layout.addLayout(self.content_layout)

        self._apply_style()

    # ------------------------------------------------------------------
    # Cabeçalho
    # ------------------------------------------------------------------

    def _build_header(self, title: str, on_close: Callable[[], None]) -> QWidget:
        """Cria a barra superior arrastável com título e botão de fechar."""
        header = QWidget()
        header.setObjectName("frameless_header")
        header.setFixedHeight(_HEADER_HEIGHT)
        header.setCursor(Qt.CursorShape.SizeAllCursor)

        header.mousePressEvent = self._header_mouse_press      # type: ignore[method-assign]
        header.mouseMoveEvent = self._header_mouse_move        # type: ignore[method-assign]
        header.mouseReleaseEvent = self._header_mouse_release  # type: ignore[method-assign]

        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("frameless_header_title")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        layout.addWidget(title_label)
        layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("frameless_header_close")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(on_close)
        layout.addWidget(close_btn)

        return header

    def _apply_style(self) -> None:
        """Aplica o mesmo estilo visual usado no painel principal (MainWindow)."""
        self._container.setStyleSheet(
            f"""
            /* =================================================================
               CONTAINER GERAL DA JANELA
               ================================================================= */
            QWidget#frameless_container {{
                background-color: #fff4df;   /* Tom creme claro e limpo para o fundo */
                border-radius: {_CORNER_RADIUS}px;
                border: 1px solid #f3e1ae;   /* Borda fina externa em ouro-pastel */
            }}
            
            /* =================================================================
               CABEÇALHO / BARRA DE TÍTULO
               ================================================================= */
            QWidget#frameless_header {{
                background-color: #f3e1ae;   /* Cabeçalho combinando com o ouro-pastel */
                border-top-left-radius: {_CORNER_RADIUS}px;
                border-top-right-radius: {_CORNER_RADIUS}px;
            }}
            QLabel#frameless_header_title {{
                color: #a2835e;              /* Texto do título em marrom escuro sofisticado */
                font-weight: 600;            /* Deixa o título elegantemente encorpado */
                background: transparent;
            }}
            
            /* =================================================================
               BOTÃO DE FECHAR (✕)
               ================================================================= */
            QPushButton#frameless_header_close {{
                background: transparent;     /* Sem fundo inicial */
                border: none;
                color: rgba(162,131,94,0.65);/* Marrom escuro com opacidade para suavidade */
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }}
            QPushButton#frameless_header_close:hover {{
                /* Vermelho/Terracota baseado na paleta fina para a ação de fechar */
                background: rgba(184,65,56,0.12);
                color: #b84138;
            }}
            """
        )

    # ------------------------------------------------------------------
    # Sombra (idêntica à do MainWindow)
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        """Desenha sombra suave ao redor do painel."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        shadow_color = QColor(0, 0, 0, 35)
        for i in range(6, 0, -1):
            path = QPainterPath()
            rect = self.rect().adjusted(i, i, -i, -i)
            path.addRoundedRect(
                rect.x(), rect.y() + i, rect.width(), rect.height(),
                _CORNER_RADIUS, _CORNER_RADIUS,
            )
            painter.setPen(QPen(shadow_color, 0))
            painter.setBrush(shadow_color)
            painter.drawPath(path)

        painter.end()

    # ------------------------------------------------------------------
    # Arrastar pelo cabeçalho
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
