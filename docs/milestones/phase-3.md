# Casa Afeto — Fase 3

**Versão do documento:** 0.2
**Status:** Em andamento — M11 em implementação
**Fase:** 3 — Infraestrutura & Acesso

---

## 1. Finalidade

A Fase 3 prepara o sistema para ser usado em produção por pessoas fora do ambiente de desenvolvimento.

O objetivo é permitir que a Casa Afeto:

* coloque o sistema em um ambiente de produção acessível;
* proteja o acesso com autenticação e controle de roles;
* permita que usuários autenticados acessem o sistema de forma segura.

A Fase 3 segue o mesmo princípio das fases anteriores:

> Construa pouco, valide, aprenda e depois construa a próxima coisa.

Cada marco deve ser implementado, testado e validado manualmente antes que o próximo marco comece.

---

## 2. Sequência de Desenvolvimento da Fase 3

A Fase 3 é dividida em dois marcos. A sequência proposta é:

```text
M11 — Deploy & Ambiente de Produção (pendente)
        ↓
M12 — Autenticação & Área de Usuários (pendente)
```

A ordem é intencional:

* **M11 (Deploy)** é a base — sem ambiente de produção, a autenticação não é útil para usuários externos.
* **M12 (Autenticação)** depende de M11 — o sistema precisa estar acessível antes de proteger o acesso.

---

## 3. Estado Atual dos Marcos

| Marco | Status | Documentos |
|-------|--------|------------|
| M11 — Deploy & Ambiente de Produção | Implementação em andamento | specification.md, acceptance-criteria.md, validation.md |
| M12 — Autenticação & Área de Usuários | Pendente | A ser criado |

---

## 4. Marco M11 — Deploy & Ambiente de Produção

### Objetivo

Tornar o sistema acessível em um ambiente de produção, permitindo que pessoas fora do ambiente de desenvolvimento acessem o sistema.

### Capacidades Planejadas

* configuração de ambiente de produção (Nginx, Docker Compose, CI/CD básico);
* domínio e SSL;
* variáveis de ambiente seguras;
* backup de banco de dados;
* monitoramento básico.

### Documentos

```text
docs/milestones/m11-deploy/
├── specification.md          — Especificação detalhada (v0.1, em revisão)
├── acceptance-criteria.md    — 13 critérios de aceitação (v0.1, em revisão)
└── validation.md             — Plano de validação (v0.1, em revisão)
```

### Dependências

* Fase 1 concluída (M1-M5)
* Fase 2 concluída (M6-M10)

### Status

- Especificação: Aprovado v0.2
- Implementação: Em andamento — arquivos de infraestrutura criados

---

## 5. Marco M12 — Autenticação & Área de Usuários

### Objetivo

Habilitar o acesso controlado ao sistema através de autenticação de usuários com roles e proteção de rotas.

### Capacidades Planejadas

* cadastro de usuários com login/senha;
* recuperação de senha por email;
* roles: admin e operador;
* proteção de rotas no frontend e backend;
* página de login e área de perfil.

### Documentos

A ser criado quando o marco for detalhado:

```text
docs/milestones/m12-auth/
├── specification.md          — Especificação detalhada
├── acceptance-criteria.md    — Critérios de aceitação
├── use-cases.md              — Casos de uso
└── validation.md             — Plano de validação
```

### Dependências

* M11 — Deploy & Ambiente de Produção

### Status

- Especificação: Pendente
- Implementação: Pendente

---

## 6. Notas

Esta fase não introduz novas funcionalidades de negócio operacionais — foca em infraestrutura e acesso.

O detalhamento de cada marco (especificação, critérios de aceitação, casos de uso e validação) será feito quando o marco entrar em desenvolvimento ativo.
