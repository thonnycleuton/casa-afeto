# M11 — Deploy & Ambiente de Produção

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — implementação em andamento
**Marco:** M11 — Fase 3 — Infraestrutura & Acesso

---

## 1. Finalidade

Este marco prepara o sistema Casa Afeto para operar em um ambiente de produção acessível, com banco de dados PostgreSQL, reverse proxy Nginx, SSL/TLS e práticas básicas de operação.

O objetivo não é introduzir novas funcionalidades de negócio, mas garantir que o sistema existente possa ser executado de forma confiável fora do ambiente de desenvolvimento.

---

## 2. Escopo

### 2.1 Inclui

M11 inclui:

* **Dockerfiles de produção** — imagens otimizadas para backend e frontend (sem `--reload`, sem volumes de código fonte, build estático do frontend).
* **Docker Compose de produção** — arquivo `docker-compose.prod.yml` com todos os serviços (PostgreSQL, backend, frontend, Nginx) configurados para produção.
* **Nginx como reverse proxy** — roteamento de requisições do frontend e backend através de um único ponto de entrada.
* **SSL/TLS via Let's Encrypt** — configuração para obtenção e renovação automática de certificados.
* **Variáveis de ambiente seguras** — arquivo `.env.prod.example` com todas as variáveis necessárias; senhas e segredos nunca commitados.
* **Backup de banco de dados** — script de backup automatizado do PostgreSQL via cron ou serviço dedicado.
* **Monitoramento básico** — healthchecks nos containers e verificação de disponibilidade dos serviços.
* **Guia de deploy** — documento com instruções passo a passo para deploy em uma VPS Linux genérica.

### 2.2 Fora do Escopo

M11 não implementa:

* CI/CD automatizado (GitHub Actions, GitLab CI, etc.) — pode ser adicionado futuramente.
* Autenticação de usuários — pertence ao M12.
* Orquestração Kubernetes — complexidade desnecessária para o estágio atual.
* Load balancing entre múltiplas instâncias.
* CDN ou otimização de assets estáticos além do build do frontend.
* Logs centralizados (ELK, Loki, etc.) — logs de container são suficientes neste estágio.
* Alertas automatizados por email ou SMS.

---

## 3. Arquitetura de Produção

### 3.1 Serviços

```
┌─────────────────────────────────────────────┐
│                  Internet                    │
└──────────────────┬──────────────────────────┘
                   │  HTTPS (443)
                   ▼
         ┌─────────────────┐
         │     Nginx        │  ← Reverse proxy + SSL termination
         │  (porta 443/80)  │
         └────┬────────┬────┘
              │        │
      HTTP   │        │  HTTP
      /api   │        │  / (SPA)
       ▼     │        │    ▼
┌────────────┐     ┌────────────┐
│  Backend   │     │  Frontend  │
│  (porta    │     │  (build    │
│   8000)    │     │   estático)│
└─────┬──────┘     └────────────┘
      │
      │  PostgreSQL
      ▼
┌────────────┐
│   Banco    │
│  (porta    │
│   5432)    │  ← Não exposto externamente
└────────────┘
```

### 3.2 Rede

* O banco de dados PostgreSQL **não é exposto** para fora da rede Docker.
* O backend expõe a porta 8000 apenas internamente (rede Docker).
* O frontend serve arquivos estáticos apenas internamente (rede Docker).
* O Nginx é o único serviço exposto nas portas 80 (HTTP → redirect HTTPS) e 443 (HTTPS).

### 3.3 Persistência

* Dados do PostgreSQL persistidos em volume Docker (`postgres_data`).
* Backups periódicos salvos em volume dedicado (`backups`).
* Uploads de comprovantes de pagamento (se aplicável) persistidos em volume (`uploads`).

---

## 4. Variáveis de Ambiente

As variáveis de ambiente necessárias para produção são:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `ENVIRONMENT` | Ambiente de execução | `production` |
| `DEBUG` | Modo debug do backend | `false` |
| `POSTGRES_SERVER` | Host do banco de dados | `db` |
| `POSTGRES_PORT` | Porta do banco de dados | `5432` |
| `POSTGRES_DB` | Nome do banco de dados | `casa_afeto` |
| `POSTGRES_USER` | Usuário do banco de dados | (definido pelo operador) |
| `POSTGRES_PASSWORD` | Senha do banco de dados | (definido pelo operador) |
| `DATABASE_URL` | URL completa de conexão | `postgresql+psycopg2://USER:PASS@db:5432/DB` |
| `CORS_ORIGINS` | Origens permitidas | `["https://dominio.com"]` |
| `NGINX_DOMAIN` | Domínio do servidor | `casaafeto.com` |

**Importante:** O arquivo `.env` de produção **nunca** deve ser commitado no repositório. Um arquivo `.env.prod.example` será fornecido como template.

---

## 5. Backup

### 5.1 Estratégia

* Backups automáticos do banco de dados PostgreSQL via `pg_dump`.
* Frequência: diária (configurável via cron).
* Retenção: últimos 7 backups (configurável).
* Localização: volume Docker dedicado (`backups`).

### 5.2 Restauração

* Script de restauração disponível para reverter o banco a partir de um backup.
* Restauração manual — não automatizada neste marco.

---

## 6. Monitoramento Básico

* **Healthchecks** nos containers Docker (backend, frontend, banco de dados).
* **Logs** acessíveis via `docker compose logs`.
* **Verificação de disponibilidade** — endpoint de health do backend (`/api/health` ou similar).

---

## 7. Guia de Deploy

O guia de deploy será incluído no `validation.md` e cobrirá:

1. Pré-requisitos do servidor (Linux, Docker, Docker Compose).
2. Clonagem do repositório.
3. Configuração de variáveis de ambiente.
4. Configuração de domínio e DNS.
5. Inicialização dos serviços.
6. Obtenção de certificado SSL.
7. Verificação de funcionamento.
8. Execução de backup inicial.

---

## 8. Dependências

* Fase 1 concluída (M1–M5).
* Fase 2 concluída (M6–M10).
* Código backend e frontend funcionais e testados.

---

## 9. Critérios de Não-Qualidade

M11 não deve:

* Introduzir complexidade desnecessária (Kubernetes, CI/CD, service mesh).
* Modificar a lógica de negócio existente.
* Alterar a API ou o contrato frontend/backend de forma que quebre o sistema atual.
* Expor o banco de dados diretamente à internet.
* Commitar senhas ou segredos no repositório.

---

## 10. Relação com M12

M11 prepara a infraestrutura para que M12 (Autenticação) possa ser implementado com segurança. M12 dependerá de:

* Ambiente de produção acessível via HTTPS.
* Variáveis de ambiente configuráveis.
* Backend capaz de lidar com sessões ou tokens (já suportado por FastAPI).

---

## 11. Decisões Pendentes

* **Ambiente de hospedagem:** A ser definido pelo Product Owner (VPS, cloud provider, etc.). A especificação é genérica e funciona em qualquer servidor Linux com Docker.
* **Domínio:** O domínio final será definido quando o ambiente de hospedagem for escolhido.
* **Frequência de backup:** Padrão de diária com retenção de 7 dias pode ser ajustado conforme necessidade do negócio.
