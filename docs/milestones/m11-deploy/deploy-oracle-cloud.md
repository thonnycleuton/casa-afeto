# Guia de Deploy — Casa Afeto na Oracle Cloud

**Versão:** 0.3  
**Provedor:** Oracle Cloud Always Free  
**Shape:** VM.Standard.E2.1.Micro (1 OCPU, 1 GB RAM)  
**Última atualização:** 2026-10-29  
**Status:** Deploy concluído e sistema funcionando

---

## Visão geral

Este guia descreve como configurar e fazer deploy do sistema Casa Afeto em uma instância Oracle Cloud Always Free com recursos limitados.

**Recursos da instância:**
- 1 OCPU (x86 Intel/AMD)
- 1 GB de RAM
- 50 GB de disco
- 10 TB de rede/mês
- **Custo:** R$ 0,00/mês (grátis para sempre)

**Uso previsto:** 2 usuários simultâneos (1 operador + 1 admin).

**⚠️ Nota:** Esta configuração é otimizada para aprendizado e uso leve. Para produção com mais usuários, use pelo menos 2 GB de RAM (shape VM.Standard.A1.Flex com 2 OCPU + 12 GB RAM).

---

## Otimizações para 1 GB de RAM

Os arquivos de deploy foram otimizados para funcionar com 1 GB de RAM:

| Serviço | Limite de Memória | Otimização |
|---------|-------------------|------------|
| PostgreSQL | 256 MB | shared_buffers=32MB, max_connections=10 |
| Backend FastAPI | 256 MB | 1 worker uvicorn |
| Frontend Nginx | 64 MB | Nginx Alpine |
| Nginx reverse proxy | 32 MB | worker_processes=1, worker_connections=64 |
| Backup | 64 MB | pg_dump com retenção configurável |
| **Total estimado** | **~472 MB** | Sobram ~500 MB para o sistema |

---

## Passo 1: Criar a instância no Oracle Cloud

### 1.1 Acessar o console

1. Acesse https://cloud.oracle.com/ e faça login.
2. No menu principal, navegue até **Compute → Instâncias**.

### 1.2 Criar a instância

1. Clique em **Criar instância**.
2. Nome da instância: `casa-afeto-prod`
3. **Compartment:** selecione o compartment padrão.

### 1.3 Selecionar a imagem

1. Clique em **Change image**.
2. Busque por **Ubuntu 24.04**.
3. Selecione `Canonical Ubuntu 24.04` — escolha a versão mais recente.

### 1.4 Selecionar o shape

Use um dos seguintes shapes Always Free:

**Opção A — VM.Standard.E2.1.Micro** (se A1.Flex não estiver disponível):
- 1 OCPU, 1 GB RAM
- Este é o shape usado neste guia

**Opção B — VM.Standard.A1.Flex** (recomendado, se disponível):
- 2 OCPU, 12 GB RAM
- Se este shape estiver disponível, use-o — o sistema funcionará melhor

### 1.5 Chaves SSH

1. No campo **SSH keys**, cole sua chave pública SSH (`~/.ssh/id_ed25519.pub`).
2. Se não tiver chave SSH, crie uma localmente:
   ```bash
   ssh-keygen -t ed25519 -C "casa-afeto-deploy"
   cat ~/.ssh/id_ed25519.pub
   ```

### 1.6 Rede

Configure a rede conforme descrito na seção de configuração de rede:
- Crie uma VCN usando o **VCN Wizard** (VCN com conectividade à Internet)
- Selecione a sub-rede pública criada pelo Wizard
- Marque **Designar endereço IPv4 público automaticamente**

### 1.7 Criar

Clique em **Criar**. Aguarde a instância ser provisionada (1-2 minutos).

### 1.8 Anotar o IP público

Quando a instância estiver **Running**, anote o **IP público** exibido na página de detalhes.

---

## Passo 2: Configurar o firewall (Security Lists)

### 2.1 Abrir portas no Oracle Cloud

Na página da instância, configure as **Security Lists** ou **Security Groups** para permitir:

| Porta | Protocolo | Fonte | Descrição |
|-------|-----------|-------|-----------|
| 22 | TCP | 0.0.0.0/0 | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP |

**Nota:** A porta 443 (HTTPS) não é necessária agora — o sistema usa HTTP sem SSL. Abra a porta 443 futuramente quando configurar domínio + SSL.

### 2.2 Configurar firewall local (ufw)

Depois de conectar via SSH (Passo 3), execute:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw enable
```

---

## Passo 3: Conectar via SSH

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<IP_PUBLICO>
```

Substitua `<IP_PUBLICO>` pelo IP da instância.

---

## Passo 4: Instalar Docker e Docker Compose

### 4.1 Atualizar o sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 4.2 Instalar Docker

```bash
# Instalar dependências
sudo apt install -y ca-certificates curl gnupg

# Adicionar chave GPG do Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Adicionar repositório do Docker (ARM64)
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 4.3 Permitir usuário ubuntu usar Docker

```bash
sudo usermod -aG docker ubuntu
newgrp docker
```

### 4.4 Verificar instalação

```bash
docker --version
docker compose version
```

Ambos devem retornar as versões instaladas.

### 4.5 Adicionar swap (obrigatório para 1 GB RAM)

Com apenas 1 GB de RAM, o build do frontend (Node.js + TypeScript) esgota a memória. O swap funciona como memória virtual no disco.

```bash
# Criar arquivo de swap de 2 GB
sudo fallocate -l 2G /swapfile

# Proteger o arquivo
sudo chmod 600 /swapfile

# Configurar como swap
sudo mkswap /swapfile

# Ativar o swap
sudo swapon /swapfile

# Tornar permanente (sobrevive ao reboot)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verificar se está ativo
free -h
```

O `free -h` deve mostrar `Swap: 2.0Gi`.

---

## Passo 5: Clonar o repositório

### 5.1 Instalar Git

```bash
sudo apt install -y git
```

### 5.2 Clonar o projeto

```bash
cd ~
git clone https://github.com/<SEU_USUARIO>/casa-afeto.git
cd casa-afeto
```

Substitua `<SEU_USUARIO>` pelo seu usuário do GitHub.

Se o repositório é privado, configure o acesso SSH:

```bash
# Copiar a chave SSH para o GitHub
ssh-copy-id git@github.com

# Ou clonar com token
git clone https://<TOKEN>@github.com/<SEU_USUARIO>/casa-afeto.git
```

---

## Passo 6: Configurar variáveis de ambiente

### 6.1 Criar arquivo .env

```bash
cp .env.prod.example .env
nano .env
```

### 6.2 Preencher as variáveis

```bash
# Database — usar senha forte!
POSTGRES_USER=casa_afeto
POSTGRES_PASSWORD=<SENHA_FORTE_AQUI>
POSTGRES_DB=casa_afeto

# Backend — usar IP público inicialmente
CORS_ORIGINS=["http://<IP_PUBLICO>"]

# Backup
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION=7
```

**Importante:** Substitua `<SENHA_FORTE_AQUI>` por uma senha forte e `<IP_PUBLICO>` pelo IP público da sua instância.

### 6.3 Proteger o arquivo .env

```bash
chmod 600 .env
```

---

## Passo 7: Subir os containers

**Nota:** Os arquivos `nginx/nginx.conf` e `docker-compose.prod.yml` já vêm configurados para HTTP simples (sem SSL) e otimizados para 1 GB de RAM. Não é necessário ajustá-los manualmente.

### 7.1 Build e start

```bash
cd ~/casa-afeto
docker compose -f docker-compose.prod.yml up -d --build
```

Este comando:
1. Baixa as imagens base (PostgreSQL, Nginx, Node, Python).
2. Compila o backend e o frontend.
3. Inicia todos os containers.

**Tempo estimado:** 5-10 minutos na primeira execução.

### 7.2 Verificar status

```bash
docker compose -f docker-compose.prod.yml ps
```

Todos os serviços devem estar `Up` e `healthy`.

### 7.3 Verificar logs

```bash
# Logs do backend
docker compose -f docker-compose.prod.yml logs backend

# Logs do frontend
docker compose -f docker-compose.prod.yml logs frontend

# Logs do banco
docker compose -f docker-compose.prod.yml logs db
```

---

## Passo 8: Executar migrations do banco

```bash
# Executar migrations diretamente no container
docker exec casa_afeto_backend_prod alembic upgrade head

# Verificar a versão atual
docker exec casa_afeto_backend_prod alembic current
```

---

## Passo 9: Verificar o deploy

### 9.1 Testar acesso

No navegador, acesse:

```
http://<IP_PUBLICO>
```

O frontend do Casa Afeto deve carregar.

### 9.2 Testar API

```bash
curl http://<IP_PUBLICO>/health
```

Deve retornar `{"status":"ok"}` ou similar.

### 9.3 Testar endpoints

```bash
curl http://<IP_PUBLICO>/api/v1/products
```

Deve retornar a lista de produtos (vazia inicialmente).

---

## Passo 10: Configurar domínio (futuro)

Quando um domínio for adquirido:

### 10.1 Apontar DNS

No painel do registrador de domínio, criar um registro **A**:

```
Tipo: A
Nome: @ (ou casaafeto.com.br)
Valor: <IP_PUBLICO>
```

### 10.2 Configurar SSL no Nginx

Substituir o `nginx/nginx.conf` pela versão com SSL/TLS.

### 10.3 Obter certificado Let's Encrypt

```bash
# Subir o certbot
docker compose -f docker-compose.prod.yml --profile certbot up certbot

# Reiniciar o Nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### 10.4 Atualizar CORS

```bash
nano .env
# Atualizar CORS_ORIGINS e NGINX_DOMAIN com o domínio
CORS_ORIGINS=["https://casaafeto.com.br"]
NGINX_DOMAIN=casaafeto.com.br
```

### 10.5 Reiniciar

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## Comandos úteis

### Parar todos os serviços

```bash
docker compose -f docker-compose.prod.yml down
```

### Reiniciar após mudanças

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Ver logs em tempo real

```bash
docker compose -f docker-compose.prod.yml logs -f
```

### Verificar uso de recursos

```bash
# Memória e CPU dos containers
docker stats

# Espaço em disco
df -h

# Volume do PostgreSQL
docker volume ls
```

### Backup manual

```bash
# Executar backup manual
docker compose -f docker-compose.prod.yml exec backup /backup-scripts/backup.sh
```

---

## Monitoramento e Troubleshooting

### Verificar uso de memória

```bash
# Memória e CPU dos containers
docker stats --format "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}"

# Memória do sistema
free -h

# Processos que consomem mais memória
ps aux --sort=-%mem | head -10
```

### Se um container cair (OOM Killer)

Se um container for encerrado por falta de memória:

```bash
# Verificar logs do sistema
dmesg | grep -i "out of memory"

# Verificar status dos containers
docker compose -f docker-compose.prod.yml ps

# Reiniciar o container caído
docker compose -f docker-compose.prod.yml restart <servico>
```

**Solução:** Aumente o limite de memória do container no `docker-compose.prod.yml` ou reduza os limites dos outros serviços.

### Se o PostgreSQL ficar lento

```bash
# Verificar conexões ativas
docker compose -f docker-compose.prod.yml exec db psql -U casa_afeto -c "SELECT count(*) FROM pg_stat_activity;"

# Verificar queries lentas
docker compose -f docker-compose.prod.yml exec db psql -U casa_afeto -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 5;"
```

### Se o sistema ficar lento com 2 usuários

1. Verifique o uso de memória: `docker stats`
2. Se o PostgreSQL estiver usando >200 MB, reduza `shared_buffers` para 16MB
3. Se o backend estiver usando >200 MB, verifique os logs: `docker compose -f docker-compose.prod.yml logs backend`

### Logs em tempo real

```bash
# Todos os serviços
docker compose -f docker-compose.prod.yml logs -f

# Serviço específico
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## Migração para shape com mais recursos

Quando conseguir acesso ao shape **VM.Standard.A1.Flex** (2 OCPU + 12 GB RAM):

1. Crie a nova instância com o shape A1.Flex
2. Faça backup do banco na instância atual:
   ```bash
   docker compose -f docker-compose.prod.yml exec db pg_dump -U casa_afeto casa_afeto > backup.sql
   ```
3. Transfira o backup para a nova instância:
   ```bash
   scp backup.sql ubuntu@<NOVO_IP>:/tmp/
   ```
4. Na nova instância, restaure o banco:
   ```bash
   docker compose -f docker-compose.prod.yml exec -T db psql -U casa_afeto casa_afeto < /tmp/backup.sql
   ```
5. Atualize o DNS ou acesse pelo novo IP

### Restaurar backup

```bash
# Listar backups disponíveis
docker compose -f docker-compose.prod.yml exec backup ls -lt /backups/

# Restaurar um backup específico
docker compose -f docker-compose.prod.yml exec backup /backup-scripts/restore.sh /backups/backup_YYYYMMDD_HHMMSS.sql.gz
```

---

## Notas sobre arquitetura ARM

O Oracle Cloud usa processadores **ARM Ampere A1**. As imagens Docker usadas neste projeto são **multi-architecture** e funcionam nativamente em ARM:

| Imagem | Suporte ARM64 |
|--------|--------------|
| `python:3.12-slim` | ✅ Nativo |
| `node:18-alpine` | ✅ Nativo |
| `nginx:alpine` | ✅ Nativo |
| `postgres:16-alpine` | ✅ Nativo |
| `certbot/certbot` | ✅ Nativo |

Nenhuma modificação nos Dockerfiles é necessária.

---

## Limitações do plano Always Free

- **Instância pode ser desativada** se ficar inativa por 7 dias. Acesse o console periodicamente ou faça requests ao servidor.
- **IP público pode mudar** se a instância for deletada e recriada. Use um domínio para evitar esse problema.
- **Registro pode ser rejeitado** sem explicação. Se isso acontecer, tente em outra região.

---

## Problemas encontrados e resolvidos

Durante o deploy inicial, os seguintes problemas foram encontrados e corrigidos. Esta seção serve como referência para futuros deploys.

### 1. Nginx reiniciando em loop

**Sintoma:** Container `casa_afeto_nginx_prod` em estado `Restarting`.

**Causa:** O arquivo `nginx/nginx.conf` continha `worker_processes`, `events` e `http` — mas como ele é montado como `/etc/nginx/conf.d/default.conf`, o Nginx o inclui **dentro** do bloco `http` principal. Essas diretivas não são permitidas nesse contexto.

**Solução:** Removido `worker_processes`, `events` e wrapper `http`. O arquivo contém apenas o bloco `server`.

### 2. API retornando 404 Not Found

**Sintoma:** `curl http://localhost/api/v1/health` retorna 404.

**Causa:** O `proxy_pass http://backend:8000` (sem trailing slash) no Nginx **stripava** o prefixo `/api/`, enviando `/v1/products` ao backend em vez de `/api/v1/products`.

**Solução:** Mudado para `proxy_pass http://backend:8000/api` para preservar o caminho completo.

### 3. URL duplicada `/api/api/v1/products`

**Sintoma:** Console do navegador mostra `GET /api/api/v1/products 404`.

**Causa:** Os endpoints do frontend já incluem `/api/v1/...` (ex: `/api/v1/products`). O `VITE_API_BASE_URL` era `/api`, criando URLs como `/api/api/v1/products`.

**Solução:** O `VITE_API_BASE_URL` agora é string vazia `''` no `vite.config.ts`.

### 4. Fallback `localhost:8000` ativado em produção

**Sintoma:** Navegador tenta conectar a `http://localhost:8000` (computador do usuário).

**Causa:** No `client.ts`, o código usava `|| 'http://localhost:8000'`. Em JavaScript, string vazia `''` é **falsy**, então `'' || 'http://localhost:8000'` retornava `'http://localhost:8000'`.

**Solução:** Mudado para `?? ''` (nullish coalescing), que só usa o fallback quando o valor é `null` ou `undefined`.

### 5. Backup sem permissão de execução

**Sintoma:** Container de backup falha com `permission denied` ao executar `/backup-scripts/backup.sh`.

**Causa:** O volume montado como `:ro` não preserva o bit de execução do arquivo.

**Solução:** Mudado o entrypoint de `["/backup-scripts/backup.sh"]` para `["sh", "/backup-scripts/backup.sh"]`.

### 6. Build do frontend falhando (1 GB RAM)

**Sintoma:** `npm run build` falha com `exit code 2` durante o Docker build.

**Causa:** O compilador TypeScript + Vue.js esgota os 1 GB de RAM.

**Solução:** Adicionar 2 GB de swap ao servidor antes do build.

### 7. Firewall bloqueando acesso externo

**Sintoma:** `curl localhost:80` funciona, mas `http://<IP>` não responde.

**Causa:** As Security Lists da VCN não tinham regras de entrada para HTTP (porta 80).

**Solução:** Adicionar regra de entrada TCP porta 80 com fonte `0.0.0.0/0` nas Security Lists do Oracle Cloud.

---

## Próximos passos

1. ✅ Criar instância Oracle Cloud
2. ✅ Instalar Docker
3. ✅ Clonar repositório
4. ✅ Configurar .env
5. ✅ Subir containers
6. ✅ Executar migrations
7. ✅ Sistema acessível pelo navegador
8. ⏳ Adquirir domínio
9. ⏳ Configurar SSL/TLS
10. ⏳ Configurar renovação automática de certificado
