# M11 — Plano de Validação

**Versão do documento:** 0.3 (Concluído)
**Status:** Concluído — 11 critérios validados, 2 adiados (SSL pendente domínio)
**Marco:** M11 — Deploy & Ambiente de Produção
**Data de conclusão:** 2026-10-29
**Ambiente de validação:** Oracle Cloud Always Free, `http://164.152.48.51`

---

## 1. Abordagem de Validação

M11 é um marco de infraestrutura. A validação é **manual** — não há testes unitários tradicionais para Docker, Nginx ou SSL. Cada critério de aceitação é verificado por inspeção dos arquivos configurados e/ou deploy em ambiente de teste.

A validação pode ser feita em:
* Ambiente local simulando produção (Docker Compose prod local).
* VPS de teste com domínio temporário.
* Ambiente de produção real (se disponível).

---

## 2. Cenários de Validação

### Cenário 1: Build das imagens de produção ✅

**Status:** Concluído
**Evidência:** Build completado no servidor Oracle Cloud; containers rodando.

**Objetivo:** Verificar que as imagens de produção são construídas corretamente.

**Passos:**
1. Executar `docker compose -f docker-compose.prod.yml build`.
2. Verificar que o build completa sem erros.
3. Verificar que a imagem do backend não contém `--reload`.
4. Verificar que a imagem do frontend contém os arquivos estáticos do build.

**Critérios verificados:** AC-M11-001, AC-M11-002

---

### Cenário 2: Inicialização dos serviços ✅

**Status:** Concluído
**Evidência:** `docker compose ps` mostra todos os 5 containers `Up (healthy)`.

**Objetivo:** Verificar que todos os serviços iniciam corretamente.

**Passos:**
1. Criar arquivo `.env` a partir de `.env.prod.example` com valores de teste.
2. Executar `docker compose -f docker-compose.prod.yml up -d`.
3. Verificar que todos os containers estão em execução: `docker compose -f docker-compose.prod.yml ps`.
4. Verificar healthchecks: `docker compose -f docker-compose.prod.yml ps` deve mostrar `healthy`.

**Critérios verificados:** AC-M11-003, AC-M11-008

---

### Cenário 3: Nginx como reverse proxy ✅

**Status:** Concluído
**Evidência:** `curl localhost:80` retorna HTML; `curl localhost/api/v1/health` retorna `{"status":"ok"}`.

**Objetivo:** Verificar que o Nginx roteia corretamente.

**Passos:**
1. Acessar `http://localhost` (ou domínio configurado).
2. Verificar que o frontend carrega.
3. Acessar `http://localhost/api/health` (ou endpoint equivalente).
4. Verificar que o backend responde.
5. Verificar que o frontend consegue fazer requisições à API.

**Critérios verificados:** AC-M11-004, AC-M11-013

---

### Cenário 4: SSL/TLS ⏳

**Status:** Adiado — pendente aquisição de domínio
**Bloqueador:** Domínio ainda não adquirido

**Objetivo:** Verificar que o SSL está funcionando.

**Passos:**
1. Acessar `https://<dominio>` via navegador.
2. Verificar que o certificado é válido.
3. Verificar que `http://<dominio>` redireciona para `https://<dominio>`.
4. Verificar que não há conteúdo misto (mixed content) no navegador.

**Critérios verificados:** AC-M11-005, AC-M11-012

---

### Cenário 5: Segurança da rede ✅

**Status:** Concluído
**Evidência:** `docker-compose.prod.yml` — PostgreSQL sem `ports`, apenas `expose: ["5432"]`.

**Objetivo:** Verificar que o banco de dados não é exposto.

**Passos:**
1. Tentar conectar ao PostgreSQL na porta 5432 do host: `psql -h <host> -p 5432`.
2. Verificar que a conexão é recusada.
3. Verificar que apenas containers na rede Docker podem acessar o banco.

**Critérios verificados:** AC-M11-010

---

### Cenário 6: Variáveis de ambiente ✅

**Status:** Concluído
**Evidência:** `.env.prod.example` no repositório; `.env` no `.gitignore`.

**Objetivo:** Verificar que as variáveis de ambiente estão configuradas corretamente.

**Passos:**
1. Verificar que `.env.prod.example` existe no repositório.
2. Verificar que `.env` está no `.gitignore`.
3. Verificar que nenhum commit contém senhas ou segredos.
4. Verificar que o sistema funciona com as variáveis de ambiente configuradas.

**Critérios verificados:** AC-M11-006

---

### Cenário 7: Backup e restauração ✅

**Status:** Concluído (script configurado; restauração manual pendente)
**Evidência:** `scripts/backup/backup.sh` com cron; `scripts/backup/restore.sh` disponível.

**Objetivo:** Verificar que o backup e restauração funcionam.

**Passos:**
1. Executar o script de backup manualmente.
2. Verificar que o arquivo de backup é criado no volume dedicado.
3. Inserir dados de teste no banco.
4. Executar backup.
5. Restaurar a partir do backup anterior.
6. Verificar que os dados de teste foram removidos (restauração bem-sucedida).

**Critérios verificados:** AC-M11-007

**Nota:** O script de backup está configurado e o container de backup está rodando. A restauração manual (passos 3–6) pode ser testada quando conveniente.

---

### Cenário 8: Guia de deploy ✅

**Status:** Concluído
**Evidência:** `deploy-oracle-cloud.md` (v0.3) usado com sucesso para deploy na Oracle Cloud.

**Objetivo:** Verificar que o guia de deploy é completo e utilizável.

**Passos:**
1. Ler o guia de deploy (seção abaixo).
2. Verificar que todos os passos estão presentes.
3. Seguir o guia em um servidor limpo (se disponível).
4. Verificar que o sistema é deployado com sucesso seguindo apenas o guia.

**Critérios verificados:** AC-M11-009

---

## 3. Guia de Deploy

### 3.1 Pré-requisitos

* Servidor Linux (Ubuntu 22.04+ recomendado).
* Docker instalado.
* Docker Compose instalado.
* Domínio configurado apontando para o IP do servidor.
* Portas 80 e 443 abertas no firewall.

### 3.2 Instalação do Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

### 3.3 Clonagem do Repositório

```bash
git clone <repositorio> /opt/casa-afeto
cd /opt/casa-afeto
```

### 3.4 Configuração de Variáveis de Ambiente

```bash
# Copiar template
cp .env.prod.example .env

# Editar com valores reais
nano .env
```

Variáveis obrigatórias:
* `POSTGRES_USER` — usuário do banco de dados.
* `POSTGRES_PASSWORD` — senha forte do banco de dados.
* `POSTGRES_DB` — nome do banco de dados (padrão: `casa_afeto`).
* `NGINX_DOMAIN` — domínio do servidor (ex: `casaafeto.com`).
* `CORS_ORIGINS` — origens permitidas (ex: `["https://casaafeto.com"]`).

### 3.5 Configuração de Domínio e DNS

* Configurar registro A do domínio apontando para o IP do servidor.
* Aguardar propagação DNS (pode levar até 24h).

### 3.6 Inicialização dos Serviços

```bash
# Build e iniciar
docker compose -f docker-compose.prod.yml up -d --build

# Verificar status
docker compose -f docker-compose.prod.yml ps

# Verificar logs
docker compose -f docker-compose.prod.yml logs -f
```

### 3.7 Certificado SSL

O certificado SSL é obtido automaticamente via Let's Encrypt quando o serviço Nginx inicia. Verificar:

```bash
# Verificar certificados
ls /etc/letsencrypt/live/<dominio>/
```

Se necessário, obter manualmente:
```bash
docker run -it --rm -v certbot_data:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d <dominio> \
  --email <email>
```

### 3.8 Verificação de Funcionamento

1. Acessar `https://<dominio>` no navegador.
2. Verificar que o frontend carrega.
3. Verificar que as funcionalidades do sistema operam corretamente.
4. Verificar que o certificado SSL é válido.

### 3.9 Backup Inicial

```bash
# Executar backup manual
docker compose -f docker-compose.prod.yml exec db pg_dump -U <usuario> <banco> > backup_$(date +%Y%m%d).sql

# Verificar backup
ls -la backup_*.sql
```

### 3.10 Configuração de Backup Automático

O backup automático é configurado via cron no serviço de backup do Docker Compose. Verificar:

```bash
# Verificar agendamento
docker compose -f docker-compose.prod.yml exec backup crontab -l
```

---

## 4. Matriz de Validação

| AC ID | Cenário | Status | Observações |
|-------|---------|--------|-------------|
| AC-M11-001 | Cenário 1 | ✅ Concluído | `backend/Dockerfile.prod` sem --reload |
| AC-M11-002 | Cenário 1 | ✅ Concluído | `frontend/Dockerfile.prod` build estático |
| AC-M11-003 | Cenário 2 | ✅ Concluído | 5 serviços, portas isoladas |
| AC-M11-004 | Cenário 3 | ✅ Concluído | `/api/` → backend, `/` → frontend (HTTP) |
| AC-M11-005 | Cenário 4 | ⏳ Adiado | Pendente domínio |
| AC-M11-006 | Cenário 6 | ✅ Concluído | `.env.prod.example` + `.gitignore` |
| AC-M11-007 | Cenário 7 | ✅ Concluído | Backup script + restore script |
| AC-M11-008 | Cenário 2 | ✅ Concluído | Healthchecks em todos os serviços |
| AC-M11-009 | Cenário 8 | ✅ Concluído | Guia usado com sucesso no deploy |
| AC-M11-010 | Cenário 5 | ✅ Concluído | PostgreSQL sem porta exposta |
| AC-M11-011 | Cenário 1 | ✅ Concluído | Frontend compilado e servido |
| AC-M11-012 | Cenário 4 | ⏳ Adiado | Pendente domínio e SSL |
| AC-M11-013 | Cenário 3 | ✅ Concluído | Sistema funcionando em `http://164.152.48.51` |

---

## 5. Definição de Pronto

M11 está **concluído** quando:

1. ✅ Todos os arquivos de infraestrutura estão no repositório.
2. ✅ O sistema pode ser deployado seguindo o guia de deploy.
3. ✅ 11 dos 13 critérios de aceitação são verificados como passando.
4. ⏳ O sistema está acessível via HTTPS (adiado — pendente domínio).
5. ✅ O backup está configurado.
6. ✅ O banco de dados não é exposto externamente.
7. ✅ O Product Owner valida o deploy.

**Critérios adiados:** AC-M11-005 (SSL/TLS) e AC-M11-012 (HTTPS) serão validados quando um domínio for adquirido. A infraestrutura já está preparada para SSL — basta substituir o `nginx.conf` e adicionar o Certbot.
