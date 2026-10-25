# M8 — Gestão de Vencimentos

**Versão:** 0.2 (Aprovado)
**Status:** Aprovado — implementação concluída
**Milestone:** M8 — Fase 2
**Dependência:** M7 — Lotes de Estoque (COMPLETED)

---

## 1. Objetivo

Introduzir data de vencimento nos lotes de estoque, permitindo que a Casa Afeto rastreie quando cada grupo de unidades adquiridas vence. O consumo de estoque passa a usar a política FEFO (First Expired, First Out) como padrão, substituindo o FIFO do M7.

O sistema alerta sobre lotes próximos do vencimento e lotes já vencidos, tanto no modal de estoque por produto quanto em uma lista global de vencimentos.

---

## 2. Regras de Negócio

### EXP-001 — Vencimento opcional por lote

Cada lote de estoque pode ter uma data de vencimento (`expiry_date`). Este campo é **opcional**:

- Produtos perecíveis (ex: bolos, sucos, tortas) têm vencimento informado.
- Produtos não perecíveis (ex: arroz, feijão, óleo) ficam com `expiry_date = NULL`.
- A decisão de informar vencimento é feita por **item de compra** ou **entrada manual**.

### EXP-002 — Vencimento herdado na criação do lote

Quando um lote é criado a partir de um item de compra ou entrada manual com `expiry_date`, o lote herda essa data. Se o item não informa vencimento, o lote é criado com `expiry_date = NULL`.

### EXP-003 — Vencimento imutável

A data de vencimento de um lote **não pode ser alterada** após a criação. Um lote com vencimento errado deve ser arquivado (EXHAUSTED) e um novo lote criado.

### EXP-004 — FEFO substitui FIFO

O consumo de estoque usa **FEFO (First Expired, First Out)** como política padrão:

1. Lotes com vencimento são consumidos primeiro, ordenados pelo vencimento mais próximo.
2. Lotes sem vencimento (`expiry_date = NULL`) são consumidos após os lotes com vencimento, ordenados por data de criação (FIFO como fallback).

Exemplo de ordem de consumo:
```
Lote A: vencimento 2026-11-01 → consumido primeiro
Lote B: vencimento 2026-11-15 → consumido segundo
Lote C: vencimento NULL, criado 2026-10-01 → consumido terceiro
Lote D: vencimento NULL, criado 2026-10-15 → consumido quarto
```

### EXP-005 — Lote vencido não é consumido automaticamente

Um lote com `expiry_date < hoje` **continua ativo** e **pode ser consumido** pelo FEFO. O sistema não bloqueia automaticamente o consumo de lotes vencidos — essa é uma decisão de negócio que pode ser introduzida no futuro.

O lote vencido é apenas **sinalizado** visualmente como vencido.

### EXP-006 — Alerta de vencimento próximo

Um lote é considerado "próximo do vencimento" quando:

```
expiry_date - hoje <= threshold_dias
```

O `threshold_dias` padrão é **7 dias**, configurável via variável de ambiente `EXPIRY_ALERT_DAYS`.

### EXP-007 — Alerta de lote vencido

Um lote é considerado "vencido" quando:

```
expiry_date < hoje
```

Lotes vencidos são destacados com urgência maior que lotes próximos do vencimento.

### EXP-008 — Lista global de vencimentos

O sistema expõe uma API para listar todos os lotes ativos com vencimento próximo ou vencido, independentemente do produto. Esta lista permite visibilidade operacional de todos os vencimentos do negócio.

### EXP-009 — Destaque visual no modal de estoque

O modal de estoque de cada produto destaca os lotes com vencimento próximo ou vencido usando badges visuais:

- **Vencido:** badge vermelho (`error`)
- **Próximo do vencimento:** badge amarelo (`warning`)
- **Sem vencimento:** sem badge

### EXP-010 — Vencimento na entrada manual

Ao registrar uma entrada manual de estoque, o operador pode informar a data de vencimento. Se não informada, o lote é criado com `expiry_date = NULL`.

---

## 3. Modelo de Dados

### Alterações em `stock_batches`

| Coluna | Tipo | Restrição | Descrição |
|--------|------|-----------|-----------|
| `expiry_date` | `DATE` | `NULLABLE` | Data de vencimento do lote. NULL para produtos sem vencimento. |

### Nova coluna em `purchase_items`

| Coluna | Tipo | Restrição | Descrição |
|--------|------|-----------|-----------|
| `expiry_date` | `DATE` | `NULLABLE` | Data de vencimento deste item de compra. Herdada pelo lote criado. |

### Diagrama de relacionamento

```
PurchaseItem
  └─ expiry_date (nullable)
       ↓ herda
StockBatch
  ├─ expiry_date (nullable)
  ├─ created_at
  └─ status (ACTIVE / EXHAUSTED)
```

---

## 4. API

### 4.1. Alterações nos endpoints existentes

#### `POST /purchases` — Criar compra

**Body atualizado:**

```json
{
  "purchased_at": "2026-10-20T10:00:00",
  "items": [
    {
      "product_id": 1,
      "commercial_unit": "CX",
      "conversion_factor": 12,
      "commercial_quantity": 2,
      "commercial_unit_price": 24.00,
      "expiry_date": "2026-11-15"
    }
  ]
}
```

O campo `expiry_date` em cada item é opcional. Se informado, o lote criado herda essa data.

#### `POST /inventory/movements` — Criar movimentação

**Body atualizado para ENTRY:**

```json
{
  "product_id": 1,
  "quantity": 10,
  "type": "ENTRY",
  "unit_cost": 8.00,
  "expiry_date": "2026-12-01"
}
```

O campo `expiry_date` é opcional. Se informado, o lote criado herda essa data.

#### `GET /products/{id}/batches` — Listar lotes

**Resposta atualizada:**

```json
[
  {
    "id": 1,
    "product_id": 1,
    "purchase_id": 5,
    "quantity_original": 120,
    "quantity_remaining": 95,
    "unit_cost": 8.00,
    "expiry_date": "2026-11-15",
    "status": "ACTIVE",
    "created_at": "2026-10-20T10:00:00"
  }
]
```

Cada lote inclui `expiry_date` (nullable) e um campo derivado `expiry_status`:

- `"OK"` — sem vencimento ou vencimento distante
- `"WARNING"` — vencimento próximo (≤ threshold)
- `"EXPIRED"` — vencido

### 4.2. Novo endpoint

#### `GET /inventory/expiry-alerts` — Lista global de vencimentos

**Query params:**

- `threshold_days` (int, optional): dias para alerta (default: 7)
- `include_expired` (bool, optional): incluir lotes já vencidos (default: true)

**Resposta:**

```json
[
  {
    "batch_id": 1,
    "product_id": 1,
    "product_name": "Bolo caseiro",
    "quantity_remaining": 95,
    "unit_cost": 8.00,
    "expiry_date": "2026-11-15",
    "expiry_status": "WARNING",
    "days_until_expiry": 12,
    "purchase_id": 5
  }
]
```

Ordenado por `expiry_date ASC` (mais urgente primeiro), depois por `created_at ASC`.

---

## 5. Impacto no Frontend

### 5.1. Modal de Estoque (InventoryModal)

A tabela de lotes ativos ganha duas colunas:

| Coluna | Conteúdo |
|--------|---------|
| **Vencimento** | Data formatada ou "—" se NULL |
| **Status** | Badge: OK (verde), WARNING (amarelo), EXPIRED (vermelho) |

### 5.2. Modal de Compra (PurchaseForm)

Cada item de compra ganha um campo opcional:

- **Data de vencimento** — input date, opcional

### 5.3. Entrada manual de estoque (InventoryModal)

O formulário de entrada manual ganha um campo opcional:

- **Data de vencimento** — input date, opcional

### 5.4. Lista global de vencimentos

Uma nova seção ou modal exibe os lotes com vencimento próximo ou vencido, consultando `GET /inventory/expiry-alerts`.

---

## 6. Migração de Dados

Lotes existentes (criados pelo M7) terão `expiry_date = NULL`. Não há migração de dados necessária — a coluna é nullable.

---

## 7. Decisões do Product Owner

| ID | Decisão | Impacto |
|----|---------|---------|
| D-1 | Vencimento opcional por item de compra | Cada item de compra pode ter vencimento diferente |
| D-2 | Ambas as abordagens de alerta | Lista global + destaque no modal de estoque |
| D-3 | FEFO substitui FIFO | Consumo automático pelo vencimento mais próximo |

---

## 8. Dependências

| Dependência | Status |
|-------------|--------|
| M7 — Lotes de Estoque | COMPLETED |
| M6 — Compras | COMPLETED |

---

## 9. Escopo

O M8 está estritamente limitado a:

- Adicionar `expiry_date` opcional aos lotes de estoque.
- Evoluir o consumo de FIFO para FEFO.
- Exibir alertas visuais de vencimento no modal de estoque.
- Expor API de lista global de vencimentos.
- Permitir informar vencimento na compra e na entrada manual.

## 10. Fora do Escopo

Os seguintes itens **não** fazem parte do M8:

- Bloqueio automático de consumo de lotes vencidos.
- Notificações por e-mail ou push sobre vencimentos.
- Cálculo automático de shelf life a partir de validade padrão do produto.
- Relatórios de perda por vencimento.
- Integração com sistemas externos de controle de qualidade.

## 11. Decisões Pendentes

Nenhuma decisão pendente — todas as decisões foram definidas pelo Product Owner.

## 12. Limitações Conhecidas

1. **Sem bloqueio de consumo de lotes vencidos:** O sistema sinaliza, mas não impede o uso de lotes vencidos. Isso pode ser introduzido como regra futura.
2. **Sem notificações automáticas:** Os alertas são visuais, por e-mail ou push. Isso pode ser introduzido como regra futura.
3. **Sem cálculo de shelf life:** O vencimento é informado manualmente, não calculado a partir de validade padrão do produto.

---

*Fim da especificação do M8.*
