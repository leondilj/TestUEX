# Product Spec: Taskly

## Name
Taskly

## Objective
Taskly é um sistema web de gestão de tarefas pessoais. Permite que o usuário crie sua própria conta, organize seu trabalho em projetos e gerencie tarefas dentro de cada projeto, alternando livremente entre visualização em lista e kanban. O objetivo é dar ao usuário controle total sobre seu fluxo de trabalho pessoal, sem depender de contas de terceiros (Google/Microsoft) ou de ferramentas corporativas complexas voltadas a times.

## Users
- **Usuário final (dono da conta)**: pessoa que gerencia suas próprias tarefas e projetos. Precisa de cadastro simples (e-mail/senha), organização por projeto, edição livre de qualquer campo da tarefa após a criação, e visão flexível (lista ou kanban) do trabalho pendente.
- **Avaliador do case (UEX Startup Studio)**: [Suposição] persona secundária que não interage com o produto como usuário final, mas avalia a entrega segundo os critérios documentados (funcionalidade, arquitetura, uso de IA, documentação, vídeo, extras). Sua leitura do código, README e vídeo faz parte do "consumo" do artefato entregue.

## Core Capabilities
- Autenticação própria (cadastro, login, sessão persistente) — sem OAuth obrigatório
- Criação e organização de múltiplos projetos por usuário
- CRUD completo de tarefas dentro de um projeto: título, descrição curta, descrição completa, prazo (data e hora), tags, anexos e/ou fotos — todos os campos editáveis após a criação
- Alternância entre visualização em lista e kanban via toggle
- Gestão de status de tarefa: Não iniciada, Em andamento, Concluída, Cancelada — atualizável pelo usuário a qualquer momento

## Improvement Suggestions
1. [Sugestão] Armazenar anexos/fotos como upload de arquivo (disco local em dev, storage de objeto em produção) em vez de blob no Postgres — evita inchar o banco e simplifica servir os arquivos via URL.
2. [Sugestão] Adicionar filtro/busca por tag, status e prazo no backend, mesmo não sendo pedido explicitamente — custo baixo já com o CRUD pronto, e melhora bastante a usabilidade real de um gerenciador de tarefas.
3. [Sugestão] Versionar o registro de prompts de IA desde o primeiro commit (`spec/prompts.md` ou `docs/prompts.md`), em vez de reconstituir no fim — a entrega exige documentar os prompts usados, e isso é mais confiável feito incrementalmente do que de memória no último dia.
4. [Sugestão] Cobrir autenticação e CRUD de tarefas com testes automatizados (pytest) desde cedo — já é um diferencial priorizado pelo usuário, e protege contra regressões introduzidas por refatorações assistidas por IA em ritmo acelerado.

## Extensão além do escopo mínimo — Assistente

[Decisão do usuário, 2026-07-01] Além do escopo mínimo do case, o Taskly terá uma tela **"Assistente"** no próprio produto: um chat onde o usuário pede em linguagem natural para consultar, criar tarefas ou mudar status, como alternativa ao fluxo manual (formulários/kanban). Tratado como diferencial ("além do escopo mínimo"), não deve ser priorizado antes do escopo obrigatório, testes e documentação estarem prontos.

- O assistente roda **dentro do mesmo processo da API** (tool use da Anthropic/Claude) — não é um servidor MCP externo por enquanto. Ver `ADR-003` para a decisão e trade-offs.
- Sempre age como o **usuário autenticado da sessão de chat** — reaproveita a mesma autenticação por cookie do restante do produto (`ADR-001`), sem usuário fixo nem sistema de token separado.
- Ferramentas da primeira versão (MVP): `list_projects`, `list_tasks`, `create_task`, `update_task_status` — chamam os `services` já existentes diretamente, sem HTTP interno.
- Regras explícitas de anti-alucinação (nunca afirmar uma ação sem executá-la, nunca inventar IDs) documentadas em `spec/prompts.md`, já que o usuário levantou esse risco.
- Detalhes técnicos completos em `spec/tools.md`, `spec/prompts.md`, `spec/architecture.md` (componente Assistente) e `spec/decisions/ADR-003-assistant-in-process.md`.

## Out of Scope
- Login/cadastro via Google, Microsoft ou qualquer OAuth de terceiros (mencionado no case como não obrigatório)
- Compartilhamento de projetos/tarefas entre múltiplos usuários — o case descreve apenas o dono da conta gerenciando suas próprias tarefas, sem colaboração
- Notificações push ou por e-mail de prazos — não mencionado no escopo mínimo
- Banco de dados não-relacional (MongoDB/Redis) — decisão explícita do usuário de deixar de fora para focar no prazo de 3 dias, apesar de ser um diferencial listado nos requisitos técnicos
- Aplicativo mobile nativo — o case pede explicitamente um sistema web

## Open Questions
- Qual o limite de tamanho e tipo de arquivo aceito para anexos/fotos? Não especificado no case; será definido em `spec/architecture.md` ou `spec/data-model.md`.
- Há algum limite de projetos ou tarefas por usuário, ou é ilimitado por padrão?

## Assumptions
- [Suposição]: "conta própria" significa autenticação local com e-mail e senha, com hashing seguro (bcrypt/argon2) e sessão via JWT — o case não especifica o mecanismo exato de sessão.
- [Suposição]: "anexos e/ou fotos" são tratados como upload de arquivo genérico, sem lógica visual especial obrigatória para fotos (ex: preview não é requisito, mas pode ser um diferencial de UX).
- [Suposição]: cada projeto pertence a exatamente um usuário — o case não menciona projetos compartilhados entre contas.

---

## Decisões já confirmadas com o usuário (fora do escopo padrão deste template, registradas aqui para rastreabilidade)

- **Stack:** Backend em Python + FastAPI; Frontend em Next.js (TypeScript); banco de dados PostgreSQL rodando via Docker.
- **Sem Mongo/Redis:** descartado deliberadamente para não consumir tempo do prazo de 3 dias.
- **Deploy:** não é requisito obrigatório — o enunciado lista o link de acesso como "se possível" na entrega, e no rubric de avaliação o deploy só conta como um dos itens dos 10 pts de "além do escopo mínimo" (junto com testes extras e performance), não como categoria própria. Prioridade: **local-first** — `docker-compose` + README que rodam de primeira valem mais que um link público, já que o vídeo é o canal principal de prova de funcionamento. Deploy real (Vercel + Railway/Render) só é perseguido se sobrar tempo depois do escopo mínimo, testes e documentação estarem prontos.
- **Diferenciais priorizados:** testes automatizados (pytest) e CI/CD básico (GitHub Actions). UX/UI polish e deploy real ficam como oportunidade secundária, não prioridade.
