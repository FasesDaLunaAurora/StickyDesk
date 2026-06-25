"""Seletor de cor customizado, com o mesmo cabeçalho visual do app.

Envolve o QColorDialog nativo do Qt (roda de espectro, sliders RGB/HSV,
campo HTML) numa janela sem moldura do Windows, substituindo a barra de
título do sistema por um cabeçalho consistente com o restante do app.
"""

from __future__ import annotations

from PySide6.QtCore import QEventLoop, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QWidget

from app.ui.frameless_panel import FramelessPanel


class ColorPickerDialog(FramelessPanel):
    """Diálogo de seleção de cor com cabeçalho customizado.

    Mantém o seletor de cor nativo do Qt (roda espectral, sliders, campo
    de cor HTML) intacto por dentro, trocando apenas a moldura externa
    da janela pelo mesmo design usado no painel principal e em outros
    diálogos do app.

    Args:
        initial_color: Cor pré-selecionada ao abrir o diálogo.
    """

    def __init__(self, initial_color: QColor, parent: QWidget | None = None) -> None:
        super().__init__(
            title="Escolha uma cor para este slot",
            on_close=self._handle_cancel,
            parent=parent,
        )
        self._result: QColor | None = None
        self._loop = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._picker = self._build_picker(initial_color)
        self.content_layout.setContentsMargins(16, 10, 16, 16)
        self.content_layout.addWidget(self._picker)

        self.adjustSize()

    # ------------------------------------------------------------------
    # Construção do seletor nativo embutido
    # ------------------------------------------------------------------

    def _build_picker(self, initial_color: QColor) -> QColorDialog:
        """Cria o QColorDialog nativo, sem moldura própria, embutido aqui dentro."""
        picker = QColorDialog(initial_color, self)
        picker.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        picker.setOption(QColorDialog.ColorDialogOption.NoButtons, False)
        picker.setWindowFlags(Qt.WindowType.Widget)
        picker.colorSelected.connect(self._handle_accept)
        picker.rejected.connect(self._handle_cancel)
        self._apply_picker_style(picker)
        return picker

    def _apply_picker_style(self, picker: QColorDialog) -> None:
        """Sobrescreve o visual nativo do Windows para combinar com o app.

        O QColorDialog herda o tema do sistema operacional por padrão
        (incluindo tints de cor do Windows), então cada componente interno
        precisa de uma regra explícita para não destoar do restante do app.
        """
        picker.setStyleSheet(
        """
        QColorDialog {
            /* Fundo creme claro e limpo oficial */
            background-color: #fff4df;
        }
        QColorDialog QLabel {
            /* Textos e legendas em marrom escuro sofisticado */
            color: #a2835e;
            font-family: "Segoe UI";
            font-size: 9.5pt;
            background: transparent;
        }
        QColorDialog QGroupBox {
            background: transparent;
            border: none;
            margin-top: 6px;
            font-family: "Segoe UI";
            font-size: 9.5pt;
            /* Cabeçalhos de grupos de cores em marrom escuro */
            color: #a2835e;
        }
        QColorDialog QAbstractSpinBox {
            /* Campos numéricos com fundo cinza-claro das notas */
            background: #f1f1f1;
            /* Borda sutil em ouro-pastel */
            border: 1px solid #f3e1ae;
            border-radius: 6px;
            padding: 3px 6px;
            /* Digitação em marrom médio para alta legibilidade */
            color: #c69868;
            font-family: "Segoe UI";
        }
        QColorDialog QAbstractSpinBox:focus {
            /* Campo focado ganha contorno em marrom médio */
            border: 1px solid #c69868;
        }
        QColorDialog QLineEdit {
            /* Campo de texto (como o código HEX) com fundo cinza-claro */
            background: #f1f1f1;
            /* Borda em ouro-pastel */
            border: 1px solid #f3e1ae;
            border-radius: 6px;
            padding: 4px 8px;
            /* Texto em marrom médio */
            color: #c69868;
            font-family: "Segoe UI";
        }
        QColorDialog QLineEdit:focus {
            /* Campo de texto focado ganha contorno em marrom médio */
            border: 1px solid #c69868;
        }
        
        /* =================================================================
        BOTÕES DO DIÁLOGO: Alinhados exatamente ao padrão do "Restaurar"
        ================================================================= */
        QColorDialog QPushButton {
            background: #c69868;
            color: #fff4df;
            border: none;
            border-radius: 8px;          /* Ajustado de 6px para 8px */
            padding: 8px 12px;           /* Ajustado de 7px 16px para 8px 12px */
            font-family: "Segoe UI";
            font-size: 9.5pt;
        }
        QColorDialog QPushButton:hover {
            background: #a2835e;
        }
        """
    )



    # ------------------------------------------------------------------
    # Resultado
    # ------------------------------------------------------------------

    def _handle_accept(self, color: QColor) -> None:
        """Guarda a cor escolhida e fecha o diálogo."""
        self._result = color
        self._finish()

    def _handle_cancel(self) -> None:
        """Fecha o diálogo sem aplicar nenhuma cor nova."""
        self._result = None
        self._finish()

    def _finish(self) -> None:
        """Esconde a janela e libera o loop modal de `exec_and_get_color()`."""
        self.hide()
        if self._loop is not None:
            self._loop.quit()

    # ------------------------------------------------------------------
    # API pública (substitui QColorDialog.getColor)
    # ------------------------------------------------------------------

    def exec_and_get_color(self) -> QColor | None:
        """Exibe o diálogo de forma modal e retorna a cor escolhida.

        Returns:
            A cor selecionada, ou None se o usuário cancelou/fechou sem
            escolher uma cor válida.
        """
        self._loop = QEventLoop()
        self.show()
        self._loop.exec()
        self._loop = None
        return self._result

    def selected_color(self) -> QColor:
        """Retorna a última cor escolhida (válida apenas após exec_and_get_color)."""
        return self._result or QColor()
