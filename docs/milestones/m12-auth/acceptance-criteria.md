# M12 — Critérios de Aceitação

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — implementação pendente
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
| AC-M12-001 | test_user_password_hashed | tests/test_auth.py | — | ✗ |
| AC-M12-002 | test_login_returns_tokens | tests/test_auth.py | — | ✗ |
| AC-M12-003 | test_login_invalid_credentials | tests/test_auth.py | — | ✗ |
| AC-M12-004 | test_refresh_token_renews | tests/test_auth.py | — | ✗ |
| AC-M12-005 | test_logout_revokes_token | tests/test_auth.py | — | ✗ |
| AC-M12-006 | test_protected_route_without_token | tests/test_auth.py | — | ✗ |
| AC-M12-007 | test_admin_manage_users | tests/test_users.py | — | ✗ |
| AC-M12-008 | test_setup_create_first_admin | tests/test_setup.py | — | ✗ |
| AC-M12-009 | test_forgot_password_sends_email | tests/test_auth.py | — | ✗ |
| AC-M12-010 | test_reset_password_with_token | tests/test_auth.py | — | ✗ |
| AC-M12-011 | test_get_current_user | tests/test_auth.py | — | ✗ |
| AC-M12-012 | test_smtp_config_from_env | tests/test_config.py | — | ✗ |
| AC-M12-013 | Login page renders | tests/AuthViews.spec.ts | — | ✗ |
| AC-M12-014 | Successful login redirects | tests/AuthViews.spec.ts | — | ✗ |
| AC-M12-015 | Failed login shows error | tests/AuthViews.spec.ts | — | ✗ |
| AC-M12-016 | Route guard redirects | tests/RouterGuard.spec.ts | — | ✗ |
| AC-M12-017 | Token auto-refresh | tests/AuthInterceptor.spec.ts | — | ✗ |
| AC-M12-018 | Navbar shows user profile | tests/Navbar.spec.ts | — | ✗ |
| AC-M12-019 | Forgot password modal | tests/AuthViews.spec.ts | — | ✗ |
| AC-M12-020 | Reset password page | tests/AuthViews.spec.ts | — | ✗ |
| AC-M12-021 | Admin user management | tests/UsersView.spec.ts | — | ✗ |
| AC-M12-022 | TypeScript types compile | vue-tsc | — | ✗ |

**Nota:** M12 introduz testes de autenticação e autorização. Os testes de backend usam pytest com fixtures de usuário e token. Os testes de frontend usam Vue Test Utils com mocks de API.
