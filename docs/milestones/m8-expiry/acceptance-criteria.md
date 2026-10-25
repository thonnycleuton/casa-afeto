# M8 — Critérios de Aceitação

**Versão:** 0.2 (Aprovado)
**Milestone:** M8 — Gestão de Vencimentos

---

## Backend

### AC-M8-001 [Backend] — Vencimento opcional no lote

**Dado** um produto com estoque
**Quando** um lote é criado a partir de uma entrada com `expiry_date`
**Então** o lote armazena a data de vencimento informada

### AC-M8-002 [Backend] — Lote sem vencimento

**Dado** um produto não perecível
**Quando** um lote é criado sem `expiry_date`
**Então** o lote é criado com `expiry_date = NULL`

### AC-M8-003 [Backend] — Vencimento herdado da compra

**Dado** um item de compra com `expiry_date = "2026-11-15"`
**Quando** a compra é registrada
**Então** o lote criado herda `expiry_date = "2026-11-15"`

### AC-M8-004 [Backend] — Vencimento imutável

**Dado** um lote com `expiry_date = "2026-11-15"`
**Quando** se tenta alterar o `expiry_date` do lote
**Então** a alteração é rejeitada

### AC-M8-005 [Backend] — FEFO: consumo pelo vencimento mais próximo

**Dado** dois lotes ativos do mesmo produto:
- Lote A: `expiry_date = "2026-11-01"`, `quantity_remaining = 10`
- Lote B: `expiry_date = "2026-11-15"`, `quantity_remaining = 10`
**Quando** uma saída consome 5 unidades
**Então** o Lote A é consumido primeiro, restando 5 unidades

### AC-M8-006 [Backend] — FEFO: fallback FIFO para lotes sem vencimento

**Dado** dois lotes ativos do mesmo produto:
- Lote A: `expiry_date = "2026-11-01"`, `quantity_remaining = 10`
- Lote B: `expiry_date = NULL`, `created_at = "2026-10-01"`
**Quando** uma saída consome 5 unidades
**Então** o Lote A (com vencimento) é consumido primeiro

### AC-M8-007 [Backend] — FEFO: FIFO entre lotes sem vencimento

**Dado** dois lotes ativos do mesmo produto sem vencimento:
- Lote A: `expiry_date = NULL`, `created_at = "2026-10-01"`, `quantity_remaining = 10`
- Lote B: `expiry_date = NULL`, `created_at = "2026-10-15"`, `quantity_remaining = 10`
**Quando** uma saída consome 5 unidades
**Então** o Lote A (mais antigo) é consumido primeiro

### AC-M8-008 [Backend] — FEFO: consumo cruzando lotes

**Dado** dois lotes ativos:
- Lote A: `expiry_date = "2026-11-01"`, `quantity_remaining = 3`
- Lote B: `expiry_date = "2026-11-15"`, `quantity_remaining = 10`
**Quando** uma saída consome 7 unidades
**Então** o Lote A é esgotado (3 unidades) e o Lote B perde 4 unidades

### AC-M8-009 [Backend] — Lote vencido permanece ativo

**Dado** um lote com `expiry_date = "2026-10-01"` (vencido)
**Quando** o lote é consultado
**Então** o lote retorna com `status = "ACTIVE"` e `expiry_status = "EXPIRED"`

### AC-M8-010 [Backend] — Alerta de vencimento próximo

**Dado** um lote com `expiry_date = "2026-10-25"` (5 dias no futuro, threshold = 7)
**Quando** o lote é consultado via API
**Então** o lote retorna com `expiry_status = "WARNING"`

### AC-M8-011 [Backend] — Alerta de lote vencido

**Dado** um lote com `expiry_date = "2026-10-15"` (já vencido)
**Quando** o lote é consultado via API
**Então** o lote retorna com `expiry_status = "EXPIRED"`

### AC-M8-012 [Backend] — Lote sem vencimento não gera alerta

**Dado** um lote com `expiry_date = NULL`
**Quando** a lista de alertas é consultada
**Então** o lote não aparece nos resultados

### AC-M8-013 [Backend] — Lista global de vencimentos

**Dado** lotes de diferentes produtos com vencimento próximo
**Quando** `GET /inventory/expiry-alerts` é chamado
**Então** todos os lotes com vencimento próximo ou vencido são retornados, ordenados por urgência

### AC-M8-014 [Backend] — Lista global ordenada por urgência

**Dado** lotes com diferentes vencimentos:
- Lote A: vencido há 5 dias
- Lote B: vence em 2 dias
- Lote C: vence em 10 dias (fora do threshold)
**Quando** `GET /inventory/expiry-alerts` é chamado com `threshold_days=7`
**Então** a resposta contém Lote A e Lote B, ordenados com Lote A primeiro

### AC-M8-015 [Backend + Frontend] — Vencimento na entrada manual

**Dado** o formulário de entrada manual de estoque
**Quando** o operador informa `expiry_date`
**Então** o lote criado herda a data de vencimento

### AC-M8-016 [Backend + Frontend] — Vencimento na compra por item

**Dado** uma compra com múltiplos itens
**Quando** apenas alguns itens têm `expiry_date`
**Então** apenas os lotes correspondentes herdam o vencimento

---

## Frontend

### AC-M8-017 [Frontend] — Badge visual no modal de estoque

**Dado** o modal de estoque de um produto com lotes
**Quando** um lote tem `expiry_status = "EXPIRED"`
**Então** o lote exibe um badge vermelho

### AC-M8-018 [Frontend] — Badge de alerta no modal de estoque

**Dado** o modal de estoque de um produto com lotes
**Quando** um lote tem `expiry_status = "WARNING"`
**Então** o lote exibe um badge amarelo

### AC-M8-019 [Frontend] — Sem badge para lotes sem vencimento

**Dado** o modal de estoque de um produto com lotes
**Quando** um lote tem `expiry_date = NULL`
**Então** o lote não exibe badge de vencimento

### AC-M8-025 [Frontend] — Seção "Vencimentos" na navegação

**Dado** o menu lateral da aplicação
**Quando** o usuário clica em "Vencimentos"
**Então** uma nova seção é exibida com a lista global de lotes com alerta de vencimento

### AC-M8-026 [Frontend] — Tabela de alertas com badges

**Dado** a seção "Vencimentos" com lotes em alerta
**Quando** o usuário visualiza a tabela
**Então** cada linha mostra: produto, data de vencimento, dias restantes, quantidade e status com badge colorido (vermelho=vencido, amarelo=próximo)

---

## Backend (continuação)

### AC-M8-020 [Backend] — Threshold configurável

**Dado** `EXPIRY_ALERT_DAYS = 14` configurado
**Quando** um lote vence em 10 dias
**Então** o lote retorna com `expiry_status = "WARNING"`

### AC-M8-021 [Backend] — days_until_expiry calculado

**Dado** um lote com `expiry_date = "2026-10-27"` (hoje = 2026-10-20)
**Quando** o lote é consultado via API de alertas
**Então** `days_until_expiry = 7`

### AC-M8-022 [Backend] — days_until_expiry negativo para vencidos

**Dado** um lote com `expiry_date = "2026-10-15"` (hoje = 2026-10-20)
**Quando** o lote é consultado via API de alertas
**Então** `days_until_expiry = -5`

### AC-M8-023 [Backend] — include_expired=false filtra vencidos

**Dado** lotes vencidos e lotes próximos do vencimento
**Quando** `GET /inventory/expiry-alerts?include_expired=false` é chamado
**Então** apenas lotes próximos do vencimento são retornados, sem os vencidos

### AC-M8-024 [Backend] — Migração: lotes existentes sem vencimento

**Dado** lotes criados pelo M7 sem `expiry_date`
**Quando** a migração do M8 é aplicada
**Então** os lotes existentes têm `expiry_date = NULL` e continuam funcionando

---

*Fim dos critérios de aceitação do M8.*
