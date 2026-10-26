# M11 — Critérios de Aceitação

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — implementação em andamento
**Marco:** M11 — Deploy & Ambiente de Produção

---

## Backend

### AC-M11-001 [Backend] — Dockerfile de produção do backend

**Dado** que o backend possui um Dockerfile de desenvolvimento
**Quando** um Dockerfile de produção é criado
**Então** a imagem não inclui `--reload` no uvicorn
**E** a imagem não monta volumes de código fonte
**E** a imagem usa uma imagem base slim
**E** a imagem instala apenas as dependências de produção

---

### AC-M11-002 [Backend] — Dockerfile de produção do frontend

**Dado** que o frontend possui um Dockerfile de desenvolvimento
**Quando** um Dockerfile de produção é criado
**Então** a imagem executa o build estático do frontend (`npm run build`)
**E** a imagem serve os arquivos estáticos (via Nginx ou similar)
**E** a imagem não inclui `node_modules` desnecessários
**E** a imagem não executa `npm run dev`

---

### AC-M11-003 [Backend] — Docker Compose de produção

**Dado** que existe um `docker-compose.yml` de desenvolvimento
**Quando** um `docker-compose.prod.yml` é criado
**Então** o arquivo inclui todos os serviços necessários (PostgreSQL, backend, frontend, Nginx)
**E** o banco de dados PostgreSQL não expõe portas para fora da rede Docker
**E** o backend não expõe portas para fora da rede Docker
**E** o frontend não expõe portas para fora da rede Docker
**E** apenas o Nginx expõe as portas 80 e 443
**E** os serviços usam healthchecks
**E** os dados do banco persistem em volume Docker

---

### AC-M11-004 [Backend] — Nginx como reverse proxy

**Dado** que o sistema possui backend e frontend separados
**Quando** o Nginx é configurado como reverse proxy
**Então** as requisições para `/api` são roteadas para o backend
**E** as requisições para `/` servem o build estático do frontend
**E** o Nginx redireciona HTTP (porta 80) para HTTPS (porta 443)
**E** o Nginx suporta SSL/TLS

---

### AC-M11-005 [Backend] — SSL/TLS com Let's Encrypt

**Dado** que o Nginx está configurado
**Quando** o SSL é habilitado via Let's Encrypt
**Então** o Nginx obtém certificado automaticamente
**E** o certificado é renovado automaticamente
**E** as conexões HTTP são redirecionadas para HTTPS

---

### AC-M11-006 [Backend] — Variáveis de ambiente seguras

**Dado** que o sistema usa variáveis de ambiente para configuração
**Quando** o deploy é preparado
**Então** um arquivo `.env.prod.example` existe no repositório
**E** o arquivo `.env.prod.example` contém todas as variáveis necessárias
**E** o arquivo `.env` real não está no repositório (listado no `.gitignore`)
**E** senhas e segredos não são commitados

---

### AC-M11-007 [Backend] — Backup automatizado do banco de dados

**Dado** que o sistema usa PostgreSQL
**Quando** o serviço de backup é configurado
**Então** backups são executados automaticamente via `pg_dump`
**E** a frequência de backup é configurável (padrão: diária)
**E** os backups são retidos por um período configurável (padrão: 7 dias)
**E** os backups são salvos em volume Docker dedicado
**E** um script de restauração está disponível

---

### AC-M11-008 [Backend] — Healthchecks dos serviços

**Dado** que os serviços estão em execução
**Quando** um healthcheck é verificado
**Então** o banco de dados responde a `pg_isready`
**E** o backend responde a um endpoint de health
**E** o frontend está acessível
**E** o Nginx está servindo requisições

---

### AC-M11-009 [Backend] — Guia de deploy

**Dado** que o sistema precisa ser deployado em uma VPS
**Quando** o guia de deploy é consultado
**Então** o guia lista os pré-requisitos do servidor
**E** o guia descreve como clonar o repositório
**E** o guia descreve como configurar as variáveis de ambiente
**E** o guia descreve como configurar domínio e DNS
**E** o guia descreve como iniciar os serviços
**E** o guia descreve como obter certificado SSL
**E** o guia descreve como verificar o funcionamento
**E** o guia descreve como executar backup inicial

---

### AC-M11-010 [Backend] — Banco de dados não exposto

**Dado** que o sistema está em execução em produção
**Quando** a rede é inspecionada
**Então** a porta 5432 do PostgreSQL não é acessível externamente
**E** apenas containers na rede Docker interna podem acessar o banco

---

## Frontend

### AC-M11-011 [Frontend] — Build estático do frontend

**Dado** que o frontend é uma aplicação Vue/Vite
**Quando** o build de produção é executado
**Então** os arquivos estáticos são gerados na pasta de saída
**E** os arquivos incluem HTML, CSS e JavaScript otimizados
**E** os arquivos são servidos corretamente pelo Nginx

---

### AC-M11-012 [Frontend] — Frontend acessível via HTTPS

**Dado** que o sistema está deployado com SSL
**Quando** o usuário acessa o domínio via HTTPS
**Então** a aplicação frontend carrega corretamente
**E** os recursos estáticos (CSS, JS, imagens) são carregados via HTTPS
**E** não há conteúdo misto (mixed content) — todos os recursos usam HTTPS

---

### AC-M11-013 [Frontend] — Frontend conecta ao backend via Nginx

**Dado** que o frontend e backend estão atrás do Nginx
**Quando** o frontend faz requisições à API
**Então** as requisições são roteadas corretamente pelo Nginx
**E** o frontend consegue comunicar com o backend sem erros de CORS
**E** as requisições de API usam o mesmo domínio (via reverse proxy)

---

## Test Coverage Matrix

| AC ID | Test Name | File | Line | Status |
|-------|-----------|------|------|--------|
| AC-M11-001 | Verificar Dockerfile backend sem --reload | Manual | — | ✗ |
| AC-M11-002 | Verificar build estático do frontend | Manual | — | ✗ |
| AC-M11-003 | Verificar docker-compose.prod.yml | Manual | — | ✗ |
| AC-M11-004 | Verificar roteamento do Nginx | Manual | — | ✗ |
| AC-M11-005 | Verificar certificado SSL | Manual | — | ✗ |
| AC-M11-006 | Verificar .env.prod.example e .gitignore | Manual | — | ✗ |
| AC-M11-007 | Verificar backup e restauração | Manual | — | ✗ |
| AC-M11-008 | Verificar healthchecks | Manual | — | ✗ |
| AC-M11-009 | Verificar guia de deploy | Manual | — | ✗ |
| AC-M11-010 | Verificar porta 5432 não exposta | Manual | — | ✗ |
| AC-M11-011 | Verificar build estático | Manual | — | ✗ |
| AC-M11-012 | Verificar HTTPS sem mixed content | Manual | — | ✗ |
| AC-M11-013 | Verificar comunicação frontend-backend | Manual | — | ✗ |

**Nota:** M11 é um marco de infraestrutura. A validação é predominantemente manual — os critérios são verificados pelo deploy e teste em ambiente real ou simulado. Não há testes unitários tradicionais para infraestrutura Docker/Nginx.
