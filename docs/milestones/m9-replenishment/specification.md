# M9 — Especificação de Reposição de Estoque

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — validado pelo Product Owner
**Marco:** M9 — Reposição de Estoque
**Fase:** 2 — Evolução do Estoque e dos Clientes

---

# 1. Finalidade

O M9 introduz a capacidade de **identificar produtos com estoque insuficiente** para atender às necessidades operacionais da Casa Afeto.

Antes do M9, o operador precisa manualmente verificar o estoque de cada produto e comparar com as cestas e vendas para saber o que precisa repor. Não há visibilidade centralizada sobre o que está faltando.

Após o M9, o sistema oferece uma **lista de reposição** que mostra:

```
Produto
    ↓
Estoque atual (soma dos lotes ativos)
    ↓
Necessidade estimada (cestas templates ativas)
    ↓
Necessidade urgente (vendas confirmadas)
    ↓
Status: OK | BAIXO | CRÍTICO
```

O M9 segue o princípio fundamental:

> **Visibilidade antes de automação.**

O sistema mostra o que precisa ser repostido. Não automatiza compras, não gera pedidos, não sugere fornecedores.

---

# 2. Escopo

## 2.1 Dentro do escopo

O M9 inclui:

### Cálculo de necessidade por cesta template

* Para cada template de cesta ativo, calcular a quantidade total de cada produto necessária;
* Somar as necessidades de todos os templates ativos para obter a necessidade estimada por produto.

### Cálculo de necessidade urgente por venda confirmada

* Para cada venda com status CONFIRMADA ou EM_PREPARAÇÃO, calcular a quantidade de cada produto necessária;
* Subtrair o que já foi baixado do estoque (movimentações OUTPUT vinculadas à venda);
* O restante é a necessidade urgente por produto.

### Estoque atual por produto

* Calcular o estoque físico de cada produto como soma das `quantity_remaining` dos lotes ativos (LOT-008);
* Expor o estoque atual junto com a necessidade.

### Lista de reposição

* Gerar uma lista de produtos com estoque insuficiente;
* Classificar cada produto como OK, BAIXO ou CRÍTICO;
* Exibir: produto, estoque atual, necessidade estimada, necessidade urgente e status.

### Filtros

* Filtrar a lista de reposição por status (BAIXO, CRÍTICO);
* Filtrar por produto específico.

## 2.2 Explicitamente fora do escopo

O seguinte **não** deve ser implementado como parte do M9:

* automação de compras — o M9 apenas mostra o que falta;
* sugestão de quantidade para comprar;
* integração com fornecedores;
* pedidos de compra;
* histórico de reposição;
* alertas automáticos ou notificações;
* cálculo de lead time ou prazo de entrega;
* estoque mínimo configurável por produto (por enquanto).

---

# 3. Dependências

O M9 depende de:

* `docs/domain/business-contract.md` — regras de negócio;
* `docs/product/roadmap.md` — direção da Fase 2;
* `docs/milestones/m1-products-inventory/specification.md` — produtos e estoque;
* `docs/milestones/m2-baskets/specification.md` — cestas e templates;
* `docs/milestones/m4-sales/specification.md` — vendas;
* `docs/milestones/m7-stock-batches/specification.md` — lotes de estoque;
* `docs/milestones/m8-expiry/specification.md` — vencimentos;
* `docs/architecture/technical-foundation.md` — fundamentos técnicos.

O M9 depende da implementação do M7 (lotes) e M8 (vencimentos) para calcular estoque atual corretamente.

---

# 4. Conceitos de Domínio

O M9 introduz um novo conceito:

```
Item de Reposição (ReplenishmentItem)
```

Um **Item de Reposição** representa a análise de reposição de um produto específico. Não é uma entidade persistente — é um cálculo derivado do estado atual do estoque, das cestas templates e das vendas.

```
Produto
  ↓
Item de Reposição
  ├─ product_id
  ├─ product_name
  ├─ stock_quantity (estoque atual)
  ├─ estimated_need (necessidade das cestas templates)
  ├─ urgent_need (necessidade das vendas confirmadas)
  ├─ total_need (estimated_need + urgent_need)
  ├─ shortage (total_need - stock_quantity, mínimo 0)
  └─ status: OK | BAIXO | CRÍTICO
```

Classificação de status:

```
OK: stock_quantity >= total_need
BAIXO: stock_quantity < total_need e urgent_need = 0
CRÍTICO: urgent_need > 0 e stock_quantity < urgent_need
```

---

# 5. Regras de Negócio

### REP-001 — Estoque atual por produto

O estoque atual de um produto é a soma das `quantity_remaining` de todos os lotes com status `ACTIVE` (LOT-008).

### REP-002 — Necessidade estimada por cesta template

A necessidade estimada de um produto é a soma das quantidades desse produto em todos os templates de cesta ativos.

Cada template ativo contribui com a quantidade do produto, independentemente de quantas vezes o template foi usado.

### REP-003 — Necessidade urgente por venda confirmada

A necessidade urgente de um produto é a soma das quantidades desse produto em todas as vendas com status CONFIRMADA ou EM_PREPARAÇÃO, menos o que já foi baixado do estoque.

Uma venda CONFIRMADA gera necessidade urgente porque o produto precisa estar disponível para preparação.
Uma venda EM_PREPARAÇÃO gera necessidade urgente porque o produto está sendo preparado agora.

### REP-004 — Status de reposição

Cada produto recebe um status de reposição:

* **OK:** Estoque suficiente para cobrir todas as necessidades.
* **BAIXO:** Estoque insuficiente para necessidades estimadas, mas sem necessidade urgente.
* **CRÍTICO:** Estoque insuficiente para necessidades urgentes (vendas confirmadas).

### REP-005 — Venda cancelada não gera necessidade

Uma venda com status CANCELADA não contribui para a necessidade urgente.

### REP-006 — Venda entregue não gera necessidade

Uma venda com status ENTREGUE não contribui para a necessidade urgente — o produto já foi baixado.

### REP-007 — Template inativo não gera necessidade

Um template de cesta com `active = false` não contribui para a necessidade estimada.

### REP-008 — Lista de reposição é cálculo em tempo real

A lista de reposição não é persistida. É calculada sob demanda a partir do estado atual do banco de dados.

### REP-009 — Produto sem estoque é BAIXO ou CRÍTICO

Se um produto tem estoque zero e há necessidade (estimada ou urgente), ele aparece como BAIXO ou CRÍTICO.

### REP-010 — Produto sem necessidade é OK

Se um produto não aparece em nenhum template ativo e não tem vendas confirmadas, ele é classificado como OK independentemente do estoque.

---

# 6. Comportamento Importante

## 6.1 Cálculo da necessidade urgente

A necessidade urgente considera apenas vendas que ainda precisam de produto físico:

```
Venda CONFIRMADA → necessidade urgente (produto ainda não baixado)
Venda EM_PREPARAÇÃO → necessidade urgente (produto sendo preparado)
Venda PRONTA → necessidade urgente (produto preparado, aguardando entrega)
Venda ENTREGUE → sem necessidade urgente (produto já baixado)
Venda CANCELADA → sem necessidade urgente
Venda RASCUNHO → sem necessidade urgente
```

A quantidade já baixada é calculada a partir das movimentações OUTPUT vinculadas à venda.

## 6.2 Impacto no M5 (Reservas e Baixas)

O M5 implementa reserva de estoque por venda. O M9 não interfere na lógica de reserva:

* A reserva (RES-001 a RES-012) continua operando no nível do produto.
* O M9 apenas calcula a necessidade com base no estado atual, sem alterar reservas.

## 6.3 Impacto no frontend

* Uma nova seção "Reposição" na navegação lateral;
* Uma tabela mostrando produtos com status BAIXO ou CRÍTICO;
* Filtros por status.

---

# 7. Decisões do Product Owner

### D-1: Visibilidade antes de automação

O M9 mostra o que precisa ser repostido. Não automatiza compras nem gera pedidos.

### D-2: Templates ativos definem necessidade estimada

A necessidade estimada é baseada nos templates de cesta ativos, não em um histórico de uso ou previsão.

### D-3: Vendas confirmadas definem necessidade urgente

A necessidade urgente é baseada em vendas CONFIRMADA, EM_PREPARAÇÃO e PRONTA — vendas que já comprometem o estoque.

### D-4: Cálculo em tempo real

A lista de reposição é calculada sob demanda. Não há tabela de cache ou agendamento.

---

# 8. Modelo de Dados

O M9 **não** introduz novas tabelas. Toda a informação necessária já existe:

* `stock_batches` — estoque atual por produto (via LOT-008);
* `basket_templates` + `basket_template_items` — necessidade estimada;
* `sales` + `sale_baskets` + `sale_basket_items` — necessidade urgente;
* `inventory_movements` — baixas já realizadas.

O cálculo de reposição é uma consulta SQL que agrega essas tabelas.

---

# 9. API

## 9.1 Novos endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/v1/inventory/replenishment` | Lista de reposição com filtros |

### `GET /api/v1/inventory/replenishment`

**Query parameters:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `status` | string | Não | Filtrar por status: `BAIXO`, `CRÍTICO`, `OK` |
| `product_id` | integer | Não | Filtrar por produto específico |

**Response:**

```json
{
  "items": [
    {
      "product_id": 1,
      "product_name": "Arroz 5kg",
      "stock_quantity": "2.00",
      "estimated_need": "10.00",
      "urgent_need": "5.00",
      "total_need": "15.00",
      "shortage": "13.00",
      "status": "CRÍTICO"
    }
  ],
  "total": 1
}
```

---

# 10. Frontend

## 10.1 Nova seção "Reposição"

* Item na navegação lateral com ícone de alerta;
* Tabela com colunas: Produto, Estoque, Necessidade Estimada, Necessidade Urgente, Falta, Status;
* Badges coloridos: verde (OK), amarelo (BAIXO), vermelho (CRÍTICO);
* Filtros por status acima da tabela;
* Estado vazio quando todos os produtos estão OK.

---

# 11. Testes

Os testes devem cobrir:

* Estoque atual calculado corretamente a partir dos lotes ativos;
* Necessidade estimada calculada a partir dos templates ativos;
* Necessidade urgente calculada a partir das vendas confirmadas;
* Status OK quando estoque >= necessidade total;
* Status BAIXO quando estoque < necessidade estimada e sem urgência;
* Status CRÍTICO quando estoque < necessidade urgente;
* Venda cancelada não gera necessidade;
* Venda entregue não gera necessidade;
* Template inativo não gera necessidade;
* Produto sem necessidade é OK;
* Produto sem estoque com necessidade é BAIXO/CRÍTICO;
* Filtro por status funciona;
* Filtro por produto funciona;
* Lista vazia quando todos os produtos estão OK.

---

# 12. Riscos

1. **Performance:** O cálculo de reposição requer múltiplas agregações. Mitigação: índices em `basket_template_items.product_id`, `sale_basket_items.product_id`, e `stock_batches.product_id`.
2. **Consistência:** Se o estoque mudar entre o cálculo e a ação do operador, os números podem estar desatualizados. Mitigação: o cálculo é em tempo real; o operador deve recarregar a lista antes de agir.
3. **Interpretação:** O operador pode confundir "necessidade estimada" com "necessidade real". Mitigação: labels claras no frontend distinguindo "cestas templates" de "vendas confirmadas".

---

# 13. Critérios de Aceitação

Os critérios de aceitação detalhados estão em `acceptance-criteria.md`.

Resumo:

* AC-M9-001 a AC-M9-005: cálculo de estoque e necessidade;
* AC-M9-006 a AC-M9-010: classificação de status;
* AC-M9-011 a AC-M9-015: filtros e API;
* AC-M9-016 a AC-M9-020: frontend.

---

# 14. Documentação a Atualizar

* `docs/domain/business-contract.md`: adicionar regras REP-001 a REP-010;
* `docs/product/roadmap.md`: atualizar status do M9;
* `docs/milestones/phase-2.md`: atualizar estado do M9;
* `docs/design/design-system.md`: se aplicável, padrões visuais para a seção de reposição.

---

*Fim da especificação do M9.*
