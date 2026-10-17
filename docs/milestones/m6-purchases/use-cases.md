# M6 — Casos de Uso de Compras e Reposição de Estoque

**Versão do documento:** 0.1 (Rascunho)
**Status:** Rascunho — pendente de aprovação final
**Marco:** M6 — Compras e Reposição de Estoque
**Data:** 17 de outubro de 2026

---

## UC-M6-001 — Registrar compra recebida

**Objetivo:** Registrar uma compra de produtos recebida fisicamente pela Casa Afeto, gerando automaticamente as movimentações de estoque correspondentes.

**Pré-condições:**
- Produtos referenciados existem e estão ativos.

**Fluxo principal:**
1. O operador inicia a criação de uma compra.
2. O operador informa a data de aquisição (opcional; padrão: data/hora atual).
3. O operador adiciona um ou mais itens:
   - Seleciona um produto ativo.
   - Informa a unidade comercial (opcional).
   - Informa o fator de conversão para a unidade-base (obrigatório, > 0).
   - Informa a quantidade na unidade comercial (obrigatório, > 0).
   - Informa o preço de aquisição por unidade comercial (obrigatório, ≥ 0).
4. O sistema valida cada item:
   - Produto existe e está ativo (PUR-006).
   - Fator de conversão > 0 (PUR-002).
   - Quantidade comercial > 0 (PUR-002).
   - Preço ≥ 0 (PUR-003).
   - Calcula `quantidade_base = quantidade_comercial × fator_de_conversão`.
   - Verifica que `quantidade_base` respeita as regras de UN inteiro / decimal (PUR-005).
5. O sistema inicia uma transação atômica (PUR-011):
   - Persiste a Compra com `purchased_at`.
   - Para cada item, em ordem:
     - Adquire lock do produto (`SELECT FOR UPDATE`) — PUR-012.
     - Calcula `unit_cost = commercial_unit_price / fator_de_conversão` (PUR-004).
     - Cria `InventoryMovement` do tipo ENTRY com `quantity`, `unit_cost` e `purchase_id`.
     - Cria o `PurchaseItem`.
6. O sistema confirma a transação e retorna a compra com itens e ENTRY geradas.

**Fluxos alternativos:**
- 3a. Produto inativo: o sistema rejeita a compra e informa que o produto está inativo (PUR-006).
- 3b. Conversão fracionária em UN: a conversão resulta em quantidade não inteira para produto com `base_unit = UN`. O sistema rejeita e informa o produto e a quantidade calculada (PUR-005).
- 3c. Preço negativo: o sistema rejeita e informa que o preço deve ser não negativo (PUR-003).
- 3d. Fator de conversão zero ou negativo: o sistema rejeita e informa que o fator deve ser maior que zero (PUR-002).
- 3e. Compra sem itens: o sistema rejeita e informa que a compra deve conter pelo menos um item.
- 5a. Falha em qualquer item: a transação é revertida integralmente. Nem a compra nem nenhuma ENTRY são persistidas (PUR-011).

**Pós-condições:**
- Compra registrada com `purchased_at`.
- Itens de compra persistidos.
- ENTRY criadas para cada item, vinculadas à compra via `purchase_id`.
- Estoque atualizado com as novas entradas.
- Custo médio ponderado recalculado.

**Regras aplicáveis:** PUR-001, PUR-002, PUR-003, PUR-004, PUR-005, PUR-006, PUR-011, PUR-012

---

## UC-M6-002 — Consultar compras por período

**Objetivo:** Listar as compras registradas, opcionalmente filtradas por período de aquisição.

**Pré-condições:**
- Compras registradas no sistema.

**Fluxo principal:**
1. O operador solicita a lista de compras.
2. O operador informa, opcionalmente, data inicial e data final de filtro.
3. O sistema retorna as compras dentro do período (ou todas, sem filtro).
4. O sistema ordena por `purchased_at` descendente (mais recente primeiro).
5. Cada compra inclui os itens com produto, unidade comercial, quantidade e preço.

**Pós-condições:**
- Lista de compras exibida ao operador.

**Regras aplicáveis:** PUR-010

---

## UC-M6-003 — Consultar detalhes de uma compra

**Objetivo:** Exibir os detalhes completos de uma compra específica, incluindo todos os itens e valores calculados.

**Pré-condições:**
- Compra registrada no sistema.

**Fluxo principal:**
1. O operador solicita os detalhes de uma compra pelo ID.
2. O sistema retorna a compra com:
   - `id`, `purchased_at`, `created_at`.
   - Lista de itens com:
     - Produto (ID, nome, unidade-base).
     - Unidade comercial.
     - Fator de conversão.
     - Quantidade comercial.
     - Preço por unidade comercial.
     - Quantidade calculada em unidade-base.
     - Custo unitário calculado (`unit_cost` da ENTRY).

**Fluxos alternativos:**
- 1a. Compra não encontrada: o sistema retorna erro 404.

**Pós-condições:**
- Detalhes da compra exibidos ao operador.

**Regras aplicáveis:** PUR-010

---

## UC-M6-004 — Corrigir compra por compra complementar

**Objetivo:** Corrigir uma compra registrada com erro sem alterar o histórico original.

**Pré-condições:**
- Compra original já registrada com ENTRY geradas.
- O operador identificou um erro na compra original.

**Fluxo principal:**
1. O operador registra uma nova compra com os valores corretos (UC-M6-001).
2. O sistema processa a compra corretiva normalmente, gerando ENTRY novas.
3. A compra original permanece inalterada.
4. Se necessário ajustar o estoque para compensar a compra errada, o operador usa separadamente o fluxo de ajuste de estoque (ADJUSTMENT), respeitando INV-002 e INV-006.

**Fluxos alternativos:**
- 2a. Estoque da compra errada já reservado: se o ajuste negativo for rejeitado pelo sistema para proteger reservas ativas, o operador registra apenas a compra correta e usa ajuste quando o saldo permitir.

**Pós-condições:**
- Compra corretiva registrada com ENTRY novas.
- Compra original preservada no histórico.
- Estoque reflete ambas as compras (e eventuais ajustes).

**Regras aplicáveis:** PUR-008, PUR-009

---

## UC-M6-005 — Registrar compra com unidade comercial diferente

**Objetivo:** Registrar uma compra onde a unidade de aquisição difere da unidade-base de estoque do produto.

**Pré-condições:**
- Produto ativo com unidade-base definida (ex: UN, KG, L, ML, G).

**Fluxo principal:**
1. O operador inicia a criação de uma compra (UC-M6-001).
2. Para um item, o operador informa:
   - Unidade comercial: "caixa".
   - Fator de conversão: 24 (1 caixa = 24 unidades-base).
   - Quantidade comercial: 2 caixas.
   - Preço por unidade comercial: R$ 48,00 por caixa.
3. O sistema calcula:
   - `quantidade_base = 2 × 24 = 48 UN`.
   - `unit_cost = 48.00 / 24 = 2.00 por UN`.
4. O sistema cria a ENTRY com `quantity = 48`, `unit_cost = 2.00`.

**Pós-condições:**
- Compra registrada com conversão aplicada.
- ENTRY com quantidade e custo em unidade-base.

**Regras aplicáveis:** PUR-002, PUR-004

---

## UC-M6-006 — Registrar compra com preço zero (doação)

**Objetivo:** Registrar uma compra de itens obtidos sem custo (doação, brinde).

**Pré-condições:**
- Produto ativo.

**Fluxo principal:**
1. O operador registra uma compra com `commercial_unit_price = 0.00`.
2. O sistema aceita o preço zero.
3. O sistema calcula `unit_cost = 0.00 / fator_de_conversão = 0.00`.
4. O sistema cria a ENTRY com `unit_cost = 0.00`.
5. O custo médio ponderado é recalculado, incluindo a ENTRY com custo zero.

**Pós-condições:**
- Compra registrada com custo zero.
- ENTRY com `unit_cost = 0.00` participa do custo médio ponderado.

**Regras aplicáveis:** PUR-003, PUR-004

---

*Fim dos casos de uso do M6.*
