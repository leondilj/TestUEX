# UX Spec: Toggle Lista/Kanban, Formulário de Tarefa e Upload de Anexos (T27)

Source:
- `spec/product.md` — users: **Usuário final (dono da conta)**; requisito explícito: todos os campos da tarefa editáveis após a criação; alternância livre lista ↔ kanban
- `spec/tasks.md` — task: **T27** (depende da T26 — `ux-spec-navigation-and-identity.md`, que define navegação, drawer e identidade)
- `spec/api.md` — endpoints usados: `GET /projects/{id}/tasks` (filtros `status`/`tag`), `POST /projects/{id}/tasks`, `GET/PATCH/DELETE /tasks/{id}`, `POST/GET /tasks/{id}/attachments`, `GET /attachments/{id}/download`, `DELETE /attachments/{id}`
- `spec/data-model.md` — campos da `Task` e `Attachment`; `api/app/config.py` — limites reais: **10MB por arquivo**; tipos: PNG, JPEG, GIF, WebP, PDF, DOC, DOCX, TXT
- `spec/decisions/ADR-004` — sem drag-and-drop; ordenação fixa por `created_at ASC`; mudança de status por controle explícito no card

> Este spec detalha as interações que a T26 deixou em nível de wireframe. Tokens de cor, tipografia, drawer e copy de navegação: ver `ux-spec-navigation-and-identity.md`.

---

## 1. User Goal

Ver as tarefas do projeto do jeito que preferir (lista corrida ou colunas por status), mudar o status de uma tarefa em um clique, e criar/editar qualquer campo — incluindo anexos — sem sair do contexto do projeto.

---

## 2. Toggle Lista / Kanban

### Controle

Segmented control com dois segmentos — **Lista** e **Kanban** — na barra de controles do projeto (posição definida na T26). Segmento ativo: fundo `accent`, texto branco; inativo: fundo `surface`, texto `ink-muted`, borda `line`.

- Alternar é **instantâneo e client-side**: mesma coleção de tarefas (mesmo fetch), apenas re-renderizada — sem novo request, sem spinner
- A escolha persiste por projeto: `localStorage` chave `taskly:view:<projectId>`, default **Lista** (T26)
- Filtros ativos (status/tag) e o drawer aberto **sobrevivem à alternância** — trocar de visualização nunca descarta estado

### Modo Lista

Uma linha-card por tarefa, ordenadas por `created_at ASC` (mais antiga primeiro — ordenação fixa, ADR-004). Cada linha mostra, nesta ordem:

1. Badge de status (pill com rótulo — cores da T26 §3)
2. **Título** (weight 600, 1 linha com ellipsis)
3. `short_description` (1 linha, `ink-muted`, ellipsis; omitida se vazia — sem placeholder "—" ocupando espaço)
4. Metadados à direita: prazo (`⏰ dd/mm HH:mm`; vencido e não concluída/cancelada → cor `danger`, prefixo "Venceu") · tags (pills neutras `#tag`, máx. 3 visíveis + contador "+2")

Clique/Enter na linha → abre o drawer da tarefa (seção 4). A linha inteira é o alvo clicável (mín. 44px de altura).

**Empty states:**
- Projeto sem tarefas: título **"Nenhuma tarefa ainda"**, subtítulo "Crie a primeira tarefa deste projeto.", botão primário **"+ Nova tarefa"**
- Filtro sem resultados: **"Nenhuma tarefa encontrada"** + "Ajuste os filtros ou limpe-os." + botão de texto **"Limpar filtros"**

### Modo Kanban

4 colunas fixas, sempre nesta ordem: **Não iniciada · Em andamento · Concluída · Cancelada**. Coluna sempre visível mesmo vazia (a estrutura é o mapa mental do usuário — colunas não somem).

- Cabeçalho da coluna: rótulo + contagem `(N)`; cor do texto = cor de status (tom `-700`)
- Card: título (2 linhas máx.) · prazo · até 2 tags · **controle de status** (abaixo)
- Dentro da coluna, cards ordenados por `created_at ASC`
- Coluna vazia: texto discreto `ink-muted` "Sem tarefas" (sem CTA — o CTA global "Nova tarefa" já está na barra)
- `<1024px`: colunas em scroll horizontal com `scroll-snap`, largura de coluna ~280px, indicador de overflow (fade na borda)

### Mudança de status no card (ADR-004 — sem drag-and-drop)

Cada card (kanban **e** lista) tem um controle de status: no kanban é um `<select>` estilizado no rodapé do card; na lista, o próprio badge de status é o gatilho (clique abre o mesmo menu de 4 opções).

Fluxo:

Step 1: usuário abre o menu de status no card
  - User sees: as 4 opções com o rótulo em português; a atual marcada com ✓
  - User action: seleciona outro status
  - System response: **update otimista** — o card muda de coluna (kanban) ou de badge (lista) imediatamente; `PATCH /tasks/{id}` com `{ "status": "<novo>" }` em background

Step 2 (sucesso): nada além da mudança visual — sem toast de sucesso (a movimentação do card É o feedback). Live region anuncia: *"<título> movida para <status>"*

Step 2 (falha — rede ou 400): card **volta** à coluna/badge anterior + toast: **"Não foi possível atualizar o status. Tente novamente."**

O clique no controle de status **não** abre o drawer (stopPropagation) — só o resto do card abre.

### Filtros (T35) × visualizações

- **Filtro por status** — select "Status: Todos ▾" com os 4 status. Na **lista**, filtra as linhas. No **kanban**, exibe apenas a coluna do status selecionado (as outras colapsam); manter o filtro visível deixa óbvio por que as colunas sumiram
- **Filtro por tag** — select "Tag: Todas ▾" populado com as tags distintas das tarefas carregadas do projeto. Filtra cards em ambas as visualizações
- Filtros combinam (E lógico) e são enviados como query params ao `GET /projects/{id}/tasks` (`?status=&tag=`) — refetch a cada mudança
- Filtro ativo: o select ganha borda `accent` + botão "×" para limpar aquele filtro individualmente

---

## 3. Formulário de Tarefa (criar/editar — todos os campos)

Abre no **drawer lateral** definido na T26 (~480px, direita, focus trap, fecha com Esc/✕/overlay). O mesmo drawer serve para criar e editar; o que muda é o título e os dados iniciais.

### Campos (ordem vertical no drawer)

| Campo | Controle | Regras / comportamento |
|---|---|---|
| **Título** * | input texto | obrigatório; erro inline "Informe um título." se vazio no submit; autofocus ao abrir em modo criação |
| **Status** | select (4 opções) | **só no modo edição** — na criação a tarefa nasce `not_started` (contrato do `POST`); não mostrar campo desabilitado, simplesmente omitir |
| **Descrição curta** | input texto com contador | máx. 280 chars; contador "212/280" à direita do label, visível a partir de 200 chars; excedeu → borda `danger` + bloqueia submit |
| **Descrição completa** | textarea auto-expansível | 4 linhas iniciais, cresce até ~12 e depois rola |
| **Prazo** | `<input type="datetime-local">` | opcional; botão de texto "Limpar" ao lado quando preenchido (permite remover o prazo — requisito: tudo editável) |
| **Tags** | chip input | digitar + Enter (ou vírgula) adiciona chip; ✕ no chip ou Backspace com campo vazio remove; input converte para **minúsculas** ao adicionar (espelha a normalização do backend — o usuário vê exatamente o que será salvo); chips duplicados são ignorados silenciosamente |
| **Anexos** | ver seção 4 | só no modo edição (a tarefa precisa de `id`) |

\* = obrigatório. Todos os campos com `<label>` visível (T26 §7).

### Modo criação

Step 1: usuário clica em **"+ Nova tarefa"** na barra do projeto
  - System response: drawer abre com título **"Nova tarefa"**, formulário vazio, foco no campo Título
  - Rodapé do drawer: botão primário **"Criar tarefa"** + botão de texto "Cancelar"

Step 2: usuário preenche e submete
  - System response: `POST /projects/{id}/tasks` → **201**: o drawer **permanece aberto e vira modo edição** da tarefa recém-criada (título do drawer vira o título da tarefa, campo Status e seção Anexos aparecem). Live region: *"Tarefa criada"*. A tarefa já aparece na lista/kanban ao fundo (fim da ordenação — é a mais recente)
  - Racional: anexos exigem a tarefa criada; fechar o drawer e obrigar o usuário a reabrir para anexar seria fricção no fluxo mais comum ("criar tarefa com foto")

Step 3: usuário fecha o drawer quando quiser (✕, Esc, overlay) — não há "salvar e fechar" separado

**Cancelar/fechar com alterações não salvas** (criação ou edição): confirmação inline no rodapé do drawer — texto "Descartar alterações?" + botões "Descartar" (danger) e "Continuar editando". Sem `window.confirm` nativo.

### Modo edição

Step 1: usuário clica em um card/linha
  - System response: drawer abre com `GET /tasks/{id}` (detalhe completo — `full_description` + anexos); skeleton nos campos enquanto carrega
  - Título do drawer = título da tarefa; rodapé: botão primário **"Salvar"** (desabilitado até haver mudança) + botão de texto **"Excluir tarefa"** (danger, alinhado à esquerda)

Step 2: usuário edita qualquer campo e clica em "Salvar"
  - System response: `PATCH /tasks/{id}` com **apenas os campos alterados** → 200: o drawer **fecha**; o card ao fundo atualiza; live region: *"Tarefa salva"* (revisão de 2026-07-02, decisão do usuário — substituiu o estado "Salvo ✓" com drawer aberto). Erros 400 → mensagem inline no campo correspondente (copy do backend traduzida: título vazio → "Informe um título."; status inválido não é alcançável pela UI)
  - Modelo de salvamento: **submit explícito**, não autosave por campo — decisão para caber no prazo e evitar estados intermediários confusos; a exceção é o controle de status no card (seção 2), que continua imediato

Step 3 (excluir): "Excluir tarefa" → confirmação: título "Excluir tarefa?", texto **"\"<título>\" e seus anexos serão excluídos permanentemente."**, botões "Cancelar" (padrão) / "Excluir" (danger) → `DELETE /tasks/{id}` → drawer fecha, card some, live region: *"Tarefa excluída"*

**Error states gerais do formulário:**
- Falha de rede no submit → toast "Não foi possível salvar. Tente novamente." — **dados digitados permanecem intactos**
- `404` ao abrir o drawer (tarefa excluída em outra aba) → drawer mostra "Tarefa não encontrada" + botão "Fechar"; ao fechar, refetch da lista

---

## 4. Upload de Anexos

Seção **"Anexos"** no fim do drawer, apenas em modo edição.

### Layout da seção

```
Anexos
+------------------------------------------+
|  ⬆ Arraste arquivos ou clique para       |
|     selecionar                           |
|  PNG, JPG, GIF, WebP, PDF, DOC, TXT —    |
|  até 10MB cada                           |
+------------------------------------------+
| [img] mockup.png            240 KB  ⬇ ✕ |
| [pdf] contrato.pdf          1.2 MB  ⬇ ✕ |
+------------------------------------------+
```

- Dropzone: borda tracejada `line`, ícone ⬆; hover/drag-over → borda `accent` + fundo levemente tingido. Clique abre o file picker (`<input type="file" multiple>` oculto e **acessível por teclado** — o dropzone é um `<button>`)
- As restrições ficam **visíveis permanentemente** no dropzone (tipos + 10MB) — o usuário não descobre o limite pelo erro
- Lista de anexos abaixo: thumbnail 40×40 para imagens (servida pelo próprio endpoint de download); ícone por tipo para PDF/DOC/TXT; nome (ellipsis no meio, preservando a extensão) + tamanho humanizado
- Ações por item: **⬇ baixar** (abre `GET /attachments/{id}/download` em nova aba) e **✕ remover**

### Fluxo de upload

Step 1: usuário solta N arquivos no dropzone (ou seleciona no picker)
  - System response: **validação client-side imediata** de cada arquivo (tipo pela extensão/MIME e tamanho) antes de qualquer request; arquivos válidos entram na fila, inválidos aparecem na lista com estado de erro (abaixo) sem bloquear os demais

Step 2: uploads em sequência (1 request `multipart` por arquivo — contrato da API)
  - User sees: cada arquivo aparece na lista imediatamente com barra de progresso fina no lugar do tamanho; os demais na fila mostram "Aguardando…"
  - System response por arquivo: `POST /tasks/{id}/attachments` → **201**: barra some, item vira anexo normal (com tamanho e ações). Live region: *"<nome> anexado"*

**Error states (por arquivo, nunca bloqueando os outros):**
- Tipo não permitido (client-side ou `400`) → item em estado de erro: nome + **"Tipo de arquivo não permitido."** + botão ✕ para dispensar
- Acima de 10MB (client-side ou `400`) → **"Arquivo acima de 10MB."** + ✕
- Falha de rede/5xx → **"Falha no envio."** + botão de texto **"Tentar de novo"** + ✕

Step 3 (remover anexo): ✕ no item → confirmação compacta inline no próprio item ("Remover? **Sim** / Não" — anexo é menos destrutivo que tarefa/projeto, não merece modal) → `DELETE /attachments/{id}` → item some; falha → item volta + toast padrão de rede

---

## 5. Accessibility Notes

- **Toggle Lista/Kanban:** `role="radiogroup"` com dois `role="radio"` (`aria-checked`) — semanticamente é escolha exclusiva, não navegação por abas; setas ←/→ alternam, e a alternância anuncia via live region *"Visualização em lista/kanban"*
- **Kanban:** colunas como `<section aria-labelledby>` (T26); a movimentação de card por mudança de status é anunciada (*"movida para Em andamento"*) — crítico porque, sem drag-and-drop, o select é a única interação e o resultado visual (card mudando de coluna) precisa de equivalente não-visual
- **Select de status no card:** `aria-label="Status de <título da tarefa>"` (só "Status" seria ambíguo entre dezenas de cards)
- **Chip input de tags:** container `role="group" aria-label="Tags"`; cada chip com botão de remoção `aria-label="Remover tag <nome>"`; instrução oculta (`aria-describedby`): "Pressione Enter para adicionar"
- **Contador da descrição curta:** `aria-live="polite"` só a partir de 260 chars (anunciar cada tecla é ruído)
- **Dropzone:** é um `<button>` com `aria-describedby` apontando para o texto de restrições; progresso de upload com `role="progressbar"` + `aria-valuenow`; estados de erro por arquivo com `role="alert"`
- **Drawer:** regras da T26 §7 (focus trap, retorno de foco ao card de origem); confirmação de descarte move o foco para "Continuar editando" (opção segura primeiro)
- **Contraste e teclado:** herdados da T26 §7 — nenhum controle novo depende de hover (as ações ⬇/✕ dos anexos ficam sempre visíveis, não apenas on-hover)

---

## 6. Open Questions

1. **Thumbnail de imagem** usa o próprio endpoint de download como `src` (`GET /attachments/{id}/download` com cookie). Funciona em dev (mesma origem via proxy/CORS com credentials); confirmar com o frontend-engineer que o `<img>` envia credenciais no setup escolhido — senão, degradar para ícone genérico de imagem. **Não bloqueia.**
2. **Filtro de tag** popula opções a partir das tarefas já carregadas — tags que só existem em tarefas filtradas fora podem não aparecer. Aceitável no escopo mínimo; endpoint de tags distintas fica como melhoria.
3. `PATCH` parcial pressupõe que o backend distingue "campo omitido" de "campo enviado como null" (limpar prazo envia `"due_date": null`). Confirmar com o python-developer que o schema usa `exclude_unset` — senão, enviar sempre o objeto completo.

## 7. Handoff to Frontend Engineer

- **T31 (toggle):** segmented control client-side; persistência `taskly:view:<projectId>`; filtros e drawer sobrevivem à troca; empty states com a copy exata da seção 2
- **T32 (status no card):** select no card (kanban) / badge-menu (lista); update otimista com rollback; `PATCH { status }`; sem toast de sucesso; live region obrigatória; stopPropagation para não abrir o drawer
- **T33 (formulário):** drawer único criar/editar; criação **vira edição após o 201** (não fechar); campo Status omitido na criação; submit explícito com botão desabilitado sem mudanças; PATCH parcial; confirmação de descarte inline; copy exata das seções 3
- **T34 (anexos):** validação client-side antes do request; uploads sequenciais com progresso por arquivo; erros por arquivo não bloqueiam a fila; restrições visíveis no dropzone (copy exata: "PNG, JPG, GIF, WebP, PDF, DOC, TXT — até 10MB cada"); confirmação de remoção inline
- **T35 (filtros):** query params `status`/`tag` no fetch; no kanban, filtro de status colapsa as outras colunas; "×" individual para limpar
- Não instalar lib de drag-and-drop (ADR-004) nem lib de upload — `fetch` + `FormData` bastam
