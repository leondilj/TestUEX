# UX Spec: Fluxo de Navegação, Wireframes e Identidade Visual (T26)

Source:
- `spec/product.md` — users: **Usuário final (dono da conta)**; persona secundária: avaliador do case (lê o produto via vídeo/README)
- `spec/tasks.md` — task: **T26** (fluxo auth → lista de projetos → projeto → lista/kanban, wireframes de baixa fidelidade, identidade visual)
- `spec/api.md` — endpoints usados: `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, `GET/POST /projects`, `GET/PATCH/DELETE /projects/{id}`, `GET /projects/{id}/tasks`
- `spec/architecture.md` — rotas Next.js: `(auth)/login`, `(auth)/register`, `(app)/projects`, `(app)/projects/[projectId]`

> Escopo deste spec: navegação, layout macro e identidade. Os detalhes de interação do toggle lista/kanban, do formulário de tarefa e do upload de anexos são especificados na **T27** (`ux-spec-task-views-and-form.md`).

---

## 1. User Goal

Entrar no Taskly com o mínimo de atrito, escolher um projeto e enxergar/organizar as tarefas dele no modo de visualização que preferir (lista ou kanban) — sem nunca se perder sobre "onde estou" ou "como volto".

## 2. User Profile

Pessoa organizando o próprio trabalho (não um time). Nível técnico misto — a UI não pode depender de convenções de ferramenta corporativa (sem jargão tipo "sprint", "board", "backlog"). Usa desktop na maior parte do tempo; o layout deve degradar bem até ~375px, mas o alvo primário é ≥1024px (o vídeo de avaliação será gravado em desktop).

---

## 3. Identidade Visual

### Conceito

**"Papel e tinta"** — o Taskly é um caderno pessoal, não um painel corporativo. Fundo quente de papel, tipografia com personalidade no título, uma única cor de destaque (verde-petróleo) usada com parcimônia. Nada de gradientes roxos genéricos, nada de glassmorphism. A sensação-alvo: calmo, focado, artesanal.

### Logo / marca

Wordmark tipográfico `taskly` em minúsculas (Space Grotesk, weight 600), com um **check ✓** desenhado como acento sobre o "y" ou à esquerda do wordmark, na cor de destaque. Sem imagem/asset externo — o logo é texto + um SVG inline de check (traço 2.5px, cantos arredondados). Favicon: o check sozinho em `#0F766E` sobre `#FAF8F5`.

### Paleta (tokens)

| Token | Hex | Uso | Contraste |
|---|---|---|---|
| `paper` | `#FAF8F5` | fundo da aplicação | — |
| `surface` | `#FFFFFF` | cards, modais, inputs | — |
| `ink` | `#1C1B1A` | texto primário | 16.5:1 sobre paper |
| `ink-muted` | `#57534E` | texto secundário, labels | 7.0:1 sobre paper |
| `accent` | `#0F766E` | CTAs, links, foco, marca | 5.6:1 sobre branco (AA) |
| `accent-hover` | `#115E59` | hover de CTAs | — |
| `line` | `#E7E2DB` | bordas de card, divisores | decorativo |
| `danger` | `#BE123C` | ações destrutivas, erros | 5.9:1 sobre branco (AA) |

**Cores de status da tarefa** (usadas em badges e colunas do kanban — texto sempre no tom `-700` sobre fundo `-50` para garantir AA):

| Status | Rótulo na UI | Texto | Fundo do badge |
|---|---|---|---|
| `not_started` | Não iniciada | `#44403C` | `#F5F5F4` |
| `in_progress` | Em andamento | `#B45309` | `#FFFBEB` |
| `done` | Concluída | `#15803D` | `#F0FDF4` |
| `cancelled` | Cancelada | `#BE123C` | `#FFF1F2` |

Regra: **cor nunca é o único canal** — todo badge de status carrega o rótulo em texto; no kanban o nome da coluna é o rótulo.

### Tipografia

- **Display / títulos / logo:** Space Grotesk (via `next/font/google`), weights 500–700
- **UI / corpo:** Inter (via `next/font/google`), weights 400–600
- Escala: 24px títulos de página · 16px corpo · 14px metadados/labels · 12px apenas para badges
- Datas sempre no formato `dd/mm/aaaa HH:mm` (pt-BR); prazo vencido em `danger` com prefixo "Venceu em"

### Forma e espaçamento

- Radius: 10px em cards e modais, 8px em inputs e botões, pill (999px) em badges de status/tags
- Bordas `1px solid line` em vez de sombras pesadas; sombra apenas em modal/drawer (`0 8px 24px rgba(28,27,26,0.08)`)
- Densidade: espaçamento base 8px; cards de tarefa compactos (título + metadados em 2 linhas)
- Botão primário: fundo `accent`, texto branco. Secundário: borda `line`, texto `ink`. Destrutivo: texto/borda `danger`, nunca fundo vermelho sólido exceto na confirmação final

---

## 4. Mapa de Navegação

```
/                     → redirect (GET /auth/me): 200 → /projects · 401 → /login
├── (auth)  — layout centrado, sem topbar
│   ├── /login        ←→ link cruzado → /register
│   └── /register     — sucesso → login automático → /projects
└── (app)   — layout com topbar, exige sessão (guarda de rota, T29)
    ├── /projects                     — lista de projetos (raiz autenticada)
    └── /projects/[projectId]         — lista/kanban de tarefas do projeto
         └── tarefa abre em DRAWER lateral sobre esta rota (sem rota própria)
```

Regras de navegação:

1. **Guarda de rota:** toda rota `(app)` valida sessão via `GET /auth/me` no carregamento; `401` em qualquer chamada da API → limpar estado e redirecionar para `/login` (sem toast agressivo — a tela de login exibe aviso discreto "Sua sessão expirou, entre novamente")
2. **Usuário logado acessando `/login` ou `/register`** → redirect para `/projects`
3. **Topbar persistente** em `(app)`: logo à esquerda (link para `/projects`), e-mail do usuário + botão "Sair" à direita. Reservar slot de navegação para o item **"Assistente"** (T49) — não renderizar por enquanto
4. **Breadcrumb** na página do projeto: `Projetos / <nome do projeto>` — "Projetos" é link de volta; é o único nível de profundidade do app, então não há breadcrumb em nenhuma outra tela
5. **Tarefa não tem rota própria** (decisão): detalhe/edição abre em drawer lateral sobre `/projects/[projectId]`, preservando o contexto da lista/kanban e o estado de filtros. Deep-link em tarefa fica fora do escopo mínimo (registrado em Open Questions)

---

## 5. Flow

### Fluxo A — Primeiro acesso (cadastro)

Step 1: usuário chega em `/` sem sessão
  - System response: redirect para `/login`

Step 2: `/login`
  - User sees: card centrado com logo, campos **E-mail** e **Senha**, botão primário **"Entrar"**, texto "Não tem conta? **Criar conta**" (link para `/register`)
  - User action: clica em "Criar conta"

Step 3: `/register`
  - User sees: campos **E-mail**, **Senha** (helper text fixo: "Mínimo de 8 caracteres"), botão **"Criar conta"**, link "Já tem conta? **Entrar**"
  - User action: preenche e submete
  - System response: `POST /auth/register` → em sucesso (201), chama `POST /auth/login` com as mesmas credenciais e redireciona para `/projects` (login automático — não obrigar o usuário a digitar tudo de novo)

Step 4: `/projects` (primeira vez — vazio)
  - User sees: **empty state**: ilustração leve (check da marca), título "Crie seu primeiro projeto", subtítulo "Projetos agrupam suas tarefas — comece com um.", botão primário **"Novo projeto"**
  - User action: clica em "Novo projeto" → modal com campo único **Nome** e botões "Criar" / "Cancelar"
  - System response: `POST /projects` → card do projeto aparece na grade; foco move para o card criado

### Fluxo B — Retorno (sessão persistente)

Step 1: usuário abre o app em `/`
  - System response: `GET /auth/me` retorna 200 → redirect direto para `/projects` (sem flash da tela de login; exibir skeleton da grade enquanto valida)

Step 2: `/projects`
  - User sees: grade de cards de projeto (nome + data de criação + menu ⋯ com "Renomear"/"Excluir"), botão "Novo projeto" no topo direito
  - User action: clica em um card
  - System response: navega para `/projects/[projectId]`

Step 3: `/projects/[projectId]`
  - User sees: breadcrumb `Projetos / <nome>`, toggle **Lista | Kanban** (detalhado na T27), botão primário **"Nova tarefa"**, filtros por status/tag (T35), e as tarefas no modo escolhido
  - User action: alterna visualização, filtra, abre tarefa (drawer) ou cria tarefa
  - System response: preferência de visualização persiste por projeto em `localStorage` (chave `taskly:view:<projectId>`)

Step 4: sair
  - User action: clica em "Sair" na topbar
  - System response: `POST /auth/logout` → redirect para `/login`

### Error States

- Login com credenciais inválidas (`401`) → erro inline acima do botão: **"E-mail ou senha incorretos."** (nunca dizer qual dos dois; não limpar o campo de e-mail)
- Cadastro com e-mail existente (`409`) → erro inline no campo de e-mail: **"Este e-mail já está cadastrado."** + link "Entrar"
- Cadastro com senha curta (`400`) → erro inline no campo de senha: **"A senha precisa ter pelo menos 8 caracteres."** (validar também no cliente antes do submit)
- Projeto inexistente/de outro usuário (`404` em `/projects/[projectId]`) → tela de estado com título **"Projeto não encontrado"**, texto "Ele pode ter sido excluído.", botão "Voltar para projetos"
- Falha de rede em qualquer mutação → toast não bloqueante **"Não foi possível salvar. Tente novamente."** mantendo os dados digitados no formulário
- Excluir projeto → modal de confirmação: título "Excluir projeto?", texto **"As tarefas e anexos de \"<nome>\" serão excluídos permanentemente."**, botões "Cancelar" (padrão) e "Excluir" (danger)

---

## 6. Layout Notes (wireframes de baixa fidelidade)

### `/login` (layout `(auth)` — também vale para `/register`)

```
+--------------------------------------------------+
|                                                  |
|                  ✓ taskly                        |
|                                                  |
|        +------------------------------+          |
|        |  Entrar                      |          |
|        |                              |          |
|        |  E-mail                      |          |
|        |  [........................]  |          |
|        |  Senha                       |          |
|        |  [........................]  |          |
|        |                              |          |
|        |  [        Entrar         ]   |          |
|        |                              |          |
|        |  Não tem conta? Criar conta  |          |
|        +------------------------------+          |
|                                                  |
+--------------------------------------------------+
  fundo `paper`; card `surface` 400px máx, centrado
```

### `/projects`

```
+--------------------------------------------------------------+
| ✓ taskly                          user@email.com  [ Sair ]   |  ← topbar (surface, borda inferior `line`)
+--------------------------------------------------------------+
|  Projetos                               [ + Novo projeto ]   |
|                                                              |
|  +----------------+  +----------------+  +----------------+  |
|  | Website redes… |  | Casa nova      |  | Freelas        |  |
|  | 12 tarefas     |  | 4 tarefas      |  | 0 tarefas      |  |
|  | criado 01/07   |⋯ | criado 28/06   |⋯ | criado 30/06   |⋯ |
|  +----------------+  +----------------+  +----------------+  |
|                                                              |
+--------------------------------------------------------------+
  grade responsiva: 3 col ≥1024px · 2 col ≥640px · 1 col mobile
  ⋯ = menu do card: Renomear · Excluir (danger)
```

> Nota: a contagem "N tarefas" no card depende de dado que `GET /projects` **não retorna hoje** — ver Open Questions. Se não entrar, o card mostra só nome + data.

### `/projects/[projectId]` — modo lista

```
+--------------------------------------------------------------+
| ✓ taskly                          user@email.com  [ Sair ]   |
+--------------------------------------------------------------+
|  Projetos / Website redesign                                 |
|                                                              |
|  [ Lista | Kanban ]   [filtro status ▾] [filtro tag ▾]       |
|                                       [ + Nova tarefa ]      |
|  +--------------------------------------------------------+  |
|  | ● Em andamento  Redesenhar tela de login               |  |
|  |   Criar nova proposta de UI…   ⏰ 28/06 18:00  #design  |  |
|  +--------------------------------------------------------+  |
|  | ○ Não iniciada  Revisar contrato                       |  |
|  |   —                            ⏰ 03/07 18:00           |  |
|  +--------------------------------------------------------+  |
+--------------------------------------------------------------+
  linha = card clicável (abre drawer); badge de status à esquerda
```

### `/projects/[projectId]` — modo kanban

```
+--------------------------------------------------------------+
|  Projetos / Website redesign                                 |
|  [ Lista | Kanban ]   [filtros]           [ + Nova tarefa ]  |
|                                                              |
|  Não iniciada (2)  Em andamento (1)  Concluída (3)  Cancel…  |
|  +------------+    +------------+    +------------+  +-----+ |
|  | Revisar    |    | Redesenhar |    | Setup CI   |  |     | |
|  | contrato   |    | tela login |    +------------+  |     | |
|  | ⏰03/07    |    | ⏰28/06    |    | Docker     |  |     | |
|  | [status ▾] |    | [status ▾] |    +------------+  |     | |
|  +------------+    +------------+                            |
|  +------------+                                              |
+--------------------------------------------------------------+
  4 colunas fixas (uma por status); SEM drag-and-drop (ADR-004) —
  mudança de status via [status ▾] no card (interação detalhada na T27)
  em <1024px: colunas viram scroll horizontal com snap
```

### Drawer de tarefa (sobre a página do projeto)

```
+---------------------------- +==============================+
| (página do projeto,         ‖  Redesenhar tela de login  ✕ ‖
|  escurecida por overlay)    ‖  [Em andamento ▾]  #design   ‖
|                             ‖  ⏰ 28/06/2026 18:00          ‖
|                             ‖  ---------------------------- ‖
|                             ‖  descrição, anexos, ações…    ‖
|                             ‖  (conteúdo detalhado na T27)  ‖
+---------------------------- +==============================+
  ~480px, desliza da direita; fecha com ✕, Esc ou clique no overlay
```

Hierarquia de informação (ordem do que o olho encontra): **nome do projeto → toggle de visualização → tarefas → ação de criar**. O CTA "Nova tarefa" fica sempre visível acima da dobra, alinhado à direita da barra de controles.

---

## 7. Accessibility Notes

- **Landmarks:** topbar em `<header>` com `<nav aria-label="Principal">`; conteúdo em `<main>`; um único `<h1>` por página (nome da página ou do projeto)
- **ARIA:**
  - toggle Lista/Kanban: `role="tablist"` com `aria-selected` (detalhes na T27)
  - kanban: cada coluna é `<section aria-labelledby>` com heading próprio (`<h2>` visualmente estilizado como título de coluna) + contagem
  - drawer: `role="dialog" aria-modal="true"` com `aria-labelledby` apontando para o título da tarefa; foco move para o drawer ao abrir e **retorna ao card de origem** ao fechar (focus trap enquanto aberto)
  - menu ⋯ do projeto: `aria-haspopup="menu"`, itens com `role="menuitem"`
  - badges de status: texto visível é suficiente (sem `aria-label` redundante)
- **Teclado:** tudo alcançável por Tab na ordem visual; Esc fecha modal/drawer/menus; Enter/Espaço ativa cards (cards de tarefa são `<button>` ou têm `role="button"` + `tabindex=0`); anel de foco visível de 2px em `accent` sobre qualquer fundo (nunca `outline: none` sem substituto)
- **Contraste:** todos os pares texto/fundo da paleta ≥ 4.5:1 (verificados na tabela da seção 3); placeholder de input em `ink-muted`, nunca mais claro
- **Formulários:** todo input com `<label>` visível (sem placeholder-como-label); erros ligados via `aria-describedby` e anunciados com `role="alert"`
- **Screen reader:** mudanças assíncronas (tarefa criada, status alterado, erro de rede) anunciadas em live region `aria-live="polite"` global; título do documento por rota: "Entrar — Taskly", "Projetos — Taskly", "<nome do projeto> — Taskly"

---

## 8. Open Questions

1. **Contagem de tarefas no card de projeto:** `GET /projects` não retorna `task_count`. Vale a pena expor (campo agregado barato via `COUNT`)? → decidir com o project-manager/python-developer; o wireframe funciona sem isso. **Não bloqueia T26.**
2. **Deep-link de tarefa** (ex.: `?task=<id>` na URL do projeto para abrir o drawer): fora do escopo mínimo; registrar como melhoria se sobrar tempo.
3. **Dark mode:** fora do escopo dos 3 dias (identidade definida só em tema claro). Tokens já nomeados de forma neutra para permitir extensão futura.

## 9. Handoff to Frontend Engineer

- Implementar os tokens da seção 3 como theme do Tailwind (`tailwind.config`/`@theme`) — nomes exatos: `paper`, `surface`, `ink`, `ink-muted`, `accent`, `accent-hover`, `line`, `danger` + tokens de status
- Fontes via `next/font/google` (Space Grotesk + Inter) — sem `<link>` externo
- Layouts: `(auth)/layout.tsx` (card centrado) e `(app)/layout.tsx` (topbar + guarda de sessão via `GET /auth/me`); redirect raiz conforme seção 4
- Copy exata dos erros e confirmações conforme seção 5 (Error States) — não parafrasear
- Drawer de tarefa e toggle Lista/Kanban: estrutura conforme seção 6; **comportamento detalhado virá na T27** — não inventar interações além do especificado aqui
- Persistência da visualização por projeto: `localStorage`, chave `taskly:view:<projectId>`, default `lista`
- Sem drag-and-drop no kanban (ADR-004) — não instalar lib de DnD
