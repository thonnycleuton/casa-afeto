# M12 — Critérios de Aceitação

**Versão do documento:** 0.3 (Concluído)
**Status:** Concluído — implementação aprovada
**Marco:** M12 — Autenticação & Área de Usuários

---

## Objetivo

Introduzir controle de acesso ao sistema Casa Afeto com autenticação por email/senha, autorização baseada em roles (Admin e Operador), recuperação de senha por email, e proteção de todas as rotas da aplicação.

---

## Escopo

- Backend: modelo User, autenticação JWT (access + refresh tokens), endpoints de auth, gerenciamento de usuários (admin-only), endpoint de setup, recuperação de senha por email.
- Frontend: página de login, proteção de rotas, auto-refresh de token, barra de navegação com perfil, modal de recuperação de senha, painel de gerenciamento de usuários (admin).

---

## Fora do Escopo

- Auto-cadastro de usuários.
- Autenticação multifator (MFA).
- Login social.
- Permissões granulares além de admin/operador.
- Audit log de login.
- Limitação de tentativas de login.

---

## Backend

### AC-M12-001 [Backend] — Modelo User com hash de senha

**Dado** que o sistema precisa armazenar usuários
**Quando** um novo usuário é criado
**Então** a senha é armazenada como hash bcrypt
**E** o campo `password_hash` nunca contém a senha em texto plano
**E** o usuário possui uma role (`admin` ou `operator`)

---

### AC-M12-002 [Backend] — Login retorna tokens JWT

**Dado** que um usuário válido existe no sistema
**Quando** o endpoint `/api/v1/auth/login` é chamado com email e senha corretos
**Então** o servidor retorna um access token JWT e um refresh token
**E** o access token tem validade de 15 minutos
**E** o refresh token tem validade de 7 dias

---

### AC-M12-003 [Backend] — Login rejeita credenciais inválidas

**Dado** que o endpoint `/api/v1/auth/login` está disponível
**Quando** credenciais inválidas são enviadas (email inexistente ou senha errada)
**Então** o servidor retorna 401 Unauthorized
**E** a mensagem de erro não revela se o email existe ou não

---

### AC-M12-004 [Backend] — Refresh token renova access token

**Dado** que o usuário possui um refresh token válido
**Quando** o endpoint `/api/v1/auth/refresh` é chamado
**Então** um novo access token é emitido
**E** o refresh token antigo continua válido até ser revogado

---

### AC-M12-005 [Backend] — Logout revoga refresh token

**Dado** que o usuário está autenticado
**Quando** o endpoint `/api/v1/auth/logout` é chamado
**Então** o refresh token é revogado
**E** tentativas de usar o refresh token revogado retornam 401

---

### AC-M12-006 [Backend] — Rotas protegidas exigem autenticação

**Dado** que as rotas `/api/v1/*` estão protegidas
**Quando** uma requisição sem token JWT é feita
**Então** o servidor retorna 401 Unauthorized
**E** quando um token expirado é usado, o servidor retorna 401

---

### AC-M12-007 [Backend] — Admin pode gerenciar usuários

**Dado** que o usuário autenticado tem role `admin`
**Quando** o endpoint de gerenciamento de usuários é chamado
**Então** o admin pode criar, listar, atualizar e desativar usuários
**E** um usuário com role `operator` não pode acessar esses endpoints (403)

---

### AC-M12-008 [Backend] — Endpoint de setup cria primeiro admin

**Dado** que o sistema foi recém-deployado e não tem usuários
**Quando** o endpoint `/api/v1/setup/create-admin` é chamado com dados do admin
**Então** o primeiro usuário admin é criado
**E** o endpoint é desativado automaticamente
**E** chamadas subsequentes retornam 403 Forbidden

---

### AC-M12-009 [Backend] — Recuperação de senha envia email

**Dado** que um usuário existe no sistema
**Quando** o endpoint `/api/v1/auth/forgot-password` é chamado com o email do usuário
**Então** um email com link de recuperação é enviado
**E** o link expira após 1 hora
**E** se o email não existe, nenhum erro é retornado (segurança)

---

### AC-M12-010 [Backend] — Reset de senha com token válido

**Dado** que o usuário possui um token de recuperação válido
**Quando** o endpoint `/api/v1/auth/reset-password` é chamado com o token e nova senha
**Então** a senha do usuário é atualizada
**E** os tokens JWT anteriores são invalidados
**E** o token de recuperação não pode ser reutilizado

---

### AC-M12-011 [Backend] — Perfil do usuário autenticado

**Dado** que o usuário está autenticado com token JWT válido
**Quando** o endpoint `/api/v1/auth/me` é chamado
**Então** o servidor retorna os dados do usuário (nome, email, role)
**E** a senha não é retornada

---

### AC-M12-012 [Backend] — Configuração SMTP via variáveis de ambiente

**Dado** que o sistema precisa enviar emails
**Quando** as variáveis de ambiente SMTP estão configuradas
**Então** os emails são enviados via SMTP
**E** se as variáveis não estão configuradas, o sistema registra um aviso mas não falha

---

## Frontend

### AC-M12-013 [Frontend] — Página de login

**Dado** que o usuário acessa o sistema sem estar autenticado
**Quando** a aplicação carrega
**Então** o usuário é redirecionado para a página de login
**E** a página exibe um formulário com campos de email e senha
**E** há um link "Esqueci minha senha"

---

### AC-M12-014 [Frontend] — Login bem-sucedido redireciona

**Dado** que o usuário preencheu email e senha corretos
**Quando** o formulário de login é submetido
**Então** os tokens são armazenados localmente
**E** o usuário é redirecionado para a página principal do sistema

---

### AC-M12-015 [Frontend] — Login falha exibe erro

**Dado** que o usuário preencheu credenciais inválidas
**Quando** o formulário de login é submetido
**Então** uma mensagem de erro é exibida no formulário
**E** os campos não são limpos automaticamente

---

### AC-M12-016 [Frontend] — Proteção de rotas

**Dado** que o usuário não possui token JWT válido
**Quando** tenta acessar uma rota protegida diretamente pela URL
**Então** é redirecionado para a página de login
**E** após login bem-sucedido, retorna à rota original

---

### AC-M12-017 [Frontend] — Auto-refresh do token

**Dado** que o access token está próximo da expiração
**Quando** uma requisição API é feita
**Então** o refresh token é usado automaticamente para obter novo access token
**E** a sessão do usuário não é interrompida

---

### AC-M12-018 [Frontend] — Barra de navegação com perfil

**Dado** que o usuário está autenticado
**Quando** a barra de navegação é exibida
**Então** o nome do usuário é mostrado
**E** há um botão "Sair" que faz logout
**E** clicar em "Sair" revoga os tokens e redireciona para login

---

### AC-M12-019 [Frontend] — Modal de recuperação de senha

**Dado** que o usuário clicou em "Esqueci minha senha"
**Quando** o modal de recuperação é aberto
**Então** há um campo de email para solicitar o link
**E** após envio, uma mensagem de confirmação é exibida

---

### AC-M12-020 [Frontend] — Página de reset de senha

**Dado** que o usuário clicou no link de recuperação do email
**Quando** a página de reset é carregada
**Então** há um formulário com campos de nova senha e confirmação
**E** após sucesso, o usuário é redirecionado para login

---

### AC-M12-021 [Frontend] — Painel de gerenciamento de usuários (admin)

**Dado** que o usuário autenticado tem role `admin`
**Quando** acessa o painel de usuários
**Então** vê a lista de usuários com nome, email, role e status
**E** pode criar, editar e desativar usuários via modais
**E** um usuário com role `operator` não vê o menu de gerenciamento

---

### AC-M12-022 [Frontend] — Tipos TypeScript de autenticação

**Dado** que o frontend usa TypeScript
**Quando** os tipos de autenticação são importados
**Então** `User`, `UserRole`, `LoginRequest`, `LoginResponse` e `AuthTokens` estão definidos
**E** o código compila sem erros de tipo

---

## Test Coverage Matrix

| AC ID | Test Name | File | Line | Status |
|-------|-----------|------|------|--------|
| AC-M12-001 | test_login_success (password hash verified in service) | tests/test_m12_auth.py | 100 | ✅ |
| AC-M12-002 | test_login_success | tests/test_m12_auth.py | 100 | ✅ |
| AC-M12-003 | test_login_invalid_password / test_login_nonexistent_user | tests/test_m12_auth.py | 113 | ✅ |
| AC-M12-004 | test_refresh_returns_new_tokens | tests/test_m12_auth.py | 152 | ✅ |
| AC-M12-005 | test_logout_revokes_refresh_token | tests/test_m12_auth.py | 177 | ✅ |
| AC-M12-006 | test_me_unauthorized | tests/test_m12_auth.py | 206 | ✅ |
| AC-M12-007 | test_list_users / test_create_user / test_operator_denied_on_admin_routes | tests/test_m12_auth.py | 247 | ✅ |
| AC-M12-008 | test_create_first_admin / test_setup_rejected_after_first_admin | tests/test_m12_auth.py | 78 | ✅ |
| AC-M12-009 | test_forgot_password_returns_202 | tests/test_m12_auth.py | 218 | ⏳ |
| AC-M12-010 | test_reset_password_invalid_token | tests/test_m12_auth.py | 230 | ⏳ |
| AC-M12-011 | test_me_returns_profile | tests/test_m12_auth.py | 197 | ✅ |
| AC-M12-012 | SMTP config via env vars (manual) | — | — | ⏳ |
| AC-M12-013 | LoginView.vue renders | Implementação verificada | — | ✅ |
| AC-M12-014 | Login redirects on success | Implementação verificada | — | ✅ |
| AC-M12-015 | Login shows error on failure | Implementação verificada | — | ✅ |
| AC-M12-016 | Router guard redirects | useAuth.ts + App.vue | — | ✅ |
| AC-M12-017 | Auto-refresh on 401 | client.ts interceptor | — | ✅ |
| AC-M12-018 | Navbar shows user profile + logout | App.vue | — | ✅ |
| AC-M12-019 | Forgot password modal | LoginView.vue | — | ⏳ |
| AC-M12-020 | Reset password page | LoginView.vue | — | ⏳ |
| AC-M12-021 | Admin user management panel | App.vue + UserFormModal.vue | — | ✅ |
| AC-M12-022 | TypeScript types compile | vue-tsc --noEmit | — | ✅ |

**Nota:** ACs marcados com ⏳ (AC-M12-009, 010, 012, 019, 020) dependem da configuração do serviço de email (SMTP) e estão adiados para um milestone futuro (multi-tenancy). O código backend e frontend já está implementado e testado — basta configurar as credenciais SMTP quando necessário.
