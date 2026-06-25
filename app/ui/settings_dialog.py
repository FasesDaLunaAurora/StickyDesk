"""Janela de configurações: paleta de cores personalizável."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QEventLoop, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.settings_service import PALETTE_SIZE, SettingsService
from app.ui.color_picker_dialog import ColorPickerDialog
from app.ui.frameless_panel import FramelessPanel


class SettingsDialog(FramelessPanel):
    """Diálogo de configurações de aparência das notas.

    Permite personalizar cada um dos 5 slots de cor disponíveis, usando o
    seletor de cores customizado (mesmo visual do restante do app), e
    restaurar a paleta original de fábrica. Usa o mesmo design de
    cabeçalho do painel principal, sem moldura nativa do Windows.

    Args:
        settings: Serviço de configurações a ser lido/gravado.
        on_palette_change: Callback chamado sempre que a paleta mudar,
            recebendo a nova lista de 5 cores.
    """

    _closed_signal = Signal()

    def __init__(
        self,
        settings: SettingsService,
        on_palette_change: Callable[[list[str]], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="Configurações",
            on_close=self._handle_close,
            parent=parent,
        )
        self._settings = settings
        self._on_palette_change = on_palette_change
        self._swatches: list[QPushButton] = []

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(360, 280)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._build_content()
        self._refresh_swatches()

    # ------------------------------------------------------------------
    # Conteúdo
    # ------------------------------------------------------------------

    def _build_content(self) -> None:
        """Constrói o conteúdo específico do diálogo dentro do painel base."""
        heading = QLabel("Paleta de cores")
        heading.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        # Cor do título principal em marrom escuro característico do app
        heading.setStyleSheet("color: #a2835e; font-weight: 600;")
        self.content_layout.addWidget(heading)

        subtitle = QLabel(
            "Escolha qualquer cor do espectro para cada um dos 5 slots\n"
            "disponíveis nas notas."
        )
        subtitle.setFont(QFont("Segoe UI", 9))
        # Subtítulo em marrom médio para consistência com o painel de notas
        subtitle.setStyleSheet("color: #c69868;")
        self.content_layout.addWidget(subtitle)

        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(12)
        for index in range(PALETTE_SIZE):
            swatch_row.addWidget(self._build_swatch(index))
        self.content_layout.addLayout(swatch_row)

        self.content_layout.addStretch()

        restore_btn = QPushButton("Restaurar configurações padrão")
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.setStyleSheet(
            """
            QPushButton {
                /* Botão secundário: fundo cinza-claro, contorno e texto em marrom médio */
                background-color: #f1f1f1;
                color: #c69868;
                border: 1px solid #c69868;
                border-radius: 14px; /* Formato pílula idêntico às notas */
                padding: 7px 12px;
                font-family: "Segoe UI", "Helvetica Neue", sans-serif;
                font-size: 10pt;
            }
            QPushButton:hover {
                /* Efeito hover inverte as cores exatamente como os itens da lista */
                background-color: #c69868;
                border-color: #c69868;
                color: #fff4df; /* Texto ganha o tom creme claro */
            }
            """
        )
        restore_btn.clicked.connect(self._restore_defaults)
        self.content_layout.addWidget(restore_btn)

    def _build_swatch(self, index: int) -> QPushButton:
        """Cria um botão circular que representa um slot de cor editável."""
        btn = QPushButton()
        btn.setFixedSize(44, 44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Clique para escolher uma cor")
        btn.clicked.connect(lambda _checked, i=index: self._pick_color(i))
        self._swatches.append(btn)
        return btn

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _pick_color(self, index: int) -> None:
        """Abre o seletor de cor customizado (mesmo cabeçalho do app) para um slot."""
        current = QColor(self._settings.get_colors()[index])
        picker = ColorPickerDialog(initial_color=current, parent=self)
        if picker.exec_and_get_color() is not None:
            chosen = picker.selected_color()
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
                    border-radius: 22px; /* Metade de 44 para garantir círculo perfeito */
                    /* Substituído o preto genérico por borda fina no tom pastel dourado */
                    border: 2px solid #f3e1ae; 
                }}
                QPushButton:hover {{
                    /* Ao passar o mouse, a borda do círculo se destaca no marrom médio */
                    border: 2px solid #c69868;
                }}
                """
            )

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def _handle_close(self) -> None:
        """Marca como fechado e esconde a janela (compatível com exec())."""
        self.hide()
        self._closed_signal.emit()

    def exec(self) -> None:
        """Exibe o diálogo de forma modal, bloqueando até ser fechado.

        Como FramelessPanel é um QWidget (não QDialog), usamos um
        QEventLoop conectado ao sinal de fechamento, para simular o
        comportamento bloqueante que o restante do código (MainWindow)
        espera de `dialog.exec()`, sem recorrer a polling.
        """
        loop = QEventLoop()
        self._closed_signal.connect(loop.quit)
        self.show()
        loop.exec()
