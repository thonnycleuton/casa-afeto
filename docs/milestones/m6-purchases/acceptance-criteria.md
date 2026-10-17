# M6 — Critérios de Aceitação

**Versão do documento:** 0.1 (Rascunho)
**Status:** Rascunho — pendente de aprovação final
**Marco:** M6 — Compras e Reposição de Estoque
**Data:** 17 de outubro de 2026

---

## Criação de Compras

### AC-M6-001 — Criação de compra com um item

**Dado** um produto ativo com `base_unit = UN`
**Quando** o operador registra uma compra com 1 item:
- produto: Chocolate
- unidade comercial: "caixa"
- fator de conversão: 24
- quantidade comercial: 2
- preço por unidade comercial: 48.00
**Então** a compra é registrada com sucesso
**E** é criada uma ENTRY com `quantity = 48`, `unit_cost = 2.00`
**E** o saldo do produto aumenta em 48 UN

**Regra:** PUR-001, PUR-002, PUR-004
**Cobertura de testes:** Não implementada

---

### AC-M6-002 — Criação de compra com múltiplos itens

**Dado** produtos ativos Chocolate (UN) e Suco (L)
**Quando** o operador registra uma compra com 2 itens:
- Item 1: Chocolate, "caixa", fator 24, qty 2, preço 48.00
- Item 2: Suco, "fardo", fator 12, qty 1, preço 36.00
**Então** a compra é registrada com sucesso
**E** são criadas 2 ENTRY:
- Chocolate: `quantity = 48`, `unit_cost = 2.00`
- Suco: `quantity = 12`, `unit_cost = 3.00`

**Regra:** PUR-001, PUR-002, PUR-004
**Cobertura de testes:** Não implementada

---

### AC-M6-003 — Rejeição de compra com produto inativo

**Dado** um produto inativo
**Quando** o operador tenta registrar uma compra contendo esse produto
**Então** a compra não é registrada
**E** nenhuma ENTRY é criada
**E** o erro indica que o produto está inativo

**Regra:** PUR-006, INV-008
**Cobertura de testes:** Não implementada

---

### AC-M6-004 — Rejeição de conversão fracionária em UN

**Dado** um produto ativo com `base_unit = UN`
**Quando** o operador registra uma compra com:
- fator de conversão: 2.5
- quantidade comercial: 1
**Então** a compra não é registrada
**E** nenhuma ENTRY é criada
**E** o erro indica que a conversão resultou em quantidade fracionária

**Regra:** PUR-005
**Cobertura de testes:** Não implementada

---

### AC-M6-005 — Preço zero aceito

**Dado** um produto ativo
**Quando** o operador registra uma compra com `commercial_unit_price = 0.00`
**Então** a compra é registrada com sucesso
**E** a ENTRY é criada com `unit_cost = 0.00`

**Regra:** PUR-003, PUR-004
**Cobertura de testes:** Não implementada

---

### AC-M6-006 — Preço negativo rejeitado

**Dado** um produto ativo
**Quando** o operador tenta registrar uma compra com `commercial_unit_price < 0`
**Então** a compra não é registrada
**E** o erro indica que o preço deve ser não negativo

**Regra:** PUR-003
**Cobertura de testes:** Não implementada

---

### AC-M6-007 — Fator de conversão zero rejeitado

**Quando** o operador tenta registrar uma compra com `conversion_factor = 0`
**Então** a compra não é registrada
**E** o erro indica que o fator deve ser maior que zero

**Regra:** PUR-002
**Cobertura de testes:** Não implementada

---

### AC-M6-008 — Atomicidade: falha em um item invalida toda a compra

#### 8a — Falha na validação de entrada

**Dado** produtos A (ativo) e B (inativo)
**Quando** o operador registra uma compra com itens de A e B
**Então** a compra não é registrada
**E** nenhuma ENTRY é criada para nenhum produto
**E** o estoque de A não é alterado

**Regra:** PUR-011
**Cobertura de testes:** Não implementada

#### 8b — Falha durante a persistência transacional

**Dado** uma compra com 2 itens válidos de produtos ativos
**Quando** a criação da primeira ENTRY ocorre com sucesso, mas a criação da segunda ENTRY falha (ex: violação de constraint de banco)
**Então** toda a transação é revertida
**E** a compra não é persistida
**E** a primeira ENTRY é revertida e não permanece no banco
**E** nenhum registro parcial da operação é deixado no banco

**Regra:** PUR-011
**Cobertura de testes:** Não implementada

---

### AC-M6-009 — Custo médio ponderado atualizado

**Dado** um produto com ENTRY anterior: qty 100, unit_cost 2.00
**Quando** o operador registra uma compra: qty_base 50, unit_cost 3.00
**Então** o custo médio ponderado do produto é recalculado
**E** o custo médio é `(100 × 2.00 + 50 × 3.00) / (100 + 50) = 2.33`

**Regra:** PUR-004, Custo médio ponderado (business-contract.md §19.2)
**Cobertura de testes:** Não implementada

---

### AC-M6-010 — `reference_price` não alterado pela compra

**Dado** um produto com `reference_price = 5.00`
**Quando** o operador registra uma compra com `unit_cost = 2.00`
**Então** o `reference_price` do produto permanece `5.00`

**Regra:** PUR-007
**Cobertura de testes:** Não implementada

---

### AC-M6-011 — Consulta de compras por período

**Dado** compras registradas em diferentes datas
**Quando** o operador filtra por `purchased_at` entre duas datas
**Então** apenas as compras dentro do período são retornadas

**Regra:** PUR-010
**Cobertura de testes:** Não implementada

---

### AC-M6-012 — Consulta de compra individual com itens

**Dado** uma compra registrada com 3 itens
**Quando** o operador consulta a compra pelo ID
**Então** a compra é retornada com todos os 3 itens e seus detalhes

**Regra:** PUR-010
**Cobertura de testes:** Não implementada

---

### AC-M6-013 — Compra sem itens rejeitada

**Quando** o operador tenta registrar uma compra sem itens
**Então** a compra não é registrada
**E** o erro indica que a compra deve conter pelo menos um item

**Regra:** Validação de entrada
**Cobertura de testes:** Não implementada

---

### AC-M6-014 — Concorrência: ENTRY de compra respeita lock de produto

**Dado** duas requisições concorrentes de compra do mesmo produto
**Quando** ambas tentam criar ENTRY simultaneamente
**Então** as operações são serializadas pelo lock do produto
**E** o saldo final reflete corretamente ambas as entradas
**E** nenhuma ENTRY é perdida ou duplicada

**Regra:** PUR-012, ADR-001
**Cobertura de testes:** Não implementada

---

### AC-M6-015 — Unidade comercial opcional

**Dado** um produto ativo com `base_unit = UN`
**Quando** o operador registra uma compra sem informar `commercial_unit`:
- fator de conversão: 1
- quantidade comercial: 10
- preço: 2.00
**Então** a compra é registrada com sucesso
**E** a ENTRY é criada com `quantity = 10`, `unit_cost = 2.00`

**Regra:** PUR-002, Decisão 12.4
**Cobertura de testes:** Não implementada

---

### AC-M6-016 — `purchased_at` padrão

**Quando** o operador registra uma compra sem informar `purchased_at`
**Então** a compra é registrada com `purchased_at` igual à data/hora atual do servidor

**Regra:** Fluxo 7.1
**Cobertura de testes:** Não implementada

---

### AC-M6-017 — Conversão com KG

**Dado** um produto ativo com `base_unit = KG`
**Quando** o operador registra uma compra com:
- unidade comercial: "saco"
- fator de conversão: 5
- quantidade comercial: 3
- preço: 25.00
**Então** a compra é registrada com sucesso
**E** a ENTRY é criada com `quantity = 15.0`, `unit_cost = 5.00`

**Regra:** PUR-002, PUR-004
**Cobertura de testes:** Não implementada

---

### AC-M6-018 — Compras não podem ser excluídas

**Dado** uma compra registrada com ENTRY geradas
**Quando** o operador tenta excluir a compra
**Então** a exclusão é rejeitada
**E** a compra e suas ENTRY permanecem intactas
**E** as ENTRY geradas pela compra não podem ser excluídas individualmente

**Regra:** PUR-008
**Cobertura de testes:** Não implementada

---

### AC-M6-019 — Correção por compra complementar

**Dado** um produto ativo com `base_unit = UN` e estoque inicial zero:
- Uma compra original registrada com erro:
  - Item: unidade comercial "caixa", fator de conversão 24, quantidade comercial 2, preço 48.00
  - ENTRY gerada: `quantity = 48`, `unit_cost = 2.00`
  - Saldo após a compra original: 48 unidades
**Quando** o operador registra uma compra corretiva com os valores corretos:
- Item: unidade comercial "caixa", fator de conversão 24, quantidade comercial 3, preço 48.00
- ENTRY gerada: `quantity = 72`, `unit_cost = 2.00`
**Então** a compra corretiva é registrada com sucesso
**E** a compra original permanece inalterada com sua ENTRY (`quantity = 48`)
**E** o estoque reflete ambas as ENTRY (saldo: 120 unidades)
**E** se permitido pelas regras INV-002, INV-006 e pelas reservas ativas, um ajuste manual de −48 UN resulta em saldo de 72 unidades
**E** o custo médio ponderado considera as ENTRY da compra original e da compra corretiva, sem apagar o histórico
**E** neste exemplo, ambas as ENTRY têm custo unitário de R$ 2,00/UN, portanto o custo médio permanece em R$ 2,00/UN

**Regra:** PUR-009, Decisão 12.1
**Cobertura de testes:** Não implementada

---

### AC-M6-020 — Rastreabilidade de ENTRY para compra via `purchase_id`

**Dado** uma compra registrada com 2 itens
**Quando** o operador consulta o histórico de movimentações de um dos produtos
**Então** as ENTRY geradas pela compra mostram `purchase_id` populado
**E** é possível identificar a compra de origem de cada ENTRY
**E** as ENTRY manuais (M1) mostram `purchase_id = NULL`

**Regra:** PUR-011, Decisão 12.2
**Cobertura de testes:** Não implementada

---

### AC-M6-021 — Itens do mesmo produto geram ENTRY separadas

**Dado** um produto ativo com `base_unit = UN`
**Quando** o operador registra uma compra com 2 itens do mesmo produto:
- Item 1: "caixa", fator 24, qty 1, preço 48.00
- Item 2: "caixa", fator 24, qty 1, preço 54.00
**Então** a compra é registrada com sucesso
**E** são criadas 2 ENTRY separadas:
- ENTRY 1: `quantity = 24`, `unit_cost = 2.00`
- ENTRY 2: `quantity = 24`, `unit_cost = 2.25`
**E** ambas as ENTRY referenciam a mesma compra via `purchase_id`

**Regra:** PUR-012, Decisão 12.3
**Cobertura de testes:** Não implementada

---

## Test Coverage Matrix

| AC ID | Test Name | File | Line | Status |
|-------|-----------|------|------|--------|
| AC-M6-001 | test_create_purchase_single_item | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-002 | test_create_purchase_multiple_items | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-003 | test_reject_purchase_inactive_product | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-004 | test_reject_fractional_conversion_un | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-005 | test_accept_zero_price | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-006 | test_reject_negative_price | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-007 | test_reject_zero_conversion_factor | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-008a | test_atomicity_validation_failure | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-008b | test_atomicity_transaction_failure | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-009 | test_weighted_average_cost_updated | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-010 | test_reference_price_unchanged | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-011 | test_list_purchases_by_period | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-012 | test_get_purchase_with_items | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-013 | test_reject_empty_purchase | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-014 | test_concurrent_purchase_lock | tests/test_m6_concurrency.py | — | ✗ |
| AC-M6-015 | test_optional_commercial_unit | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-016 | test_default_purchased_at | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-017 | test_conversion_with_kg | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-018 | test_cannot_delete_purchase | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-019 | test_correction_by_complementary_purchase | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-020 | test_entry_traceability_purchase_id | tests/test_m6_purchases.py | — | ✗ |
| AC-M6-021 | test_same_product_separate_entries | tests/test_m6_purchases.py | — | ✗ |

---

*Fim dos critérios de aceitação do M6.*
