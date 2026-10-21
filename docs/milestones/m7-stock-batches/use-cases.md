# M7 — Casos de Uso

**Versão do documento:** 0.1 (RASCUNHO)
**Marco:** M7 — Lotes de Estoque
**Fase:** 2 — Evolução do Estoque e dos Clientes

---

## UC-M7-001 — Registrar compra e visualizar lotes gerados

**Atores:** Operador
**Pré-condição:** Produto cadastrado e ativo; M6 (Compras) implementado.

**Fluxo principal:**
1. O operador registra uma compra com um ou mais itens.
2. O sistema gera as movimentações ENTRY e os lotes correspondentes.
3. O operador consulta o produto no modal de estoque.
4. O sistema exibe os lotes ativos com quantidade, custo e data de entrada.

**Fluxos alternativos:**
- A. Item com preço zero: o lote é criado com `unit_cost = 0,00`.
- B. Produto inativo: a compra é rejeitada (PUR-006).

**Critérios relacionados:** AC-M7-001, AC-M7-003, AC-M7-004, AC-M7-005, AC-M7-023

---

## UC-M7-002 — Registrar entrada manual e visualizar lote

**Atores:** Operador
**Pré-condição:** Produto cadastrado e ativo.

**Fluxo principal:**
1. O operador abre o modal de estoque e seleciona um produto.
2. Preenche a quantidade e o custo unitário (opcional) da entrada.
3. Clica em "Registrar entrada".
4. O sistema cria a movimentação ENTRY e o lote correspondente.
5. O lote aparece na lista de lotes ativos do produto.

**Fluxos alternativos:**
- A. Custo unitário não informado: o lote é criado com `unit_cost = NULL`.
- B. Produto inativo: a entrada é rejeitada.

**Critérios relacionados:** AC-M7-002, AC-M7-005, AC-M7-023

---

## UC-M7-003 — Consultar lotes de um produto

**Atores:** Operador
**Pré-condição:** Produto com lotes existentes.

**Fluxo principal:**
1. O operador abre o modal de estoque e seleciona um produto.
2. O sistema exibe:
   - Saldo total (soma dos lotes ativos).
   - Lista de lotes ativos com: data de entrada, quantidade original, quantidade restante, custo unitário e origem (compra ou manual).
3. O operador pode expandir o histórico para ver lotes exauridos.

**Critérios relacionados:** AC-M7-005, AC-M7-006, AC-M7-007, AC-M7-023

---

## UC-M7-004 — Baixa de estoque por venda (FIFO)

**Atores:** Sistema (automático)
**Pré-condição:** Venda confirmada com cestas; produto com múltiplos lotes.

**Fluxo principal:**
1. A venda inicia a preparação e dispara a baixa física.
2. O sistema identifica os produtos e quantidades necessárias.
3. Para cada produto, consome os lotes em ordem FIFO (mais antigo primeiro).
4. Se um lote não tiver quantidade suficiente, continua no próximo lote.
5. Lotes esgotados mudam para status EXHAUSTED.
6. Movimentações OUTPUT são registradas com `batch_id` dos lotes consumidos.

**Fluxos alternativos:**
- A. Estoque insuficiente: a baixa é rejeitada (INV-006).
- B. Lote único suficiente: apenas um lote é consumido.

**Critérios relacionados:** AC-M7-008, AC-M7-009, AC-M7-010, AC-M7-011, AC-M7-016

---

## UC-M7-005 — Rastrear lote até a compra de origem

**Atores:** Operador
**Pré-condição:** Lote criado a partir de compra.

**Fluxo principal:**
1. O operador consulta o detalhe de um lote.
2. O sistema exibe a compra de origem: data da compra, item de compra, produto, quantidade comercial e preço pago.
3. O operador pode navegar para o detalhe da compra.

**Critérios relacionados:** AC-M7-015

---

## UC-M7-006 — Ajuste de estoque com lotes

**Atores:** Operador
**Pré-condição:** Produto com lotes ativos.

**Fluxo principal:**
1. O operador registra um ajuste de estoque (ADJUSTMENT).
2. O ajuste cria uma movimentação separada, não altera os lotes existentes.
3. Se o ajuste for positivo, um novo lote é criado.
4. Se o ajuste for negativo, os lotes são consumidos em ordem FIFO.

**Critérios relacionados:** AC-M7-014

---

*Total: 6 casos de uso.*
