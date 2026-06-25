"""Modelo de domínio para uma nota adesiva."""

from dataclasses import dataclass, field


@dataclass
class Note:
    """Representa uma nota adesiva.

    Attributes:
        id: Identificador único da nota.
        x: Posição horizontal na tela.
        y: Posição vertical na tela.
        width: Largura atual da janela da nota.
        height: Altura atual da janela da nota.
        color: Cor de fundo em formato hexadecimal.
        content: Texto da nota (markdown bruto).
        title: Título exibido no cabeçalho da nota.
        visible: Indica se a janela da nota deve ser exibida ao abrir o app.
    """

    id: int
    x: int
    y: int
    color: str
    content: str = field(default="")
    title: str = field(default="")
    visible: bool = field(default=True)
    width: int = field(default=250)
    height: int = field(default=270)

    def to_dict(self) -> dict:
        """Serializa a nota para um dicionário compatível com JSON."""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "content": self.content,
            "title": self.title,
            "visible": self.visible,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        """Desserializa uma nota a partir de um dicionário JSON."""
        return cls(
            id=data["id"],
            x=data["x"],
            y=data["y"],
            color=data["color"],
            content=data.get("content", ""),
            title=data.get("title", ""),
            visible=data.get("visible", True),
            width=data.get("width", 250),
            height=data.get("height", 270),
        )
