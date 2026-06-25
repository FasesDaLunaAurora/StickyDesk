"""Editor de texto rich-text com formatação markdown aplicada em tempo real.

Diferente de um preview separado, este editor nunca guarda os marcadores
de markdown (**, *, -, [ ]) no documento — eles são consumidos no momento
em que o padrão é reconhecido, e a formatação correspondente (negrito,
itálico, marcador de lista, caixa de seleção) é aplicada diretamente como
atributo de caractere/bloco, ao estilo de um editor rich-text comum
(Google Docs, Word).
"""

from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QFont,
    QKeyEvent,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
)
from PySide6.QtWidgets import QTextEdit

# Padrões reconhecidos ao terminar de digitar o caractere de fechamento.
# Negrito é checado antes de itálico para não confundir ** com *.
_BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*$")
_ITALIC_PATTERN = re.compile(r"(?<!\*)\*(.+?)\*(?!\*)$")

# Padrões reconhecidos ao digitar espaço no início da linha.
_BULLET_PATTERN = re.compile(r"^[-*]\s$")
_CHECKBOX_PATTERN = re.compile(r"^\[( |x|X)\]\s$")


class LiveMarkdownEditor(QTextEdit):
    """QTextEdit que converte markdown em formatação rich-text ao digitar.

    O conteúdo é sempre persistido como HTML (via `toHtml()`), já que não
    sobra markdown bruto depois que os marcadores são consumidos.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._checkbox_positions: list[int] = []

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Intercepta cada tecla para detectar e aplicar formatação ao vivo."""
        super().keyPressEvent(event)

        key = event.key()
        text = event.text()

        if key in (Qt.Key.Key_Space,):
            self._try_apply_line_start_formatting()
        elif text in ("*",):
            self._try_apply_inline_formatting()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._continue_list_on_new_line()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Permite alternar uma caixa de seleção ao clicar sobre o símbolo."""
        cursor = self.cursorForPosition(event.pos())
        block = cursor.block()
        block_text = block.text()

        if block_text.startswith(("☐", "☑")) and cursor.positionInBlock() <= 1:
            self._toggle_checkbox(block)
            return

        super().mousePressEvent(event)

    # ------------------------------------------------------------------
    # Formatação inline: **negrito** e *itálico*
    # ------------------------------------------------------------------

    def _try_apply_inline_formatting(self) -> None:
        """Verifica se o texto antes do cursor fechou negrito ou itálico."""
        cursor = self.textCursor()
        block_text = cursor.block().text()
        pos_in_block = cursor.positionInBlock()
        prefix = block_text[:pos_in_block]

        bold_match = _BOLD_PATTERN.search(prefix)
        if bold_match:
            self._replace_and_format(cursor, bold_match, bold=True)
            return

        italic_match = _ITALIC_PATTERN.search(prefix)
        if italic_match:
            self._replace_and_format(cursor, italic_match, italic=True)

    def _replace_and_format(
        self, cursor: QTextCursor, match: re.Match, bold: bool = False, italic: bool = False
    ) -> None:
        """Substitui o trecho com marcadores pelo texto formatado, sem os símbolos.

        Reposiciona explicitamente o cursor visível ao final do texto
        formatado, já que a remoção dos marcadores desloca as posições
        de caractere no documento.
        """
        block_start = cursor.block().position()
        match_start = block_start + match.start()
        match_end = block_start + match.end()
        inner_text = match.group(1)

        select_cursor = QTextCursor(self.document())
        select_cursor.setPosition(match_start)
        select_cursor.setPosition(match_end, QTextCursor.MoveMode.KeepAnchor)

        char_format = QTextCharFormat()
        if bold:
            char_format.setFontWeight(QFont.Weight.Bold)
        if italic:
            char_format.setFontItalic(True)

        select_cursor.insertText(inner_text, char_format)

        # O cursor visível precisa ser realocado para o fim do texto recém
        # inserido (match_start + len(inner_text)), e não mantido na posição
        # antiga, que agora não corresponde mais ao mesmo ponto no documento.
        new_cursor_pos = match_start + len(inner_text)
        new_cursor = QTextCursor(self.document())
        new_cursor.setPosition(new_cursor_pos)

        normal_format = QTextCharFormat()
        normal_format.setFontWeight(QFont.Weight.Normal)
        normal_format.setFontItalic(False)
        new_cursor.setCharFormat(normal_format)
        self.setTextCursor(new_cursor)

    # ------------------------------------------------------------------
    # Formatação de início de linha: listas e caixas de seleção
    # ------------------------------------------------------------------

    def _try_apply_line_start_formatting(self) -> None:
        """Verifica se o início da linha atual formou um marcador de lista/tarefa."""
        cursor = self.textCursor()
        block_text = cursor.block().text()
        pos_in_block = cursor.positionInBlock()
        prefix = block_text[:pos_in_block]

        if _CHECKBOX_PATTERN.match(prefix):
            self._convert_prefix_to_checkbox(cursor, prefix)
        elif _BULLET_PATTERN.match(prefix):
            self._convert_prefix_to_bullet(cursor, prefix)

    def _convert_prefix_to_bullet(self, cursor: QTextCursor, prefix: str) -> None:
        """Remove o marcador '- ' digitado e aplica uma lista com marcador nativo."""
        block_start = cursor.block().position()
        select_cursor = QTextCursor(self.document())
        select_cursor.setPosition(block_start)
        select_cursor.setPosition(block_start + len(prefix), QTextCursor.MoveMode.KeepAnchor)
        select_cursor.removeSelectedText()

        list_format = QTextListFormat()
        list_format.setStyle(QTextListFormat.Style.ListDisc)
        list_format.setIndent(1)
        select_cursor.createList(list_format)

        # Reposiciona o cursor visível no início do item de lista recém-criado
        self.setTextCursor(select_cursor)

    def _convert_prefix_to_checkbox(self, cursor: QTextCursor, prefix: str) -> None:
        """Remove o marcador '[ ] ' digitado e insere um símbolo de caixa clicável."""
        checked = prefix.strip().lower().startswith("[x")
        block_start = cursor.block().position()

        select_cursor = QTextCursor(self.document())
        select_cursor.setPosition(block_start)
        select_cursor.setPosition(block_start + len(prefix), QTextCursor.MoveMode.KeepAnchor)
        select_cursor.removeSelectedText()

        symbol = "☑ " if checked else "☐ "
        char_format = QTextCharFormat()
        if checked:
            char_format.setFontStrikeOut(True)
            char_format.setForeground(Qt.GlobalColor.gray)
        select_cursor.insertText(symbol, char_format)

        # O restante da linha (a digitar) volta ao normal, sem strikethrough
        normal_format = QTextCharFormat()
        normal_format.setFontStrikeOut(False)
        select_cursor.setCharFormat(normal_format)
        self.setTextCursor(select_cursor)

    def _continue_list_on_new_line(self) -> None:
        """Mantém o cursor pronto para novo item ao pressionar Enter em checkbox."""
        # Listas com marcador nativo (QTextList) já continuam automaticamente.
        # Checkboxes são apenas símbolos de texto, então não há continuação
        # automática — cada linha de tarefa exige digitar "[ ] " novamente.
        return

    def _toggle_checkbox(self, block) -> None:
        """Alterna o estado marcado/desmarcado de uma caixa de seleção clicada."""
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)

        current_char = block.text()[:1]
        is_checked = current_char == "☑"
        new_symbol = "☐" if is_checked else "☑"

        char_format = QTextCharFormat()
        char_format.setFontStrikeOut(not is_checked)
        if not is_checked:
            char_format.setForeground(Qt.GlobalColor.gray)
        else:
            char_format.setForeground(Qt.GlobalColor.black)

        cursor.insertText(new_symbol, char_format)

        # Aplica strikethrough/cor ao restante do texto da linha também
        rest_cursor = QTextCursor(block)
        rest_cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        rest_cursor.movePosition(QTextCursor.MoveOperation.NextCharacter)
        rest_cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)

        rest_format = QTextCharFormat()
        rest_format.setFontStrikeOut(not is_checked)
        rest_format.setForeground(
            Qt.GlobalColor.gray if not is_checked else Qt.GlobalColor.black
        )
        rest_cursor.mergeCharFormat(rest_format)
