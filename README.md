# StickyDesk

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![PySide6](https://img.shields.io/badge/PySide6-Qt-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-orange)

> Post-its digitais para sua área de trabalho.

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

* Categorias
* Pesquisa de notas
* Fixar sempre visível
* Atalhos de teclado
* Suporte a Markdown
* Checklists
* Lembretes
* Tags
* Exportação de notas

---

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

```text
stickydesk
│
├── app
│   ├── models
│   │   └── note.py
│   │
│   ├── services
│   │   └── note_service.py
│   │
│   ├── storage
│   │   └── json_storage.py
│   │
│   └── ui
│       ├── main_window.py
│       └── sticky_note.py
│
├── data
│   └── notes.json
│
├── assets
│
├── tests
│
├── main.py
│
└── requirements.txt
```

---

# 🚀 Executando o Projeto

## Clone o repositório

```bash
git clone https://github.com/seu-usuario/stickydesk.git

cd stickydesk
```

## Instale as dependências

```bash
pip install -r requirements.txt
```

## Execute a aplicação

```bash
python main.py
```

---

# 💾 Persistência

As notas são armazenadas localmente em formato JSON.

Exemplo:

```json
[
  {
    "id": 1,
    "x": 320,
    "y": 180,
    "color": "#fff176",
    "content": "Fazer deploy"
  }
]
```

Ao reiniciar a aplicação, todas as notas são restauradas automaticamente.

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

## Versão 1.0

* [ ] Criar notas
* [ ] Editar conteúdo
* [ ] Arrastar pela tela
* [ ] Persistência local
* [ ] Personalização de cores

## Versão 1.1

* [ ] Pesquisa de notas
* [ ] Categorias
* [ ] Atalhos de teclado

## Versão 1.2

* [ ] Checklists
* [ ] Markdown
* [ ] Tags

## Versão 2.0

* [ ] Notificações
* [ ] Lembretes agendados
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
