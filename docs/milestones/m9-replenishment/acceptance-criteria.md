# M9 — Critérios de Aceitação

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — validado pelo Product Owner
**Marco:** M9 — Reposição de Estoque

---

## Backend

### AC-M9-001 [Backend] — Estoque atual calculado a partir dos lotes ativos

O sistema calcula o estoque atual de um produto como soma das `quantity_remaining` de todos os lotes com status `ACTIVE`.

**Verificação:**
- Dado um produto com 3 lotes ativos (quantidades 5, 3, 2), o estoque retornado é 10.
- Dado um produto com 1 lote ativo (quantidade 5) e 1 lote EXHAUSTED (quantidade 0), o estoque retornado é 5.

### AC-M9-002 [Backend] — Necessidade estimada calculada a partir dos templates ativos

O sistema calcula a necessidade estimada de um produto somando as quantidades desse produto em todos os templates de cesta ativos.

**Verificação:**
- Dado 2 templates ativos com o mesmo produto (quantidades 3 e 2), a necessidade estimada é 5.
- Dado 1 template ativo e 1 template inativo com o mesmo produto, apenas o template ativo contribui.

### AC-M9-003 [Backend] — Necessidade urgente calculada a partir das vendas confirmadas

O sistema calcula a necessidade urgente de um produto somando as quantidades desse produto em vendas CONFIRMADA, EM_PREPARAÇÃO e PRONTA.

**Verificação:**
- Dado uma venda CONFIRMADA com 2 unidades de um produto, a necessidade urgente é 2.
- Dado uma venda RASCUNHO com 2 unidades de um produto, a necessidade urgente é 0.

### AC-M9-004 [Backend] — Venda cancelada não gera necessidade

Uma venda com status CANCELADA não contribui para a necessidade urgente.

**Verificação:**
- Dado uma venda CANCELADA com 5 unidades de um produto, a necessidade urgente é 0.

### AC-M9-005 [Backend] — Venda entregue não gera necessidade

Uma venda com status ENTREGUE não contribui para a necessidade urgente.

**Verificação:**
- Dado uma venda ENTREGUE com 5 unidades de um produto, a necessidade urgente é 0.

### AC-M9-006 [Backend] — Status OK quando estoque suficiente

Um produto é classificado como OK quando o estoque atual é maior ou igual à necessidade total (estimada + urgente).

**Verificação:**
- Dado estoque 10, necessidade estimada 5, necessidade urgente 3, o status é OK.
- Dado estoque 10, necessidade estimada 0, necessidade urgente 0, o status é OK.

### AC-M9-007 [Backend] — Status BAIXO quando estoque insuficiente sem urgência

Um produto é classificado como BAIXO quando o estoque é menor que a necessidade estimada e não há necessidade urgente.

**Verificação:**
- Dado estoque 3, necessidade estimada 5, necessidade urgente 0, o status é BAIXO.

### AC-M9-008 [Backend] — Status CRÍTICO quando estoque insuficiente com urgência

Um produto é classificado como CRÍTICO quando há necessidade urgente e o estoque é menor que a necessidade urgente.

**Verificação:**
- Dado estoque 2, necessidade estimada 5, necessidade urgente 4, o status é CRÍTICO.

### AC-M9-009 [Backend] — Template inativo não gera necessidade

Um template de cesta com `active = false` não contribui para a necessidade estimada.

**Verificação:**
- Dado 1 template ativo (quantidade 3) e 1 template inativo (quantidade 7), a necessidade estimada é 3.

### AC-M9-010 [Backend] — Produto sem necessidade é OK

Se um produto não aparece em nenhum template ativo e não tem vendas confirmadas, ele é classificado como OK independentemente do estoque.

**Verificação:**
- Dado um produto com estoque 0, sem templates ativos e sem vendas confirmadas, o status é OK.

### AC-M9-011 [Backend] — Endpoint retorna lista de reposição

O endpoint `GET /api/v1/inventory/replenishment` retorna a lista completa de produtos com seus dados de reposição.

**Verificação:**
- A resposta contém `items` com `product_id`, `product_name`, `stock_quantity`, `estimated_need`, `urgent_need`, `total_need`, `shortage` e `status`.
- A resposta contém `total` com o número de itens.

### AC-M9-012 [Backend] — Filtro por status funciona

O parâmetro `status` filtra a lista de reposição pelo status especificado.

**Verificação:**
- `?status=CRÍTICO` retorna apenas produtos com status CRÍTICO.
- `?status=BAIXO` retorna apenas produtos com status BAIXO.
- `?status=OK` retorna apenas produtos com status OK.

### AC-M9-013 [Backend] — Filtro por produto funciona

O parâmetro `product_id` filtra a lista de reposição por um produto específico.

**Verificação:**
- `?product_id=1` retorna apenas o produto com ID 1.

### AC-M9-014 [Backend] — Shortage calculado corretamente

O campo `shortage` é calculado como `total_need - stock_quantity`, com mínimo 0.

**Verificação:**
- Dado estoque 10, necessidade total 15, o shortage é 5.
- Dado estoque 10, necessidade total 5, o shortage é 0.

### AC-M9-015 [Backend] — Lista de reposição é cálculo em tempo real

A lista de reposição é calculada sob demanda, não persistida.

**Verificação:**
- Após alterar o estoque de um produto, a próxima chamada ao endpoint reflete a mudança imediatamente.

---

## Frontend

### AC-M9-016 [Frontend] — Seção "Reposição" na navegação

O aplicativo possui uma seção "Reposição" acessível pela navegação lateral.

**Verificação:**
- O item "Reposição" aparece na sidebar.
- Clicar no item "Reposição" exibe a página de reposição.

### AC-M9-017 [Frontend] — Tabela de reposição com colunas

A página de reposição exibe uma tabela com as colunas: Produto, Estoque, Necessidade Estimada, Necessidade Urgente, Falta e Status.

**Verificação:**
- A tabela exibe todos os campos corretamente.
- Os valores numéricos são formatados com duas casas decimais.

### AC-M9-018 [Frontend] — Badges coloridos por status

Cada produto na tabela de reposição exibe um badge colorido indicando o status:

- Verde para OK
- Amarelo para BAIXO
- Vermelho para CRÍTICO

**Verificação:**
- Produtos CRÍTICO têm badge vermelho.
- Produtos BAIXO têm badge amarelo.
- Produtos OK têm badge verde.

### AC-M9-019 [Frontend] — Filtros por status

A página de reposição possui filtros por status acima da tabela.

**Verificação:**
- Clicar no filtro "CRÍTICO" mostra apenas produtos CRÍTICO.
- Clicar no filtro "BAIXO" mostra apenas produtos BAIXO.
- Clicar no filtro "Todos" mostra todos os produtos.

### AC-M9-020 [Frontend] — Estado vazio quando tudo OK

Quando todos os produtos estão com status OK, a página exibe uma mensagem informando que não há produtos que precisam de reposição.

**Verificação:**
- Com todos os produtos OK, a tabela é substituída por uma mensagem de estado vazio.

---

*Fim dos critérios de aceitação do M9.*
