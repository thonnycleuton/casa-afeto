# M9 — Casos de Uso

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — validado pelo Product Owner
**Marco:** M9 — Reposição de Estoque

---

## UC-M9-001 — Consultar lista de reposição

**Atores:** Operador

**Pré-condições:**
- Existem templates de cesta ativos com produtos;
- Existem produtos com estoque registrado.

**Fluxo principal:**
1. O operador acessa a seção "Reposição" na navegação lateral;
2. O sistema calcula o estoque atual, necessidade estimada e necessidade urgente de cada produto;
3. O sistema classifica cada produto como OK, BAIXO ou CRÍTICO;
4. O sistema exibe a tabela de reposição com todos os produtos.

**Resultado:** O operador vê a lista completa de produtos com seu status de reposição.

---

## UC-M9-002 — Filtrar produtos críticos

**Atores:** Operador

**Pré-condições:**
- Existem produtos com status CRÍTICO na lista de reposição.

**Fluxo principal:**
1. O operador acessa a seção "Reposição";
2. O operador clica no filtro "CRÍTICO";
3. O sistema filtra a lista mostrando apenas produtos CRÍTICO;
4. O sistema exibe os produtos com estoque insuficiente para vendas confirmadas.

**Resultado:** O operador vê apenas os produtos que precisam de atenção imediata.

---

## UC-M9-003 — Filtrar produtos baixos

**Atores:** Operador

**Pré-condições:**
- Existem produtos com status BAIXO na lista de reposição.

**Fluxo principal:**
1. O operador acessa a seção "Reposição";
2. O operador clica no filtro "BAIXO";
3. O sistema filtra a lista mostrando apenas produtos BAIXO;
4. O sistema exibe os produtos com estoque insuficiente para cestas templates, sem urgência.

**Resultado:** O operador vê os produtos que precisam de reposição planejada.

---

## UC-M9-004 — Ver estado vazio quando tudo OK

**Atores:** Operador

**Pré-condições:**
- Todos os produtos têm estoque suficiente (status OK).

**Fluxo principal:**
1. O operador acessa a seção "Reposição";
2. O sistema calcula o status de todos os produtos;
3. Como todos estão OK, o sistema exibe uma mensagem de estado vazio.

**Resultado:** O operador sabe que não há produtos que precisam de reposição.

---

## UC-M9-005 — Ver reposição após venda confirmada

**Atores:** Operador

**Pré-condições:**
- Um produto tinha status OK antes;
- Uma nova venda CONFIRMADA é registrada com esse produto.

**Fluxo principal:**
1. O operador registra uma venda CONFIRMADA com um produto;
2. O operador acessa a seção "Reposição";
3. O sistema recalcula a necessidade urgente incluindo a nova venda;
4. O produto pode mudar de status para BAIXO ou CRÍTICO.

**Resultado:** O operador vê o produto com o novo status refletindo a venda confirmada.

---

## UC-M9-006 — Ver reposição após compra recebida

**Atores:** Operador

**Pré-condições:**
- Um produto tinha status BAIXO ou CRÍTICO;
- Uma nova compra é registrada, gerando um lote de estoque.

**Fluxo principal:**
1. O operador registra uma compra com o produto;
2. O sistema cria um novo lote de estoque (M7);
3. O operador acessa a seção "Reposição";
4. O sistema recalcula o estoque atual incluindo o novo lote;
5. O produto pode mudar de status para OK.

**Resultado:** O operador vê o produto com o novo status refletindo o estoque atualizado.

---

*Fim dos casos de uso do M9.*
