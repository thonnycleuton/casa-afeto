# M12 — Plano de Validação

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — implementação pendente
**Marco:** M12 — Autenticação & Área de Usuários

---

## 1. Pré-requisitos

1. M11 concluído — sistema deployado em produção.
2. Servidor SMTP configurado (ou mock para testes locais).
3. Banco de dados com migrations aplicadas.
4. Endpoint de setup disponível (nenhum usuário criado).

---

## 2. Cenários de Validação

### Cenário 1: Setup inicial — criar primeiro admin

**Status:** Pendente

**Objetivo:** Verificar que o primeiro admin pode ser criado via endpoint de setup.

**Passos:**

1. Acessar o sistema deployado (sem usuários).
2. Chamar `POST /api/v1/setup/create-admin` com nome, email e senha.
3. Verificar que o usuário admin foi criado no banco de dados.
4. Chamar o endpoint novamente e verificar que retorna 403.

**Critérios verificados:** AC-M12-008

---

### Cenário 2: Login com credenciais válidas

**Status:** Pendente

**Objetivo:** Verificar que o login retorna tokens JWT corretamente.

**Passos:**

1. Acessar a página de login no navegador.
2. Preencher email e senha do admin criado no Cenário 1.
3. Submeter o formulário.
4. Verificar que o usuário é redirecionado para a página principal.
5. Verificar que o nome do usuário aparece na barra de navegação.

**Critérios verificados:** AC-M12-002, AC-M12-013, AC-M12-014, AC-M12-018

---

### Cenário 3: Login com credenciais inválidas

**Status:** Pendente

**Objetivo:** Verificar que credenciais erradas são rejeitadas.

**Passos:**

1. Acessar a página de login.
2. Preencher email válido com senha errada.
3. Submeter o formulário.
4. Verificar que mensagem de erro é exibida.
5. Tentar com email inexistente.
6. Verificar que a mensagem de erro é genérica (não revela se o email existe).

**Critérios verificados:** AC-M12-003, AC-M12-015

---

### Cenário 4: Proteção de rotas

**Status:** Pendente

**Objetivo:** Verificar que rotas protegidas exigem autenticação.

**Passos:**

1. Fazer logout (ou abrir navegador em modo anônimo).
2. Tentar acessar `http://<IP>/products` diretamente.
3. Verificar que o navegador redireciona para `/login`.
4. Fazer login e verificar que o usuário é redirecionado para `/products`.

**Critérios verificados:** AC-M12-006, AC-M12-016

---

### Cenário 5: Gerenciamento de usuários (admin)

**Status:** Pendente

**Objetivo:** Verificar que o admin pode criar e gerenciar usuários.

**Passos:**

1. Estar logado como admin.
2. Acessar o painel de gerenciamento de usuários.
3. Criar um novo usuário com role `operator`.
4. Verificar que o usuário aparece na lista.
5. Editar o usuário (mudar nome, por exemplo).
6. Desativar o usuário e verificar que o status muda.

**Critérios verificados:** AC-M12-007, AC-M12-021

---

### Cenário 6: Operador não acessa gerenciamento

**Status:** Pendente

**Objetivo:** Verificar que o operador não pode gerenciar usuários.

**Passos:**

1. Fazer login como operador (criado no Cenário 5).
2. Verificar que o menu de gerenciamento de usuários não aparece.
3. Tentar acessar `POST /api/v1/users` via curl e verificar 403.

**Critérios verificados:** AC-M12-007, AC-M12-021

---

### Cenário 7: Recuperação de senha

**Status:** Pendente

**Objetivo:** Verificar que o fluxo de recuperação de senha funciona.

**Passos:**

1. Estar logado como operador.
2. Clicar em "Esqueci minha senha" no login.
3. Inserir o email do operador.
4. Verificar que o email de recuperação é recebido.
5. Clicar no link do email.
6. Preencher nova senha e confirmar.
7. Fazer login com a nova senha.
8. Verificar que os tokens antigos foram invalidados.

**Critérios verificados:** AC-M12-009, AC-M12-010, AC-M12-019, AC-M12-020

---

### Cenário 8: Logout

**Status:** Pendente

**Objetivo:** Verificar que o logout revoga os tokens.

**Passos:**

1. Estar logado.
2. Clicar em "Sair" na barra de navegação.
3. Verificar que o usuário é redirecionado para o login.
4. Tentar usar o refresh token antigo via curl e verificar 401.

**Critérios verificados:** AC-M12-005, AC-M12-018

---

### Cenário 9: Auto-refresh do token

**Status:** Pendente

**Objetivo:** Verificar que o token é renovado automaticamente.

**Passos:**

1. Estar logado.
2. Aguardar o access token expirar (ou simular com token de curta validade).
3. Navegar entre as páginas do sistema.
4. Verificar que a sessão não é interrompida.
5. Verificar que as requisições API continuam funcionando.

**Critérios verificados:** AC-M12-017

---

### Cenário 10: Perfil do usuário

**Status:** Pendente

**Objetivo:** Verificar que o perfil do usuário é retornado corretamente.

**Passos:**

1. Estar logado.
2. Chamar `GET /api/v1/auth/me` via curl com token.
3. Verificar que retorna nome, email e role.
4. Verificar que a senha não é retornada.

**Critérios verificados:** AC-M12-011

---

## 3. Matriz de Validação

| AC ID | Cenário | Status | Observações |
|-------|---------|--------|-------------|
| AC-M12-001 | Cenário 5 | Pendente | Hash bcrypt verificado via DB |
| AC-M12-002 | Cenário 2 | Pendente | |
| AC-M12-003 | Cenário 3 | Pendente | |
| AC-M12-004 | Cenário 9 | Pendente | |
| AC-M12-005 | Cenário 8 | Pendente | |
| AC-M12-006 | Cenário 4 | Pendente | |
| AC-M12-007 | Cenário 5 + 6 | Pendente | |
| AC-M12-008 | Cenário 1 | Pendente | |
| AC-M12-009 | Cenário 7 | Pendente | |
| AC-M12-010 | Cenário 7 | Pendente | |
| AC-M12-011 | Cenário 10 | Pendente | |
| AC-M12-012 | Cenário 7 | Pendente | SMTP config |
| AC-M12-013 | Cenário 2 | Pendente | |
| AC-M12-014 | Cenário 2 | Pendente | |
| AC-M12-015 | Cenário 3 | Pendente | |
| AC-M12-016 | Cenário 4 | Pendente | |
| AC-M12-017 | Cenário 9 | Pendente | |
| AC-M12-018 | Cenário 2 + 8 | Pendente | |
| AC-M12-019 | Cenário 7 | Pendente | |
| AC-M12-020 | Cenário 7 | Pendente | |
| AC-M12-021 | Cenário 5 + 6 | Pendente | |
| AC-M12-022 | Build | Pendente | `vue-tsc --noEmit` |

---

## 4. Definição de Pronto

M12 está completo quando:

1. Todos os endpoints de autenticação estão implementados e testados.
2. O endpoint de setup cria o primeiro admin com sucesso.
3. As rotas estão protegidas e exigem autenticação.
4. O frontend exibe login, proteção de rotas, e perfil do usuário.
5. O admin pode gerenciar usuários (criar, editar, desativar).
6. O operador não acessa funções de admin.
7. A recuperação de senha por email funciona.
8. Os tokens JWT são renovados automaticamente.
9. O logout revoga os tokens corretamente.
10. Os testes automatizados passam.
11. O Product Owner valida o fluxo completo de autenticação.
