# StickyDesk

> Post-its digitais para sua área de trabalho.

StickyDesk é uma aplicação desktop para Windows que permite criar e organizar notas flutuantes diretamente na área de trabalho, simulando a experiência dos tradicionais post-its físicos.

O objetivo do projeto é fornecer uma ferramenta simples, leve e prática para anotações rápidas, lembretes e organização de tarefas diárias.

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

# 📂 Estrutura do Projeto

```text
stickydesk
│
├── app
│   ├── ui
│   ├── models
│   ├── services
│   └── storage
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

## Instalação

```bash
git clone https://github.com/seu-usuario/stickydesk.git

cd stickydesk
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute:

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

# 🎯 Objetivo

Este projeto nasceu da necessidade de uma ferramenta simples para organização pessoal, permitindo manter lembretes visíveis durante o trabalho sem depender de aplicações pesadas ou serviços externos.

Além de resolver um problema real do dia a dia, o projeto serve como estudo de desenvolvimento desktop utilizando Python.

---

# 🛣️ Roadmap

## Versão 1.0

* [ ] Criar notas
* [ ] Editar conteúdo
* [ ] Arrastar pela tela
* [ ] Persistência local
* [ ] Personalização de cores

## Versão 1.1

* [ ] Pesquisa
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

# 📸 Capturas de Tela

Em breve.

---

# 🤝 Contribuições

Sugestões, melhorias e correções são bem-vindas.

---

# 📄 Licença

Este projeto está licenciado sob a licença MIT.
