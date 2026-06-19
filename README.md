# StickyDesk

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![PySide6](https://img.shields.io/badge/PySide6-Qt-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-orange)

> Post-its digitais para sua área de trabalho.
> **Versão atual: v1.1.0**

StickyDesk é uma aplicação desktop desenvolvida em Python e PySide6 que permite criar post-its digitais diretamente na área de trabalho do Windows.

Projetado para ser leve, rápido e intuitivo, o StickyDesk ajuda a organizar lembretes, ideias e tarefas sem interromper o fluxo de trabalho.

---

# 📸 Demonstração

Em breve.

<!-- Exemplo futuro -->

<!-- ![StickyDesk Demo](docs/demo.gif) -->

---

# ✨ Funcionalidades

## MVP

* Criar post-its
* Editar conteúdo em tempo real
* Arrastar notas pela tela
* Personalizar cores
* Salvamento automático
* Persistência local
* Reabertura automática das notas salvas

---

## Funcionalidades Planejadas

* Atalhos de teclado
* Suporte a Markdown
* Checklists
* Exportação de notas

---

## Novidades da v1.1.0

- 🖥️ **Atalho na área de trabalho** — duplo clique abre o app e reabre as notas salvas
- 🟰 **Fechar ≠ Excluir** — fechar uma nota (botão `—`) apenas oculta a janela; a nota continua salva e reaparece da próxima vez que o app abrir ou ao clicar em *Mostrar todas as notas*
- 🗑️ **Excluir permanentemente** — botão `✕` agora pede confirmação antes de apagar a nota para sempre
- 📝 **Título no cabeçalho** — cada nota tem um campo de título editável, salvo junto com o conteúdo
- 💾 **Persistência reforçada** — ao fechar o app pelo menu da bandeja, todo conteúdo e título pendentes são salvos antes de encerrar
- 🔌 **Sobrevive a reinício do PC** — os dados ficam em `data/notes.json`, lidos com caminho absoluto (não depende mais de qual pasta você estava ao abrir o terminal)

# 🖥️ Tecnologias

* Python
* PySide6
* JSON (persistência local)

---

# 🏗️ Arquitetura

O projeto segue uma arquitetura simples baseada em separação de responsabilidades, facilitando manutenção, testes e futuras expansões.

```text
UI
 ├── Interface gráfica
 ├── Componentes visuais
 └── Eventos do usuário

Services
 ├── Regras de negócio
 ├── Manipulação das notas
 └── Fluxos da aplicação

Models
 ├── Estruturas de dados
 └── Representação das notas

Storage
 ├── Leitura de arquivos
 ├── Escrita de arquivos
 └── Persistência JSON
```

---

# 📂 Estrutura do Projeto

```
stickydesk/
│
├── app/
│   ├── models/
│   │   └── note.py           # Dataclass Note — domínio puro (id, x, y, color, content, title, visible)
│   │
│   ├── services/
│   │   └── note_service.py   # CRUD, geração de ID, paleta de cores, visibilidade
│   │
│   ├── storage/
│   │   └── json_storage.py   # Leitura/escrita no arquivo JSON
│   │
│   └── ui/
│       ├── main_window.py    # Systray + coordenação dos widgets
│       └── sticky_note.py    # Widget visual de cada nota (título, fechar, excluir)
│
├── data/
│   └── notes.json            # Persistência local (criado automaticamente)
│
├── main.py                   # Ponto de entrada + DI manual + caminho absoluto do JSON
├── StickyDesk.bat            # Launcher sem console, usado pelo atalho
├── criar_atalho.ps1          # Script que gera o atalho na Área de Trabalho
└── requirements.txt
```
### Fluxo de dados

```
main.py
  └─ instancia JsonStorage + NoteService + MainWindow
        │
        ├─ MainWindow carrega notas com visible=True via NoteService.get_all()
        │    └─ para cada Note visível → cria StickyNoteWidget
        │
        └─ Usuário interage com StickyNoteWidget
             ├─ on_content_change  → NoteService.update_content()   → JsonStorage.save()
             ├─ on_title_change    → NoteService.update_title()     → JsonStorage.save()
             ├─ on_position_change → NoteService.update_position()  → JsonStorage.save()
             ├─ on_color_change    → NoteService.update_color()     → JsonStorage.save()
             ├─ on_close           → NoteService.set_visibility(False) → JsonStorage.save()
             └─ on_delete          → NoteService.delete()           → JsonStorage.save()
```
---

### Princípios seguidos

- **Separação de camadas**: a UI nunca acessa o JSON diretamente
- **Fechar vs. Excluir são operações distintas**: fechar é uma mudança de estado (`visible=False`), excluir é destrutivo e pede confirmação
- **Debounce de auto-save**: texto e título são salvos 500 ms após parar de digitar (evita I/O excessivo)
- **Caminho absoluto para o JSON**: funciona igual seja chamado via terminal, atalho ou outro processo
- **DI manual em `main.py`**: dependências são compostas externamente, facilitando testes
- **Sem estado global**: cada widget é independente e se comunica via callbacks

---

### Paleta de cores disponível

| Cor | Hex |
|---|---|
| Amarelo suave | `#fff176` |
| Laranja suave | `#ffcc80` |
| Verde suave | `#a5d6a7` |
| Azul suave | `#90caf9` |
| Lilás suave | `#ce93d8` |

---

# 🚀 Executando o Projeto

### Clone o repositório

```bash
git clone https://github.com/seu-usuario/stickydesk.git
```

### Entre na pasta do projeto

```bash
cd stickydesk
```

### Crie o ambiente virtual

```bash
python -m venv .venv
```

### Ative o ambiente virtual

```bash
.\.venv\Scripts\Activate.ps1
```

### Instale/atualize as dependências

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Execute a aplicação

```bash
python main.py
```
> Se o comando `python` não estiver funcionando, use o caminho completo do executável do Python que você instalou, por exemplo:
>
> ```powershell
> C:\Users\SeuUsuario\AppData\Local\Programs\Python\Python311\python.exe -m venv .venv
> ```
>
> E depois execute com:
>
> ```powershell
> .\.venv\Scripts\python.exe main.py
> ```

---

O ícone de post-it amarelo aparecerá na bandeja. Clique com o botão direito → Nova nota, ou dê duplo clique no ícone para criar rapidamente. <br>

### Criar o atalho na área de trabalho

Depois de instalar as dependências (passo 3 acima), rode uma vez:

```powershell
powershell -ExecutionPolicy Bypass -File criar_atalho.ps1
```

Isso cria **StickyDesk.lnk** na sua Área de Trabalho. A partir daí, basta dar **duplo clique** nele:

- Se for a primeira vez, abre o app com nenhuma nota (ou as que você já tinha)
- Se o app já tiver sido usado antes, todas as notas salvas (e marcadas como visíveis) abrem automaticamente

> O atalho aponta para `StickyDesk.bat`, que usa `pythonw.exe` do ambiente virtual — por isso nenhuma janela de terminal preta aparece.

---

## Execução em Dev

1. Entre na pasta do projeto
```
cd stickydesk
```
2. Crie o ambiente virtual
```
python -m venv .venv
```
4. Ative o ambiente virtual
```
.\.venv\Scripts\Activate.ps1
```
Se o PowerShell bloquear a ativação, rode esta linha uma vez:
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
4. Instale/atualize as dependências
```
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
5. Execute a aplicação
```
python main.py
```

## Como usar

| Ação | Como fazer |
|---|---|
| **Abrir o app** | Duplo clique no atalho da área de trabalho (ou `python main.py`) |
| **Criar nota** | Botão direito no ícone da bandeja → *Nova nota* |
| **Editar título** | Clique no campo de texto no topo da nota e digite |
| **Editar conteúdo** | Clique na área de texto da nota e digite |
| **Mover nota** | Arraste pela barra superior (fora do campo de título) |
| **Trocar cor** | Clique em um dos círculos coloridos na barra |
| **Fechar nota (sem perder)** | Botão `—` no canto superior direito — a nota some da tela, mas fica salva |
| **Reabrir notas fechadas** | Botão direito na bandeja → *Mostrar todas as notas*, ou reabra o app |
| **Excluir nota para sempre** | Botão `✕` → confirme no aviso |
| **Fechar o app (mantém tudo salvo)** | Botão direito na bandeja → *Fechar StickyDesk* |

Todas as alterações são **salvas automaticamente** em `data/notes.json`, e isso independe de você desligar o computador — os dados continuam lá na próxima vez que abrir o app.

---

# 📚 Aprendizados

Este projeto explora conceitos importantes do desenvolvimento desktop moderno com Python:

* Desenvolvimento de interfaces gráficas com PySide6
* Arquitetura em camadas
* Programação orientada a objetos
* Persistência de dados em JSON
* Gerenciamento de estado local
* Manipulação de eventos e interação com o usuário
* Organização e escalabilidade de projetos desktop

---

# 🎯 Objetivo

O StickyDesk nasceu da necessidade de uma ferramenta simples para organização pessoal, permitindo manter lembretes visíveis durante o trabalho sem depender de aplicações pesadas ou serviços externos.

Além de resolver um problema real do dia a dia, o projeto faz parte do meu portfólio de desenvolvimento de software, demonstrando boas práticas de arquitetura, organização de código e desenvolvimento de aplicações desktop com Python.

---

# 🛣️ Roadmap

## Versão 1.1.0

* [ ] Criar notas
* [ ] Editar conteúdo
* [ ] Arrastar pela tela
* [ ] Persistência local
* [ ] Personalização de cores

## Versão 1.2.0

* [ ] Checklists
* [ ] Markdown
* [ ] Atalhos de teclado

## Versão 1.3.0

* [ ] Sincronização entre dispositivos

---

# 🔮 Futuras Evoluções

* Sistema de temas
* Modo escuro
* Agrupamento de notas
* Backup automático
* Sincronização em nuvem
* Integração com calendário
* Notificações nativas do Windows

---

# 🤝 Contribuições

Sugestões, melhorias e correções são bem-vindas.

Caso encontre algum problema ou tenha uma ideia para o projeto, sinta-se à vontade para abrir uma issue.

---

# 📄 Licença

Este projeto está licenciado sob a licença MIT.

---



