"""Janela de configurações: paleta de cores personalizável."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.settings_service import PALETTE_SIZE, SettingsService


class SettingsDialog(QDialog):
    """Diálogo de configurações de aparência das notas.

    Permite personalizar cada um dos 5 slots de cor disponíveis, usando o
    seletor de cores nativo (roda espectral completa), e restaurar a
    paleta original de fábrica.

    Args:
        settings: Serviço de configurações a ser lido/gravado.
        on_palette_change: Callback chamado sempre que a paleta mudar,
            recebendo a nova lista de 5 cores.
    """

    def __init__(
        self,
        settings: SettingsService,
        on_palette_change: Callable[[list[str]], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._on_palette_change = on_palette_change
        self._swatches: list[QPushButton] = []

        self._setup_window()
        self._build_ui()
        self._refresh_swatches()

    # ------------------------------------------------------------------
    # Configuração inicial
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configura aparência e tamanho do diálogo."""
        self.setWindowTitle("Configurações — StickyDesk")
        self.setFixedSize(340, 230)
        self.setStyleSheet(
            """
            QDialog {
                /* Mesma cor de fundo creme suave do container principal */
                background-color: #fff4df; 
            }
            """
        )

    def _build_ui(self) -> None:
        """Constrói o layout do diálogo de configurações."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(14)

        heading = QLabel("Paleta de cores")
        heading.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        # Cor do título principal no marrom característico do app
        heading.setStyleSheet("color: #a2835e; font-weight: 600;")
        layout.addWidget(heading)

        subtitle = QLabel(
            "Escolha qualquer cor do espectro para cada um dos 5 slots\n"
            "disponíveis nas notas."
        )
        subtitle.setFont(QFont("Segoe UI", 9))
        # Subtítulo em marrom médio para manter o minimalismo sem sumir no fundo
        subtitle.setStyleSheet("color: #c69868;")
        layout.addWidget(subtitle)

        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(12)
        for index in range(PALETTE_SIZE):
            swatch_row.addWidget(self._build_swatch(index))
        layout.addLayout(swatch_row)

        layout.addStretch()

        restore_btn = QPushButton("Restaurar configurações padrão")
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.setStyleSheet(
            """
            QPushButton {
                /* Botão principal de ação: preenchido com o marrom de destaque */
                background-color: #c69868;
                color: #fff4df;
                border: 1px solid #c69868;
                border-radius: 14px; /* Formato pílula consistente */
                padding: 7px 12px;
                font-family: "Segoe UI";
                font-size: 10pt;
                font-weight: 500;
            }
            QPushButton:hover {
                /* Destaque sutil ao passar o mouse */
                background-color: #a2835e;
                border-color: #a2835e;
            }
            """
        )
        restore_btn.clicked.connect(self._restore_defaults)
        layout.addWidget(restore_btn)


    def _build_swatch(self, index: int) -> QPushButton:
        """Cria um botão circular que representa um slot de cor editável."""
        btn = QPushButton()
        btn.setFixedSize(44, 44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Clique para escolher uma cor")
        
        # Estilização dinâmica para os círculos de cores (swatches)
        # Adiciona uma borda fina elegante para que as cores conversem com o resto da interface
        btn.setStyleSheet(
            """
            QPushButton {
                border: 2px solid #f3e1ae;
                border-radius: 22px; /* Metade de 44 para garantir que seja um círculo perfeito */
            }
            QPushButton:hover {
                border: 2px solid #c69868; /* Destaca o slot ativo ao passar o mouse */
            }
            """
        )
        
        btn.clicked.connect(lambda _checked, i=index: self._pick_color(i))
        self._swatches.append(btn)
        return btn


    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _pick_color(self, index: int) -> None:
        """Abre o seletor de cor nativo (roda espectral) para um slot."""
        current = QColor(self._settings.get_colors()[index])
        chosen = QColorDialog.getColor(
            current, self, "Escolha uma cor para este slot"
        )
        if chosen.isValid():
            self._settings.set_color(index, chosen.name())
            self._refresh_swatches()
            self._on_palette_change(self._settings.get_colors())

    def _restore_defaults(self) -> None:
        """Restaura a paleta de fábrica e notifica os ouvintes."""
        self._settings.restore_defaults()
        self._refresh_swatches()
        self._on_palette_change(self._settings.get_colors())

    def _refresh_swatches(self) -> None:
        """Atualiza a cor exibida em cada botão de slot."""
        colors = self._settings.get_colors()
        for btn, color in zip(self._swatches, colors):
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: 22px;
                    border: 2px solid rgba(0,0,0,0.15);
                }}
                QPushButton:hover {{
                    border: 2px solid rgba(0,0,0,0.45);
                }}
                """
            )
