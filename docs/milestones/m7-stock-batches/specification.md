# M7 — Especificação de Lotes de Estoque

**Versão do documento:** 0.1 (RASCUNHO)
**Status:** Rascunho — pendente de aprovação do Product Owner
**Marco:** M7 — Lotes de Estoque
**Fase:** 2 — Evolução do Estoque e dos Clientes

---

# 1. Finalidade

O M7 introduz o conceito de **lote de estoque**, permitindo que cada aquisição de produto seja rastreada como um grupo distinto com custo unitário próprio, quantidade restante e data de entrada.

Antes do M7, o sistema calcula um **custo médio ponderado** do produto a partir de todas as movimentações ENTRY. Esse cálculo será **removido** porque cada produto possui um `reference_price` que serve como preço de referência comercial, e o custo de aquisição de cada lote é preservado para análise futura de variação de preços.

Após o M7, o fluxo será:

```
Registro de compra (M6)
    ↓
Cada item de compra gera um lote
    ↓
Lote com: produto, quantidade, unit_cost, data de entrada
    ↓
Saídas consomem lotes em ordem FIFO
    ↓
Lote esgotado é arquivado, não removido
```

---

# 2. Escopo

## 2.1 Dentro do escopo

O M7 inclui:

### Lote de Estoque

* criar lote automaticamente ao registrar uma compra (M6);
* criar lote automaticamente ao registrar uma entrada manual de estoque;
* cada lote armazena: produto, quantidade original, quantidade restante, `unit_cost`, data de entrada;
* consultar lotes ativos de um produto;
* consultar histórico completo de lotes (ativos e esgotados);
* rastrear lote até a compra de origem via `purchase_id`.

### Consumo FIFO

* ao registrar saída de estoque (OUTPUT), consumir do lote mais antigo primeiro;
* se um lote não tiver quantidade suficiente, consumir o restante e continuar no próximo lote;
* respeitar as regras INV-001 a INV-008 e RES-001 a RES-012.

### Remoção do custo médio ponderado

* remover o cálculo de custo médio ponderado do produto;
* o `reference_price` do produto permanece como preço de referência comercial;
* o `unit_cost` do lote permanece como custo de aquisição rastreável;
* ajustar a API e o frontend para não expor mais o custo médio.

### Migração de dados existentes

* converter as movimentações ENTRY existentes em lotes implícitos;
* preservar o `unit_cost` de cada ENTRY como custo do lote correspondente.

## 2.2 Explicitamente fora do escopo

O seguinte **não** deve ser implementado como parte do M7:

* datas de vencimento (M8);
* política FEFO (M8);
* fornecedores;
* notas fiscais;
* produção interna;
* perdas, avarias e consumo interno;
* alertas de reposição (M9);
* exclusão de lotes — lotes esgotados são arquivados, não deletados.

---

# 3. Dependências

O M7 depende de:

* `docs/domain/business-contract.md` — regras de negócio;
* `docs/product/roadmap.md` — direção da Fase 2;
* `docs/milestones/m1-products-inventory/specification.md` — contratos de estoque;
* `docs/milestones/m6-purchases/specification.md` — compras e itens de compra;
* `docs/architecture/technical-foundation.md` — fundamentos técnicos;
* `docs/architecture/decisions/ADR-001-inventory-concurrency.md` — concorrência de estoque.

O M7 depende da implementação do M6 (compras) e do M1 (estoque).

---

# 4. Conceitos de Domínio

O M7 introduz um novo conceito:

```
Lote de Estoque (StockBatch)
```

Um **Lote de Estoque** representa uma quantidade de produto adquirida em um momento específico, com um custo unitário conhecido. O lote é a unidade de rastreabilidade do estoque.

```
Produto
  ↓
Lote de Estoque
  ├─ product_id
  ├─ purchase_id (opcional — NULL para entradas manuais)
  ├─ quantity_original
  ├─ quantity_remaining
  ├─ unit_cost
  ├─ created_at (data de entrada)
  └─ status: ACTIVE | EXHAUSTED
```

Relação com conceitos existentes:

```
Compra → Item de Compra → Lote de Estoque → Movimentação ENTRY
                                              ↓
                                        (saldo do produto)
```

Cada `PurchaseItem` gera exatamente um `StockBatch`.
Cada entrada manual de estoque gera um `StockBatch` com `purchase_id = NULL`.

---

# 5. Regras de Negócio

### LOT-001 — Criação automática do lote

Cada item de compra gera automaticamente um lote de estoque ao ser registrado. O lote recebe a quantidade convertida para unidade-base e o `unit_cost` calculado a partir do preço comercial e fator de conversão.

### LOT-002 — Entrada manual gera lote

Cada movimentação ENTRY manual (não vinculada a compra) gera um lote implícito com `purchase_id = NULL`.

### LOT-003 — FIFO no consumo

Ao registrar saída de estoque (OUTPUT), o sistema consome do lote mais antigo primeiro, baseado em `created_at`. Se um lote não tiver quantidade suficiente, o consumo continua no próximo lote mais antigo.

### LOT-004 — Lote esgotado é arquivado

Quando `quantity_remaining` chega a zero, o lote muda para status `EXHAUSTED`. O lote não é deletado — permanece no histórico para rastreabilidade.

### LOT-005 — Lote não é deletável

Um lote de estoque não pode ser excluído. Correções são feitas por ajustes de estoque (ADJUSTMENT), não por alteração do lote.

### LOT-006 — Rastreabilidade até a compra

Cada lote vinculado a compra preserva `purchase_id` e `purchase_item_id` para rastreabilidade completa da origem.

### LOT-007 — Custo do lote é imutável

O `unit_cost` do lote não é alterado após a criação. Ele reflete o custo real de aquisição naquele momento.

### LOT-008 — Estoque físico = soma dos lotes ativos

O saldo físico do produto é a soma das `quantity_remaining` de todos os lotes com status `ACTIVE`.

### LOT-009 — Remoção do custo médio ponderado

O cálculo de custo médio ponderado do produto é removido. O `reference_price` do produto serve como preço de referência comercial. O `unit_cost` de cada lote serve para rastreabilidade de custo de aquisição.

### LOT-010 — Concorrência de lotes

As operações que modificam lotes seguem as mesmas regras de concorrência do M1/M5: `SELECT FOR UPDATE` com ordenação por `product_id` para evitar deadlocks.

---

# 6. Comportamento Importante

## 6.1 Migração de dados existentes

As movimentações ENTRY existentes devem ser convertidas em lotes:

```
InventoryMovement (ENTRY)
    ↓
StockBatch com:
  - product_id = movement.product_id
  - purchase_id = movement.purchase_id (pode ser NULL)
  - quantity_original = movement.quantity
  - quantity_remaining = movement.quantity
  - unit_cost = movement.unit_cost
  - created_at = movement.created_at
  - status = ACTIVE
```

Se múltiplos ENTRY do mesmo produto existirem, cada um gera um lote separado, preservando a granularidade temporal.

## 6.2 Impacto no M5 (Reservas e Baixas)

O M5 implementa reserva e baixa de estoque por venda. Com lotes:

* A reserva continua operando no nível do produto (saldo total).
* A baixa física (OUTPUT) consome lotes em ordem FIFO.
* A lógica de reserva (RES-001 a RES-012) permanece válida — a reserva verifica saldo total, não lotes individuais.

## 6.3 Impacto no frontend

* O modal de estoque (`InventoryModal.vue`) deve exibir os lotes ativos do produto selecionado, não apenas o saldo total.
* O histórico de movimentações deve indicar o lote de origem de cada ENTRY.
* O custo médio ponderado não é mais exibido.

---

# 7. Decisões do Product Owner

### D-1: Lote automático por item de compra

Cada item de compra gera automaticamente um lote. Não há opção de criar compra sem lote.

### D-2: FIFO como estratégia de consumo

O consumo de estoque segue First-In-First-Out: o lote mais antigo é consumido primeiro. Esta é uma regra substituível — pode evoluir para FEFO no M8.

### D-3: Remoção do custo médio ponderado

O custo médio ponderado é removido porque cada produto tem `reference_price`. O `unit_cost` do lote serve para rastreabilidade de custo de aquisição, não para cálculo de preço.

---

# 8. Modelo de Dados

## 8.1 Nova tabela: `stock_batches`

```sql
CREATE TABLE stock_batches (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    purchase_id INTEGER REFERENCES purchases(id) ON DELETE SET NULL,
    purchase_item_id INTEGER,
    quantity_original NUMERIC NOT NULL CHECK (quantity_original > 0),
    quantity_remaining NUMERIC NOT NULL CHECK (quantity_remaining >= 0),
    unit_cost NUMERIC CHECK (unit_cost IS NULL OR unit_cost >= 0),
    status VARCHAR(10) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'EXHAUSTED')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_stock_batches_product ON stock_batches(product_id);
CREATE INDEX idx_stock_batches_purchase ON stock_batches(purchase_id);
CREATE INDEX idx_stock_batches_status ON stock_batches(status);
```

## 8.2 Alterações em tabelas existentes

* `inventory_movements`: adicionar `batch_id` (nullable) para vincular cada movimentação ao lote de origem.
* `products`: avaliar remoção de campos relacionados ao custo médio ponderado, se existirem.

---

# 9. API

## 9.1 Novos endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/v1/products/{id}/batches` | Listar lotes de um produto |
| `GET` | `/api/v1/products/{id}/batches/{batch_id}` | Detalhe de um lote |

## 9.2 Endpoints modificados

| Endpoint | Mudança |
|----------|---------|
| `POST /api/v1/purchases` | Agora gera `StockBatch` para cada item |
| `POST /api/v1/products/{id}/inventory/movements` (ENTRY) | Agora gera `StockBatch` |
| `POST /api/v1/products/{id}/inventory/movements` (OUTPUT) | Consome lotes em FIFO |
| `GET /api/v1/products/{id}` | Remover `average_cost` da resposta, se existir |

---

# 10. Frontend

## 10.1 Mudanças no InventoryModal

* Exibir lista de lotes ativos do produto selecionado com: data de entrada, quantidade original, quantidade restante, `unit_cost`, e origem (compra ou manual).
* Manter o saldo total como soma dos lotes ativos.
* Remover exibição do custo médio ponderado, se presente.

## 10.2 Mudanças no histórico de movimentações

* Cada ENTRY deve indicar o lote de origem.
* Cada OUTPUT deve indicar os lotes consumidos.

---

# 11. Testes

Os testes devem cobrir:

* Criação automática de lote ao registrar compra;
* Criação automática de lote ao registrar entrada manual;
* Consumo FIFO com um lote;
* Consumo FIFO com múltiplos lotes (parcial + completo);
* Lote esgotado muda para EXHAUSTED;
* Estoque físico = soma dos lotes ativos;
* Rastreabilidade: lote → compra → item;
* Migração de ENTRY existentes para lotes;
* Concorrência: duas saídas simultâneas do mesmo produto;
* Lote não é deletável;
* `unit_cost` do lote é imutável.

---

# 12. Riscos

1. **Migração de dados:** Se ENTRY existentes tiverem `unit_cost = NULL`, os lotes correspondentes terão custo desconhecido. Mitigação: preservar `NULL` no lote, não forçar zero.
2. **Performance:** Consultar lotes em vez de um único saldo pode ser mais lento. Mitigação: índice em `(product_id, status)` e cache do saldo total.
3. **Concorrência de lotes:** Duas saídas simultâneas podem tentar consumir o mesmo lote. Mitigação: `SELECT FOR UPDATE` nos lotes, seguindo ADR-001.
4. **Impacto no M5:** A lógica de reserva precisa continuar funcionando com lotes. Mitigação: a reserva opera no saldo total, não nos lotes individuais.

---

# 13. Critérios de Aceitação

Os critérios de aceitação detalhados estão em `acceptance-criteria.md`.

Resumo:

* AC-M7-001 a AC-M7-015: criação, consulta e consumo de lotes;
* AC-M7-016 a AC-M7-020: migração e rastreabilidade;
* AC-M7-021 a AC-M7-025: concorrência e imutabilidade.

---

# 14. Documentação a Atualizar

* `docs/domain/business-contract.md`: adicionar regras LOT-001 a LOT-010;
* `docs/product/roadmap.md`: atualizar status do M7;
* `docs/milestones/phase-2.md`: atualizar estado do M7;
* `docs/design/design-system.md`: se aplicável, padrões visuais para lotes.

---

*Fim da especificação do M7.*
