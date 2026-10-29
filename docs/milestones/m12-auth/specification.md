# M12 — Autenticação & Área de Usuários

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — implementação pendente
**Marco:** M12 — Autenticação & Área de Usuários
**Fase:** 3 — Infraestrutura & Acesso

---

## 1. Objetivo

Introduzir controle de acesso ao sistema Casa Afeto para que apenas usuários autorizados possam acessar e operar o sistema. O marco implementa autenticação por email/senha, autorização baseada em roles (Admin e Operador), recuperação de senha por email, e proteção de todas as rotas da aplicação.

---

## 2. Escopo

### 2.1 Backend

**Modelo de usuário:**

- Nova entidade `User` com campos: id, email, password_hash, full_name, role, is_active, is_setup_complete, created_at, updated_at.
- Roles: `admin` (acesso total) e `operator` (acesso limitado a operações do dia a dia).
- Senhas armazenadas como hash bcrypt — nunca em texto plano.

**Autenticação JWT:**

- Token de acesso (access token) com validade curta (15 minutos).
- Token de atualização (refresh token) com validade longa (7 dias).
- Refresh token armazenado no banco de dados para revogação.
- Middleware de autenticação protegendo rotas `/api/v1/*`.

**Endpoints de autenticação:**

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/login` | Autenticar usuário e retornar tokens |
| POST | `/api/v1/auth/refresh` | Renovar access token usando refresh token |
| POST | `/api/v1/auth/logout` | Revogar refresh token |
| POST | `/api/v1/auth/forgot-password` | Solicitar recuperação de senha por email |
| POST | `/api/v1/auth/reset-password` | Redefinir senha com token de recuperação |
| GET | `/api/v1/auth/me` | Retornar perfil do usuário autenticado |

**Gerenciamento de usuários (apenas admin):**

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/users` | Criar novo usuário |
| GET | `/api/v1/users` | Listar todos os usuários |
| GET | `/api/v1/users/{id}` | Detalhe de um usuário |
| PUT | `/api/v1/users/{id}` | Atualizar usuário |
| DELETE | `/api/v1/users/{id}` | Desativar usuário (soft delete) |

**Endpoint de setup inicial:**

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/setup/create-admin` | Criar primeiro admin e desativar endpoint |

- O endpoint verifica se `is_setup_complete` é falso no banco de dados.
- Após criar o primeiro admin, o endpoint é desativado automaticamente.
- Retorna 403 se o setup já foi concluído.

**Envio de email:**

- Configuração SMTP via variáveis de ambiente.
- SendGrid como provedor de email (plano grátis: 100 emails/dia).
- Template de recuperação de senha com link expiratório (1 hora).
- Biblioteca `aiosmtplib` para envio assíncrono.

**Política de senha:**

- Mínimo 8 caracteres.
- Pelo menos 1 letra maiúscula.
- Pelo menos 1 número.

**Dependências novas:**

- `python-jose[cryptography]` — geração e validação de JWT.
- `passlib[bcrypt]` — hash de senhas.
- `aiosmtplib` — envio de email assíncrono.

---

### 2.2 Frontend

**Página de login:**

- Formulário com email e senha.
- Link "Esqueci minha senha" que abre modal de recuperação.
- Mensagem de erro clara em caso de credenciais inválidas.
- Após login, redirecionar para a página principal.

**Modal de recuperação de senha:**

- Campo de email para solicitar link de recuperação.
- Confirmação visual de email enviado.

**Página de reset de senha:**

- Acessada via link do email.
- Formulário com nova senha e confirmação.
- Após sucesso, redirecionar para login.

**Proteção de rotas:**

- Router guard que verifica token de acesso antes de carregar qualquer página protegida.
- Se token ausente ou expirado, redirecionar para `/login`.
- Auto-refresh do token quando próximo da expiração.

**Barra de navegação atualizada:**

- Exibir nome do usuário logado.
- Botão "Sair" (logout) que revoga tokens e redireciona para login.
- Seção de perfil mostrando nome, email e role.

**Painel de gerenciamento de usuários (apenas admin):**

- Lista de usuários com nome, email, role e status.
- Modal para criar novo usuário (nome, email, senha, role).
- Modal para editar usuário (nome, role, status).
- Botão para desativar usuário com confirmação.

**Tipos TypeScript:**

- `User`, `UserRole`, `LoginRequest`, `LoginResponse`, `AuthTokens`.

---

## 3. Fora do Escopo

- **Auto-cadastro** — Apenas o admin cadastra novos usuários.
- **Autenticação multifator (MFA)** — Pode ser adicionado em milestone futuro.
- **Login social** (Google, Facebook) — Fora de escopo.
- **Permissões granulares** — Apenas duas roles (admin/operador) neste marco.
- **Audit log de login** — Pode ser adicionado em milestone futuro.
- **Limitação de tentativas de login** — Pode ser adicionado em milestone futuro.

---

## 4. Dependências

- **M11 concluído** — O sistema precisa estar deployado em produção para testar a autenticação.
- **Servidor SMTP** — É necessário um servidor de email configurado para recuperação de senha. O Product Owner precisa fornecer as credenciais SMTP ou configurar um serviço (ex: SendGrid, Mailgun, ou SMTP do provedor de email).

---

## 5. Decisões Confirmadas

1. **Servidor SMTP** — SendGrid (plano grátis, 100 emails/dia).
2. **Política de senha** — Mínimo 8 caracteres, 1 maiúscula, 1 número.
3. **Operador vs Admin** — Operador não acessa: gerenciamento de usuários, exclusão de vendas, exclusão de produtos.

---

## 6. Riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Servidor SMTP não configurado | Recuperação de senha não funciona | Permitir fallback: admin redefine senha manualmente |
| Tokens JWT vazados | Acesso não autorizado | Validade curta (15 min) + refresh token revogável |
| Primeiro admin bloqueado | Sem acesso ao sistema | Endpoint de setup com token secreto como fallback |

---

## 7. Sequência de Implementação

```text
1. Backend: modelo User + migration Alembic
        ↓
2. Backend: utilitários de JWT e hash de senha
        ↓
3. Backend: endpoints de autenticação (login, refresh, logout)
        ↓
4. Backend: middleware de proteção de rotas
        ↓
5. Backend: endpoint de setup (create-admin)
        ↓
6. Backend: endpoints de gerenciamento de usuários (CRUD admin)
        ↓
7. Backend: recuperação de senha (forgot + reset + email)
        ↓
8. Frontend: tipos TypeScript e interceptador de API
        ↓
9. Frontend: página de login
        ↓
10. Frontend: proteção de rotas (router guard)
        ↓
11. Frontend: barra de navegação com perfil e logout
        ↓
12. Frontend: modal de recuperação de senha
        ↓
13. Frontend: painel de gerenciamento de usuários (admin)
        ↓
14. Testes: autenticação, autorização, recuperação de senha
        ↓
15. Validação: deploy em produção e teste manual
```
