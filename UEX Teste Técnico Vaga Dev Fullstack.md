# Perfil de vaga e case de seleção

**UEX Startup Studio**
Documento de referência para contratação PJ — Desenvolvedor Fullstack

`Contrato PJ` · `Nível sênior` · `Startup Studio` · `2025`

---

## Perfil de função

### Desenvolvedor Fullstack
**UEX Startup Studio** — `Contrato PJ`

- 💼 PJ — Pessoa Jurídica
- 🏅 Sênior
- 👥 Time interno
- 🏢 Startup Studio

> ⚠ **Atenção:** A linguagem-alvo e o stack tecnológico são definidos projeto a projeto e especificados no aditivo de contratação correspondente. Os requisitos de base listados abaixo aplicam-se a todas as contratações desta função.

### Sobre a função

O **Desenvolvedor Fullstack** na UEX é responsável pelo desenvolvimento técnico completo dos produtos das startups do portfólio — cobrindo frontend, backend, integrações e banco de dados. Atua com base em especificações detalhadas (Spec) e incorpora ferramentas de inteligência artificial como parte central do seu fluxo de trabalho, acelerando ciclos de desenvolvimento sem abrir mão de qualidade, rastreabilidade e boas práticas de engenharia.

### Responsabilidades

- 💻 **Desenvolver funcionalidades fullstack** conforme a linguagem-alvo e o stack definidos para cada projeto
  _Frontend, backend, APIs e integrações com serviços externos_
- 📄 **Ler, interpretar e implementar** a partir de Specs técnicas fornecidas pelo time de produto
  _Garantindo aderência ao escopo e alinhamento com as decisões de UX e arquitetura_
- 🤖 **Utilizar ferramentas de IA** como parte ativa do processo de desenvolvimento
  _Geração de código, revisão automatizada, testes, documentação e refatoração assistida_
- 🗄️ **Modelar, implementar e manter** bancos de dados relacionais e não-relacionais
  _Incluindo queries, migrations, otimização de performance e integridade de dados_
- 📈 **Compreender e analisar dados** do produto para apoiar decisões técnicas e de negócio
  _Construção de relatórios, pipelines simples e leitura crítica de métricas_
- 🌿 **Manter boas práticas** de versionamento, revisão de código e documentação técnica
  _Garantindo rastreabilidade e qualidade ao longo do ciclo de desenvolvimento_
- 🔗 **Colaborar com o Product Experience** no refinamento técnico de jornadas e interfaces
  _Viabilizando tecnicamente as decisões de produto e UX dentro do prazo acordado_

### Requisitos de IA no desenvolvimento

> **Desenvolvimento assistido por IA (AI-assisted coding)**
> Cursor, GitHub Copilot, Windsurf ou equivalentes — uso fluente no dia a dia, não eventual

> **Trabalho com Spec gerada ou co-gerada por IA**
> Capacidade de consumir, questionar e implementar especificações técnicas produzidas com auxílio de LLMs

> **Prompting técnico e engenharia de contexto**
> Saber estruturar prompts para geração de código, refatoração, revisão e testes automatizados

> **Revisão crítica de código gerado por IA**
> Identificar alucinações, vulnerabilidades e desvios de boas práticas no código sugerido por modelos

> **Uso de agentes de IA para tarefas de desenvolvimento**
> Claude Code, Devin, Aider ou similares para automação de tasks, debugging e geração de testes

### Requisitos técnicos

**Obrigatórios**
- ✓ Desenvolvimento fullstack com proficiência na linguagem-alvo do projeto _(definida no aditivo de contratação)_
- ✓ Banco de dados relacional — PostgreSQL e MySQL obrigatórios; outros conforme especificado na vaga
- ✓ Leitura, análise e implementação a partir de Specs técnicas
- ✓ Uso fluente de ferramentas de IA para desenvolvimento (Cursor, Copilot, Windsurf, Claude Code, entre outros)
- ✓ Desenvolvimento e consumo de APIs REST
- ✓ Versionamento com Git e práticas de code review
- ✓ Capacidade de análise e interpretação de dados (queries analíticas, leitura de logs, métricas de produto)

**Diferenciais**
- ★ Banco de dados não-relacional (MongoDB, Redis, Firestore ou similares)
- ★ Experiência com infraestrutura em nuvem (AWS, GCP ou Azure)
- ★ Conhecimento em CI/CD e pipelines de deploy
- ★ Vivência em ambiente de startup ou produto em estágio inicial
- ★ Experiência com testes automatizados (unitários, integração, e2e)
- ★ Leitura de interfaces e compreensão básica de UX/UI

### Competências comportamentais

`Resolução de problemas` · `Atenção ao detalhe` · `Aprendizado contínuo` · `Comunicação técnica clara` · `Mentalidade AI-first` · `Autonomia e senso de prazo` · `Colaboração com produto`

---

## Case de seleção

### Taskly — sistema de gestão de tarefas
Desafio técnico aplicado à vaga de Desenvolvedor Fullstack

- 📅 Prazo de entrega: 3 dias corridos
- 👁 Critérios de avaliação visíveis

> 💡 Este case é intencionalmente aberto. O escopo mínimo está descrito abaixo, mas o que vai além dele é parte fundamental da avaliação. Criatividade, senso estético, decisões técnicas e como você comunica suas escolhas importam tanto quanto a entrega funcional. Surpreenda-nos.

### O desafio

Construa o **Taskly**, um sistema web de gestão de tarefas pessoais. O usuário deve conseguir criar uma conta própria (sem integração obrigatória com Google ou Microsoft), organizar seu trabalho em projetos e gerenciar tarefas dentro de cada projeto.

- 👤 **Autenticação própria (e-mail e senha)** — Cadastro, login e sessão persistente. Sem OAuth obrigatório.
- 📁 **Projetos** — O usuário pode criar, nomear e organizar múltiplos projetos.
- ☑️ **Tarefas por projeto** com os seguintes campos: título, descrição curta, descrição completa, prazo (data e hora), tags, anexos e/ou fotos. Todos os campos devem ser editáveis após a criação.
- 🗂️ **Visualização em lista e kanban** — O usuário pode alternar entre as duas visões por meio de um botão de toggle.
- 🔘 **Status das tarefas:** Não iniciada, Em andamento, Concluída, Cancelada — atualizável pelo usuário a qualquer momento.

### Mock de referência — mínimo esperado

> ℹ Este mock é apenas uma referência de escopo, não um wireframe a ser seguido. A identidade visual, a arquitetura de navegação e as decisões de UX são totalmente livres — e serão avaliadas.

**Taskly** — Projeto: Website redesign · `≡ Lista` (ativo) / `⊞ Kanban`

**Projetos**
- 📁 Website redesign _(ativo)_
- 📁 App mobile
- 📁 Onboarding v2
- \+ Novo projeto

**Tarefas**

| Tarefa | Descrição | Tag | Status | Prazo |
|---|---|---|---|---|
| Redesenhar tela de login | Criar nova proposta de UI para autenticação | design | Em andamento | 🕐 28/06 |
| Mapear jornada de onboarding | Documentar fluxo atual e pontos de atrito | ux | Não iniciada | 🕐 30/06 |
| Validar componentes com dev | Alinhar tokens de design com time técnico | dev | Concluída | 🕐 24/06 |

\+ Nova tarefa

### Modelo de entrega

`Desenvolvedor Fullstack`

- 🐙 Repositório público no GitHub com código-fonte completo
- 📄 README, Spec técnica e registro dos prompts utilizados no desenvolvimento
- 🔗 Link de acesso à aplicação (deploy), se possível
- 🎥 Vídeo explicando a arquitetura, decisões técnicas e demonstrando a aplicação
- 🤖 Documente como a IA foi usada — ferramentas, prompts relevantes e onde você revisou ou corrigiu o output gerado

### Critérios de avaliação

| Critério | Descrição | Pontos |
|---|---|---|
| Funcionalidade e completude técnica | O sistema funciona conforme o escopo? Sem bugs críticos? | **30 pts** |
| Qualidade do código e arquitetura | Organização, legibilidade, separação de responsabilidades | **20 pts** |
| Uso de IA no desenvolvimento | Qualidade dos prompts, rastreabilidade, revisão crítica do output gerado | **20 pts** |
| Documentação (README, Spec, prompts) | Clareza, rastreabilidade das decisões técnicas | **15 pts** |
| Apresentação em vídeo e comunicação técnica | Capacidade de explicar arquitetura e decisões com clareza | **5 pts** |
| O que foi além do escopo mínimo | Features extras, testes, performance, deploy | **10 pts** |
| **Total** | | **100 pts** |

---

Dúvidas sobre o case? Entre em contato antes de iniciar. Após o envio, pode ser agendada uma sessão de apresentação para aprofundar as decisões tomadas.

UEX Startup Studio · 2025
