# M7 — Critérios de Aceitação

**Versão do documento:** 0.3 (Tags adicionadas)
**Marco:** M7 — Lotes de Estoque
**Fase:** 2 — Evolução do Estoque e dos Clientes

---

## 1. Criação de Lotes

### AC-M7-001 [Backend] — Lote criado ao registrar compra

**Dado** um produto ativo com estoque zero
**Quando** uma compra com um item é registrada
**Então** um lote de estoque é criado automaticamente com:
* `product_id` igual ao produto do item;
* `quantity_original` igual à quantidade em unidade-base;
* `quantity_remaining` igual à quantidade em unidade-base;
* `unit_cost` calculado a partir do preço comercial e fator de conversão;
* `purchase_id` vinculado à compra;
* `status = 'ACTIVE'`.

### AC-M7-002 [Backend] — Lote criado por entrada manual

**Dado** um produto ativo
**Quando** uma entrada manual de estoque (ENTRY) é registrada
**Então** um lote de estoque é criado com:
* `purchase_id = NULL`;
* `quantity_original` igual à quantidade da entrada;
* `quantity_remaining` igual à quantidade da entrada;
* `unit_cost` igual ao valor informado (pode ser NULL);
* `status = 'ACTIVE'`.

### AC-M7-003 [Backend] — Múltiplos itens geram múltiplos lotes

**Dado** uma compra com 3 itens de produtos diferentes
**Quando** a compra é registrada
**Então** 3 lotes são criados, um por item, cada um vinculado ao respectivo produto.

### AC-M7-004 [Backend] — Lote preserva custo de aquisição

**Dado** uma compra com item a R$ 24,00 por caixa de 12 unidades
**Quando** o lote é criado
**Então** `unit_cost = 2,00` (24,00 / 12).

---

## 2. Consulta de Lotes

### AC-M7-005 [Backend] — Listar lotes ativos do produto

**Dado** um produto com 3 lotes ativos
**Quando** o usuário consulta os lotes do produto
**Então** os 3 lotes são retornados com `quantity_remaining`, `unit_cost`, `created_at` e origem.

### AC-M7-006 [Backend] — Estoque físico é soma dos lotes ativos

**Dado** um produto com lotes: Lote A (10 restantes), Lote B (5 restantes), Lote C (exaurido)
**Quando** o saldo do produto é consultado
**Então** o saldo físico é 15 (10 + 5), não incluindo o lote exaurido.

### AC-M7-007 [Backend] — Histórico inclui lotes exauridos

**Dado** um produto com 2 lotes ativos e 1 lote exaurido
**Quando** o histórico completo de lotes é consultado
**Então** todos os 3 lotes são retornados, com status correto.

---

## 3. Consumo FIFO

### AC-M7-008 [Backend] — Saída consome lote mais antigo

**Dado** um produto com Lote A (criado em 01/01, 10 unidades) e Lote B (criado em 15/01, 10 unidades)
**Quando** uma saída de 5 unidades é registrada
**Então** Lote A tem 5 restantes e Lote B permanece com 10.

### AC-M7-009 [Backend] — Saída consome múltiplos lotes

**Dado** um produto com Lote A (3 unidades) e Lote B (10 unidades)
**Quando** uma saída de 7 unidades é registrada
**Então** Lote A fica exaurido (0 restantes, status EXHAUSTED) e Lote B tem 6 restantes.

### AC-M7-010 [Backend] — Lote esgotado vira EXHAUSTED

**Dado** um lote com 5 unidades restantes
**Quando** uma saída de 5 unidades consome todo o lote
**Então** o lote muda para `status = 'EXHAUSTED'` e `quantity_remaining = 0`.

### AC-M7-011 [Backend] — Saída respeita estoque negativo

**Dado** um produto com saldo total de 5 unidades
**Quando** uma saída de 10 unidades é tentada
**Então** a saída é rejeitada (INV-006: estoque não pode ficar negativo).

---

## 4. Imutabilidade e Integridade

### AC-M7-012 [Backend] — Lote não é deletável

**Dado** um lote existente
**Quando** uma tentativa de exclusão é feita
**Então** o lote não é deletado. Não existe endpoint DELETE para lotes.

### AC-M7-013 [Backend] — unit_cost do lote é imutável

**Dado** um lote com `unit_cost = 2,00`
**Quando** uma tentativa de alteração do `unit_cost` é feita
**Então** o `unit_cost` permanece 2,00.

### AC-M7-014 [Backend] — Correção por ajuste de estoque

**Dado** um lote com quantidade incorreta
**Quando** um ajuste de estoque (ADJUSTMENT) é registrado
**Então** o ajuste cria uma movimentação separada, não altera o lote original.

---

## 5. Rastreabilidade

### AC-M7-015 [Backend] — Lote rastreável até a compra

**Dado** um lote criado a partir de compra
**Quando** o detalhe do lote é consultado
**Então** `purchase_id` e `purchase_item_id` apontam para a compra e item de origem.

### AC-M7-016 [Backend] — Movimentação ENTRY vinculada ao lote

**Dado** uma entrada de estoque que gera lote
**Quando** a movimentação ENTRY é consultada
**Então** `batch_id` aponta para o lote criado.

---

## 6. Migração de Dados

### AC-M7-017 [Backend] — ENTRY existentes viram lotes

**Dado** 5 movimentações ENTRY existentes antes do M7
**Quando** a migração é executada
**Então** 5 lotes são criados, preservando `product_id`, `quantity`, `unit_cost` e `created_at`.

### AC-M7-018 [Backend] — ENTRY com unit_cost NULL preservam NULL

**Dado** uma ENTRY existente com `unit_cost = NULL`
**Quando** a migração cria o lote correspondente
**Então** o lote tem `unit_cost = NULL`, não zero.

---

## 7. Concorrência

### AC-M7-019 [Backend] — Duas saídas simultâneas não quebram lotes

**Dado** um produto com 10 unidades em um único lote
**Quando** duas saídas de 5 unidades são registradas simultaneamente
**Então** o lote fica exaurido (0 restantes) sem violar INV-006.

### AC-M7-020 [Backend] — Deadlock evitado por ordenação

**Dado** duas transações tentando consumir lotes do mesmo produto
**Quando** as transações executam simultaneamente
**Então** não ocorre deadlock graças à ordenação por `product_id` no `SELECT FOR UPDATE`.

---

## 8. Remoção do Custo Médio Ponderado

### AC-M7-021 [Backend] — API não expõe custo médio

**Dado** um produto com múltiplos lotes com custos diferentes
**Quando** o produto é consultado via API
**Então** a resposta não contém `average_cost` ou campo equivalente.

### AC-M7-022 [Backend] — reference_price permanece inalterado

**Dado** um produto com `reference_price = 50,00`
**Quando** um lote com `unit_cost = 2,00` é criado
**Então** `reference_price` permanece 50,00, não é alterado pelo custo do lote.

---

## 9. Frontend

### AC-M7-023 [Frontend] — Modal de estoque exibe lotes

**Dado** um produto com 3 lotes ativos
**Quando** o modal de estoque é aberto
**Então** a lista de lotes mostra: data de entrada, quantidade original, quantidade restante, custo unitário e origem.

### AC-M7-024 [Frontend] — Custo médio não é exibido

**Dado** o modal de estoque aberto
**Quando** o usuário visualiza as informações do produto
**Então** o custo médio ponderado não aparece na interface.

---

*Total: 24 critérios de aceitação.*
