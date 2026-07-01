# ADR-001: Estratégia de autenticação (JWT em cookie httpOnly)

**Date:** 2026-07-01
**Status:** Accepted
**Deciders:** Usuário (dono do projeto) + python-architect

---

## Context

O case exige "autenticação própria (e-mail e senha)... cadastro, login e sessão persistente. Sem OAuth obrigatório." O frontend (Next.js) e o backend (FastAPI) são aplicações separadas, então a sessão precisa atravessar essa fronteira via HTTP. Prazo de 3 dias limita quanto tempo pode ser gasto em infraestrutura de auth.

---

## Decision

Vamos usar **JWT assinado, armazenado em cookie `httpOnly` e `Secure`**, sem refresh token. O cookie é definido pela API no login e enviado automaticamente pelo browser em toda requisição subsequente (`credentials: "include"` no fetch do Next.js).

---

## Options Considered

### Option 1: JWT em cookie httpOnly (escolhida)

Token assinado com expiração longa (ex: 7 dias), guardado em cookie que o JavaScript do frontend não consegue ler.

**Pros:**
- Imune a roubo de token via XSS (JS não acessa cookie httpOnly)
- Sessão persistente "de graça" — o browser reenvia o cookie automaticamente
- Simples de implementar em FastAPI (`Response.set_cookie`) e Next.js (`fetch` com `credentials: "include"`)

**Cons:**
- Exige configurar CORS com `allow_credentials=True` e origem explícita (não pode usar `*`)
- Sem refresh token, a sessão expira de vez após o prazo definido — usuário precisa logar de novo

### Option 2: JWT em localStorage, enviado via header Authorization

**Pros:**
- Mais simples de testar via `curl`/Postman sem lidar com cookies
- Não exige configuração de CORS com credentials

**Cons:**
- Vulnerável a roubo via XSS (qualquer script no frontend lê `localStorage`)
- Frontend precisa gerenciar manualmente o anexo do header em toda chamada

### Option 3: Sessão server-side (cookie de sessão + tabela de sessões no Postgres)

**Pros:**
- Permite invalidar sessões individualmente a qualquer momento (logout remoto, revogação)

**Cons:**
- Mais uma tabela e mais lógica para um case de 3 dias sem esse requisito explícito
- Sem ganho perceptível de segurança para o escopo deste case

---

## Rationale

Para um app onde "sessão persistente" é requisito e o time é de uma pessoa em 3 dias, a Option 1 dá o melhor equilíbrio entre segurança (não expõe token a XSS) e simplicidade de implementação. Refresh token e revogação de sessão (Option 3) resolvem problemas que este case não tem.

---

## Consequences

**Positive:**
- Sessão persistente funciona sem lógica extra no frontend
- Superfície de ataque menor (sem token acessível via JS)

**Negative / Trade-offs:**
- Sessão expira totalmente após o prazo do JWT — sem renovação silenciosa
- CORS precisa ser configurado corretamente (`allow_credentials=True`, origem explícita da Vercel/localhost) — erro comum de configurar errado

**Risks:**
- Se o deploy real for perseguido (frontend e backend em domínios diferentes), o cookie precisa de `SameSite=None; Secure` — documentar isso no README para não travar o time perto da entrega.

---

## Implementation Notes

- Senha mínima: 8 caracteres — validado no schema Pydantic de `auth_schema.py` (`400` se abaixo disso, ver `spec/api.md`)
- Hashing de senha: `passlib[bcrypt]`
- Geração/validação do JWT: `python-jose` ou `pyjwt`, chave secreta via variável de ambiente (`JWT_SECRET`)
- Cookie: `httponly=True`, `secure=True` em produção, `samesite="lax"` em dev / `"none"` se domínios diferentes em produção
- Dependency `get_current_user` em `app/api/deps.py` decodifica o cookie e carrega o `User`; lança `401` se ausente/inválido/expirado
