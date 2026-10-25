# M8 — Plano de Validação

**Versão:** 0.2 (Aprovado)
**Milestone:** M8 — Gestão de Vencimentos

---

## Cenários de Validação Manual

### Cenário 1: Registrar compra com vencimento

**Objetivo:** Verificar que o vencimento informado na compra é herdado pelo lote.

**Passos:**
1. Abrir o modal de nova compra.
2. Adicionar um item perecível (ex: Bolo caseiro) com data de vencimento (ex: 2026-11-15).
3. Adicionar um item não perecível (ex: Arroz 5kg) sem data de vencimento.
4. Confirmar a compra.
5. Abrir o modal de estoque do Bolo caseiro.
6. Verificar que o lote criado exibe "15/11/2026" na coluna Vencimento.
7. Abrir o modal de estoque do Arroz 5kg.
8. Verificar que o lote criado exibe "—" na coluna Vencimento.

**Resultado esperado:** Lotes com e sem vencimento criados corretamente.

---

### Cenário 2: Registrar entrada manual com vencimento

**Objetivo:** Verificar que o vencimento informado na entrada manual é herdado pelo lote.

**Passos:**
1. Abrir o modal de estoque de um produto perecível.
2. Preencher o formulário de entrada manual com quantidade, custo e data de vencimento.
3. Confirmar a entrada.
4. Verificar que o novo lote exibe a data de vencimento e o badge correspondente.

**Resultado esperado:** Lote criado com vencimento informado.

---

### Cenário 3: Consumo FEFO

**Objetivo:** Verificar que o consumo de estoque segue a política FEFO.

**Passos:**
1. Criar dois lotes do mesmo produto com vencimentos diferentes:
   - Lote A: vencimento 2026-11-01, quantidade 10
   - Lote B: vencimento 2026-11-15, quantidade 10
2. Confirmar uma venda que consome 5 unidades do produto.
3. Abrir o modal de estoque do produto.
4. Verificar que o Lote A tem `quantity_remaining = 5` e o Lote B tem `quantity_remaining = 10`.

**Resultado esperado:** O lote com vencimento mais próximo é consumido primeiro.

---

### Cenário 4: FEFO com fallback FIFO

**Objetivo:** Verificar que lotes sem vencimento são consumidos por FIFO após os lotes com vencimento.

**Passos:**
1. Criar dois lotes do mesmo produto:
   - Lote A: vencimento 2026-11-01, quantidade 10
   - Lote B: sem vencimento, criado em 2026-10-01, quantidade 10
2. Confirmar uma venda que consome 5 unidades.
3. Verificar que o Lote A (com vencimento) é consumido primeiro.

**Resultado esperado:** Lote com vencimento é priorizado sobre lote sem vencimento.

---

### Cenário 5: Alertas de vencimento

**Objetivo:** Verificar que os badges de vencimento são exibidos corretamente.

**Passos:**
1. Criar lotes com diferentes estados de vencimento:
   - Lote vencido (data no passado)
   - Lote próximo do vencimento (dentro do threshold)
   - Lote com vencimento distante
   - Lote sem vencimento
2. Abrir o modal de estoque de cada produto.
3. Verificar os badges:
   - Vencido: badge vermelho
   - Próximo: badge amarelo
   - Distante: sem badge
   - Sem vencimento: sem badge

**Resultado esperado:** Badges exibidos corretamente conforme o estado de vencimento.

---

### Cenário 6: Lista global de vencimentos

**Objetivo:** Verificar que a lista global mostra todos os vencimentos pendentes.

**Passos:**
1. Garantir que existem lotes com vencimento próximo e vencido de diferentes produtos.
2. Acessar a seção de vencimentos.
3. Verificar que a lista exibe todos os lotes pendentes, ordenados por urgência.
4. Verificar que lotes sem vencimento não aparecem na lista.

**Resultado esperado:** Lista global ordenada por urgência, filtrando lotes sem vencimento.

---

## Checklist de Validação Técnica

| Item | Status |
|------|--------|
| Migration aplicada sem erros | ☐ |
| `expiry_date` nullable em `stock_batches` | ☐ |
| `expiry_date` nullable em `purchase_items` | ☐ |
| `consume_fifo` evoluido para FEFO | ☐ |
| `GET /products/{id}/batches` retorna `expiry_date` e `expiry_status` | ☐ |
| `GET /inventory/expiry-alerts` funciona com filtros | ☐ |
| `POST /purchases` aceita `expiry_date` por item | ☐ |
| `POST /inventory/movements` aceita `expiry_date` para ENTRY | ☐ |
| Modal de estoque exibe colunas de vencimento | ☐ |
| Modal de compra exibe campo de vencimento por item | ☐ |
| Entrada manual exibe campo de vencimento | ☐ |
| Badges de vencimento funcionam no modal de estoque | ☐ |
| Testes de backend passam (incluindo M7 existente) | ☐ |
| `vue-tsc --noEmit` sem erros novos | ☐ |
| Lotes existentes do M7 continuam funcionando | ☐ |

---

*Fim do plano de validação do M8.*
