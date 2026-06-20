"""Conversor leve de markdown básico para HTML, sem dependências externas.

Suporta apenas o subconjunto necessário para as notas do StickyDesk:
negrito, itálico, listas com marcador e caixas de seleção (checkbox).
"""

import re
import html


def markdown_to_html(text: str) -> str:
    """Converte markdown básico em HTML para exibição na nota.

    Suporta:
        **negrito**
        *itálico*
        - item de lista (ou * item)
        [ ] tarefa pendente
        [x] tarefa concluída

    Args:
        text: Texto em markdown bruto, como digitado pelo usuário.

    Returns:
        HTML equivalente, seguro para uso em QTextEdit.setHtml().
    """
    if not text:
        return ""

    lines = text.split("\n")
    html_lines: list[str] = []
    in_list = False

    for raw_line in lines:
        line = html.escape(raw_line)
        stripped = line.strip()

        checkbox_match = re.match(r"^[-*]?\s*\[( |x|X)\]\s*(.*)$", stripped)
        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)

        if checkbox_match:
            if not in_list:
                html_lines.append("<ul style='margin:0; padding-left:18px;'>")
                in_list = True
            checked = checkbox_match.group(1).lower() == "x"
            label = _apply_inline(checkbox_match.group(2))
            symbol = "☑" if checked else "☐"
            style = "text-decoration:line-through; opacity:0.6;" if checked else ""
            html_lines.append(
                f"<li style='list-style:none; {style}'>{symbol} {label}</li>"
            )
            continue

        if bullet_match:
            if not in_list:
                html_lines.append("<ul style='margin:0; padding-left:18px;'>")
                in_list = True
            label = _apply_inline(bullet_match.group(1))
            html_lines.append(f"<li>{label}</li>")
            continue

        if in_list:
            html_lines.append("</ul>")
            in_list = False

        if stripped == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p style='margin:2px 0;'>{_apply_inline(line)}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def _apply_inline(text: str) -> str:
    """Aplica negrito e itálico inline a um trecho já escapado de HTML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    return text
