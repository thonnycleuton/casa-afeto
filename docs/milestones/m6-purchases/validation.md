# M6 — Plano de Validação

**Versão do documento:** 0.1 (Rascunho)
**Status:** Rascunho — pendente de aprovação final
**Marco:** M6 — Compras e Reposição de Estoque
**Data:** 17 de outubro de 2026

---

## 1. Objetivo da validação

Validar que a implementação do M6 satisfaz as regras de negócio aprovadas (PUR-001 a PUR-012) e os critérios de aceitação definidos em `acceptance-criteria.md`.

Esta validação cobre:

- Registro de compras com unidade comercial e fator de conversão.
- Cálculo de custo por unidade-base.
- Geração atômica de ENTRY vinculadas à compra.
- Validação de produto ativo, quantidade fracionária em UN, preço negativo.
- Atomicidade transacional: falha em um item invalida toda a compra.
- Atualização do custo médio ponderado.
- `reference_price` não alterado pela compra.
- Consulta de compras por período e detalhes.
- Concorrência: lock de produto ao gerar ENTRY.
- Rastreabilidade de ENTRY para compra via `purchase_id`.
- Itens do mesmo produto geram ENTRY separadas.
- Correção por compra complementar.
- Compras não podem ser excluídas.

---

## 2. Preparação do ambiente

1. Garantir que o banco de dados está populado com os dados de M1–M5.
2. Executar as migrations do M6:
   - Criar tabela `purchases`.
   - Criar tabela `purchase_items`.
   - Adicionar coluna `purchase_id` em `inventory_movements` (nullable, FK com SET NULL).
3. Verificar que as tabelas e colunas foram criadas corretamente.
4. Verificar que `inventory/service.py:create_movement()` aceita o parâmetro `purchase_id`.

---

## 3. Validação funcional do domínio

### 3.1 Criação de compra com um item (AC-M6-001)

**Cenário positivo:**
1. Criar um produto ativo com `base_unit = UN` (ex: Chocolate).
2. Registrar uma compra com 1 item:
   - Unidade comercial: "caixa", fator: 24, qty: 2, preço: 48.00.
3. Verificar que a compra foi registrada.
4. Verificar que foi criada 1 ENTRY com `quantity = 48`, `unit_cost = 2.00`.
5. Verificar que o saldo do produto aumentou em 48 UN.
6. Verificar que `purchase_id` na ENTRY aponta para a compra.

### 3.2 Criação de compra com múltiplos itens (AC-M6-002)

1. Registrar uma compra com 2 itens de produtos diferentes:
   - Item 1: Chocolate (UN), "caixa", fator 24, qty 2, preço 48.00.
   - Item 2: Suco (L), "fardo", fator 12, qty 1, preço 36.00.
2. Verificar que foram criadas 2 ENTRY:
   - Chocolate: `quantity = 48`, `unit_cost = 2.00`.
   - Suco: `quantity = 12`, `unit_cost = 3.00`.

### 3.3 Rejeição de produto inativo (AC-M6-003)

1. Criar um produto inativo.
2. Tentar registrar uma compra contendo esse produto.
3. Verificar que a compra não é registrada.
4. Verificar que nenhuma ENTRY é criada.
5. Verificar que o erro indica produto inativo.

### 3.4 Rejeição de conversão fracionária em UN (AC-M6-004)

1. Registrar uma compra com produto UN, fator 2.5, qty 1.
2. Verificar que a compra é rejeitada.
3. Verificar que o erro indica quantidade fracionária.

### 3.5 Preço zero aceito (AC-M6-005)

1. Registrar uma compra com `commercial_unit_price = 0.00`.
2. Verificar que a compra é registrada.
3. Verificar que a ENTRY tem `unit_cost = 0.00`.

### 3.6 Preço negativo rejeitado (AC-M6-006)

1. Tentar registrar uma compra com `commercial_unit_price < 0`.
2. Verificar que a compra é rejeitada.

### 3.7 Fator de conversão zero rejeitado (AC-M6-007)

1. Tentar registrar uma compra com `conversion_factor = 0`.
2. Verificar que a compra é rejeitada.

### 3.8 Atomicidade — falha em um item (AC-M6-008)

**Cenário 8a — Falha na validação:**
1. Registrar uma compra com itens de produto ativo e produto inativo.
2. Verificar que a compra não é registrada.
3. Verificar que nenhuma ENTRY é criada para nenhum produto.
4. Verificar que o estoque do produto ativo não é alterado.

**Cenário 8b — Falha transacional:**
1. Simular falha na segunda ENTRY de uma compra com 2 itens válidos.
2. Verificar que toda a transação é revertida.
3. Verificar que nem a compra nem a primeira ENTRY permanecem no banco.

### 3.9 Custo médio ponderado (AC-M6-009)

1. Criar produto com ENTRY anterior: qty 100, unit_cost 2.00.
2. Registrar compra: qty_base 50, unit_cost 3.00.
3. Verificar que o custo médio é `(100 × 2.00 + 50 × 3.00) / (100 + 50) = 2.33`.

### 3.10 `reference_price` não alterado (AC-M6-010)

1. Criar produto com `reference_price = 5.00`.
2. Registrar compra com `unit_cost = 2.00`.
3. Verificar que `reference_price` permanece `5.00`.

### 3.11 Consulta de compras por período (AC-M6-011)

1. Registrar compras em datas diferentes.
2. Filtrar por período.
3. Verificar que apenas as compras dentro do período são retornadas.
4. Verificar ordenação descendente por `purchased_at`.

### 3.12 Consulta de compra individual (AC-M6-012)

1. Registrar compra com 3 itens.
2. Consultar pelo ID.
3. Verificar que todos os 3 itens e detalhes são retornados.

### 3.13 Compra sem itens rejeitada (AC-M6-013)

1. Tentar registrar compra sem itens.
2. Verificar que é rejeitada com mensagem adequada.

### 3.14 Concorrência (AC-M6-014)

1. Executar duas requisições concorrentes de compra do mesmo produto.
2. Verificar que as operações são serializadas pelo lock.
3. Verificar que o saldo final reflete corretamente ambas as entradas.
4. Verificar que nenhuma ENTRY é perdida ou duplicada.

### 3.15 Unidade comercial opcional (AC-M6-015)

1. Registrar compra sem `commercial_unit`, fator 1, qty 10, preço 2.00.
2. Verificar que a compra é registrada.
3. Verificar que a ENTRY tem `quantity = 10`, `unit_cost = 2.00`.

### 3.16 `purchased_at` padrão (AC-M6-016)

1. Registrar compra sem informar `purchased_at`.
2. Verificar que `purchased_at` é igual à data/hora atual do servidor.

### 3.17 Conversão com KG (AC-M6-017)

1. Registrar compra com produto KG, "saco", fator 5, qty 3, preço 25.00.
2. Verificar que a ENTRY tem `quantity = 15.0`, `unit_cost = 5.00`.

### 3.18 Compras não podem ser excluídas (AC-M6-018)

1. Registrar compra com ENTRY.
2. Tentar excluir a compra via API.
3. Verificar que a exclusão é rejeitada.
4. Verificar que a compra e ENTRY permanecem.

### 3.19 Correção por compra complementar (AC-M6-019)

1. Registrar compra original com erro (qty 48, unit_cost 2.00).
2. Registrar compra corretiva (qty 72, unit_cost 2.00).
3. Verificar que a compra original permanece inalterada.
4. Verificar que o saldo reflete ambas as ENTRY (120 unidades).
5. Verificar que o custo médio considera ambas as ENTRY.

### 3.20 Rastreabilidade via `purchase_id` (AC-M6-020)

1. Registrar compra com 2 itens.
2. Consultar histórico de movimentações do produto.
3. Verificar que as ENTRY da compra têm `purchase_id` populado.
4. Verificar que ENTRY manuais (M1) têm `purchase_id = NULL`.

### 3.21 Itens do mesmo produto — ENTRY separadas (AC-M6-021)

1. Registrar compra com 2 itens do mesmo produto, preços diferentes.
2. Verificar que são criadas 2 ENTRY separadas com custos diferentes.
3. Verificar que ambas referenciam a mesma compra via `purchase_id`.

---

## 4. Validação técnica

### 4.1 Migrações de banco de dados

- [ ] Tabela `purchases` criada com colunas corretas.
- [ ] Tabela `purchase_items` criada com FK para `purchases` e `products`.
- [ ] Coluna `purchase_id` em `inventory_movements` (nullable, FK com SET NULL).
- [ ] Constraints RESTRICT em FK de `purchase_items`.

### 4.2 API

- [ ] POST `/api/v1/purchases` — criar compra.
- [ ] GET `/api/v1/purchases` — listar com filtros.
- [ ] GET `/api/v1/purchases/{id}` — detalhes.
- [ ] DELETE `/api/v1/purchases/{id}` — rejeitado (PUR-008).

### 4.3 Integração com estoque

- [ ] `create_movement()` aceita `purchase_id`.
- [ ] ENTRY geradas por compra têm `type = ENTRY`, `sale_id = NULL`, `purchase_id` populado.
- [ ] `unit_cost` sempre populado (nunca NULL) em ENTRY de compra.

### 4.4 Concorrência

- [ ] `SELECT FOR UPDATE` no produto antes de gerar ENTRY.
- [ ] Locks em ordem crescente de `product_id` para compras com múltiplos produtos.
- [ ] Sem deadlocks entre compras concorrentes.

### 4.5 Precisão decimal

- [ ] Cálculos usam `Decimal` / `NUMERIC`.
- [ ] `unit_cost` arredondado para 2 casas decimais.
- [ ] `quantidade_base` sem arredondamento intermediário.

---

## 5. Critérios de conclusão

O M6 é considerado validado quando:

- [ ] Todos os 21 critérios de aceitação passam na validação manual.
- [ ] Todos os testes automatizados passam.
- [ ] O discrimination sensor detecta 100% das mutações injetadas.
- [ ] As migrações são reversíveis.
- [ ] A API retorna os códigos HTTP corretos (201, 404, 409, 422).
- [ ] Nenhuma regra de negócio preservada (INV-*, RES-*, PROD-*) foi violada.

---

*Fim do plano de validação do M6.*
