"""Serviço de domínio: operações CRUD sobre notas."""

from app.models.note import Note
from app.storage.json_storage import JsonStorage

# Paleta de cores disponíveis para novas notas (ciclo automático)
NOTE_COLORS: list[str] = [
    "#fff176",  # amarelo suave
    "#ffcc80",  # laranja suave
    "#a5d6a7",  # verde suave
    "#90caf9",  # azul suave
    "#ce93d8",  # lilás suave
]


class NoteService:
    """Orquestra criação, atualização e exclusão de notas.

    Args:
        storage: Instância da camada de persistência.
    """

    def __init__(self, storage: JsonStorage) -> None:
        self._storage = storage
        self._notes: list[Note] = self._storage.load()
        self._color_index: int = 0

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def get_all(self) -> list[Note]:
        """Retorna todas as notas carregadas."""
        return list(self._notes)

    def get_by_id(self, note_id: int) -> Note | None:
        """Retorna a nota com o id informado, ou None se não encontrada."""
        return next((n for n in self._notes if n.id == note_id), None)

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------

    def create(self, x: int = 100, y: int = 100) -> Note:
        """Cria uma nova nota com posição inicial e cor automática.

        Args:
            x: Posição horizontal inicial.
            y: Posição vertical inicial.

        Returns:
            A nota recém-criada.
        """
        new_id = self._next_id()
        color = NOTE_COLORS[self._color_index % len(NOTE_COLORS)]
        self._color_index += 1

        note = Note(id=new_id, x=x, y=y, color=color, content="")
        self._notes.append(note)
        self._persist()
        return note

    def update_content(self, note_id: int, content: str) -> None:
        """Atualiza o conteúdo textual de uma nota."""
        note = self._require(note_id)
        note.content = content
        self._persist()

    def update_title(self, note_id: int, title: str) -> None:
        """Atualiza o título exibido no cabeçalho de uma nota."""
        note = self._require(note_id)
        note.title = title
        self._persist()

    def set_visibility(self, note_id: int, visible: bool) -> None:
        """Marca uma nota como visível ou oculta (sem excluí-la)."""
        note = self._require(note_id)
        note.visible = visible
        self._persist()

    def update_position(self, note_id: int, x: int, y: int) -> None:
        """Atualiza a posição de uma nota na tela."""
        note = self._require(note_id)
        note.x = x
        note.y = y
        self._persist()

    def update_color(self, note_id: int, color: str) -> None:
        """Atualiza a cor de fundo de uma nota."""
        note = self._require(note_id)
        note.color = color
        self._persist()

    def delete(self, note_id: int) -> None:
        """Remove permanentemente uma nota."""
        self._notes = [n for n in self._notes if n.id != note_id]
        self._persist()

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _next_id(self) -> int:
        """Gera o próximo id disponível (max existente + 1)."""
        return max((n.id for n in self._notes), default=0) + 1

    def _require(self, note_id: int) -> Note:
        """Retorna a nota ou lança ValueError se não encontrada."""
        note = self.get_by_id(note_id)
        if note is None:
            raise ValueError(f"Nota com id={note_id} não encontrada.")
        return note

    def _persist(self) -> None:
        """Delega a persistência para a camada de storage."""
        self._storage.save(self._notes)
