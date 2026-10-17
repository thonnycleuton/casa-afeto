# M6 — Especificação de Compras e Reposição de Estoque

**Versão do documento:** 0.3 (RASCUNHO)
**Status:** Rascunho — ajustes da auditoria final aplicados, pendente de aprovação final
**Marco:** M6 — Compras e Reposição de Estoque
**Fase:** 2 — Evolução do Estoque e dos Clientes

---

# 1. Finalidade

O M6 introduz o registro de compras recebidas pela Casa Afeto, permitindo que o operador registre a aquisição de produtos com suas unidades comerciais, fatores de conversão e preços pagos, gerando automaticamente as movimentações de estoque correspondentes.

Antes do M6, o operador registra entradas de estoque manualmente, sem vínculo a uma compra. O `unit_cost` em `InventoryMovement` já existe e alimenta o custo médio ponderado, mas não há contexto de aquisição.

Após o M6, o fluxo será:

```
Registro de compra
    ↓
Itens com unidade comercial, fator de conversão e preço pago
    ↓
Conversão para unidade-base do produto
    ↓
Geração atômica de ENTRY com unit_cost
    ↓
Estoque atualizado, custo médio recalculado
```

---

# 2. Escopo

## 2.1 Dentro do escopo

O M6 inclui:

### Compra

* registrar uma compra recebida com data de aquisição;
* vincular um ou mais itens de compra;
* consultar compras com filtros por período;
* consultar os itens de uma compra específica.

### Item de Compra

* vincular a um produto existente e ativo;
* informar a unidade comercial (texto livre);
* informar o fator de conversão para a unidade-base do produto;
* informar a quantidade na unidade comercial;
* informar o preço de aquisição por unidade comercial.

### Integração com Estoque

* gerar movimentação `ENTRY` para cada item de compra;
* calcular a quantidade em unidade-base a partir da quantidade comercial e do fator de conversão;
* calcular o `unit_cost` em unidade-base a partir do preço comercial e do fator de conversão;
* executar a criação da compra e a geração das ENTRY em uma única transação atômica;
* respeitar as regras de validação de ENTRY existentes (INV-001 a INV-008).

### Correção de Compras

* definir um mecanismo de correção rastreável para compras registradas incorretamente;
* preservar o histórico da compra original;
* respeitar estoque físico, reservas ativas e as regras INV-001 a INV-008 e RES-001 a RES-012.

## 2.2 Explicitamente fora do escopo

O seguinte **não** deve ser implementado como parte do M6:

* cadastro de fornecedores;
* lotes de estoque;
* datas de vencimento;
* política FEFO;
* perdas, avarias e consumo interno;
* produção interna;
* notas fiscais e importação de documentos;
* fluxo de rascunho de compra;
* alterações na lógica de pagamentos e vendas, salvo integração estritamente necessária;
* alertas de reposição automática;
* exclusão ou reversão silenciosa de compras recebidas.

Se a implementação parecer exigir uma dessas capacidades, o agente deve parar e determinar se o requisito é genuinamente necessário para o M6.

---

# 3. Dependências

O M6 depende de:

* `docs/domain/business-contract.md` — regras de negócio;
* `docs/product/roadmap.md` — direção da Fase 2;
* `docs/architecture/technical-foundation.md` — fundamentos técnicos;
* `docs/architecture/decisions/ADR-001-inventory-concurrency.md` — concorrência de estoque;
* `docs/milestones/m1-products-inventory/specification.md` — contratos de estoque existentes;
* `docs/milestones/m5-payments/specification.md` — regras de reserva e baixa (RES-001 a RES-012);
* `docs/architecture/decisions/ADR-002-m5-architecture.md` — decisões técnicas do M5.

O M6 depende da implementação do M1 (produtos, estoque, movimentações) e do M5 (reservas de estoque).

---

# 4. Conceitos de Domínio

O M6 introduz dois novos conceitos:

```
Compra
Item de Compra
```

### Compra

Uma **Compra** representa uma aquisição de produtos pela Casa Afeto, já recebida fisicamente.

Uma compra contém um ou mais itens de compra e uma data de aquisição.

Referência: `business-contract.md` §7 (compra conceitual).

Decisão do M6: uma compra registrada representa mercadoria recebida. Não há fluxo de rascunho neste marco.

### Item de Compra

Um **Item de Compra** descreve um produto adquirido dentro de uma compra.

Um item pode usar uma unidade comercial diferente da unidade-base de estoque do produto.

Referência: `business-contract.md` §4.3 (unidade comercial vs. unidade de estoque) e §7 (compra conceitual).

---

# 5. Regras de Negócio

## 5.1 Regras preservadas do contrato de negócio

O M6 **deve preservar** as seguintes regras aprovadas, sem alterá-las:

| Regra | Referência | Implicação para o M6 |
|-------|-----------|---------------------|
| **INV-001** | `business-contract.md` §36 | Estoque baseado em movimentações. O M6 gera `InventoryMovement` do tipo ENTRY. |
| **INV-002** | `business-contract.md` §36 | Preservação do histórico. O M6 não reescreve ENTRY existentes. |
| **INV-006** | `business-contract.md` §36 | Proibição de estoque físico negativo. ENTRY gerado por compra segue as mesmas regras de validação. |
| **INV-008** | `business-contract.md` §36 | Produto inativo não pode receber ENTRY. A compra de produto inativo deve ser rejeitada. |
| **PROD-001** | `business-contract.md` §36 | `base_unit` imutável após movimentação. O M6 opera na unidade base do produto. |
| **Custo pertence ao contexto de aquisição** | `business-contract.md` §6 | O `unit_cost` em ENTRY não é propriedade permanente do Produto. |
| **Custo médio ponderado** | `business-contract.md` §19.2 | Calculado apenas sobre ENTRY com `unit_cost` não-NULL. Custos ausentes ignorados. |
| **`reference_price` não varia com preço de compra** | `business-contract.md` §6.1 | O M6 não altera `reference_price` do produto. |
| **Preservação de registros** | `business-contract.md` §19.7 | Sem custos retroativos fictícios. |
| **RES-001 a RES-012** | `business-contract.md` §37 | Política completa de reserva e baixa. O M6 não altera. |
| **ADR-001** | `ADR-001` | Concorrência via `SELECT FOR UPDATE`. O M6 deve usar o mesmo padrão ao gerar ENTRY. |

## 5.2 Regras novas do M6

### PUR-001 — Compra representa mercadoria recebida

Uma compra registrada representa mercadoria já recebida fisicamente pela Casa Afeto. O registro da compra e a geração das movimentações `ENTRY` correspondentes constituem uma única operação atômica.

Se a geração de qualquer ENTRY falhar (produto inativo, quantidade inválida, etc.), a compra inteira não é registrada e nenhuma ENTRY é criada.

### PUR-002 — Unidade comercial e fator de conversão

Cada item de compra informa:

* a **unidade comercial** (texto livre, ex: "caixa", "fardo", "pacote");
* o **fator de conversão** para a unidade-base do produto (número positivo);
* a **quantidade** na unidade comercial (número positivo).

A quantidade em unidade-base é calculada como:

```
quantidade_base = quantidade_comercial × fator_de_conversão
```

Se o fator de conversão for 1, a unidade comercial é tratada como equivalente à unidade-base.

O fator de conversão pode variar entre compras do mesmo produto, conforme `business-contract.md` §4.3.

### PUR-003 — Preço de aquisição por unidade comercial

Cada item de compra informa o **preço de aquisição por unidade comercial** (`commercial_unit_price`).

* O preço é **obrigatório**.
* O preço aceita zero (`0.00`), representando itens obtidos sem custo (doação, brinde).
* O preço deve preservar o valor efetivamente informado, com precisão de duas casas decimais.
* Valores negativos são rejeitados.

### PUR-004 — Cálculo do custo por unidade-base

O `unit_cost` da ENTRY gerada é calculado a partir do preço comercial e do fator de conversão:

```
unit_cost = commercial_unit_price / fator_de_conversão
```

O `unit_cost` é arredondado para duas casas decimais.

Se `commercial_unit_price` for zero, `unit_cost` é zero.

O `unit_cost` é sempre populado na ENTRY gerada por compra (nunca NULL), pois o preço é obrigatório por item.

### PUR-005 — Validação de quantidade em unidade-base

A `quantidade_base` calculada (PUR-002) deve respeitar as regras de validação de ENTRY existentes:

* Para `base_unit = UN`: `quantidade_base` deve ser um número inteiro positivo.
* Para `base_unit = KG, G, L, ML`: `quantidade_base` deve ser um número decimal positivo.

Se a conversão resultar em quantidade fracionária para um produto com `base_unit = UN`, a criação da compra é rejeitada com mensagem indicando o produto e a quantidade calculada.

### PUR-006 — Produto ativo obrigatório

Um item de compra só pode referenciar um produto ativo. Se o produto estiver inativo, a criação da compra é rejeitada.

Esta regra deriva de INV-008: produto inativo não pode receber ENTRY.

### PUR-007 — Compra não altera `reference_price`

O registro de uma compra não modifica o `reference_price` do produto. O `reference_price` é uma propriedade comercial deliberada, independente do custo de aquisição (`business-contract.md` §6.1).

### PUR-008 — Compras não podem ser excluídas

Compras recebidas não podem ser excluídas nem revertidas silenciosamente. O histórico de compras e as ENTRY geradas devem ser preservados.

### PUR-009 — Correção de compras por compra complementar

Se uma compra foi registrada com erro (quantidade, preço, produto), a correção é feita por uma **nova compra complementar**, não alterando a compra original.

O operador pode registrar uma nova compra com os valores corretos. Se for necessário ajustar o estoque para compensar a compra errada, o fluxo de ajuste de estoque existente (ADJUSTMENT) deve ser usado separadamente, respeitando as regras INV-002 e INV-006.

**Nota sobre reservas ativas:** Se o estoque da compra errada já foi reservado ou consumido por vendas, o ajuste negativo pode ser rejeitado pelo sistema para proteger reservas ativas (conforme `inventory/service.py` e ADR-002). Neste caso, o operador deve registrar a compra correta e usar o fluxo de ajuste apenas quando o saldo permitir.

**Decisão aprovada:** Opção A (compra complementar + ajuste manual) confirmada pelo Product Owner. Ver seção 12.1.

### PUR-010 — Consulta de compras

O sistema deve permitir consultar compras com seus itens, filtradas por período de aquisição (data inicial e data final opcionais).

### PUR-011 — Integração transacional com ENTRY

A criação de uma compra e a geração de todas as suas ENTRY ocorrem em uma única transação de banco de dados. Se qualquer validação ou inserção falhar, toda a operação é revertida: nem a compra nem nenhuma ENTRY são persistidas.

### PUR-012 — Concorrência de estoque

Ao gerar ENTRY a partir de compra, o sistema deve respeitar o padrão de concorrência definido em ADR-001: `SELECT FOR UPDATE` no produto antes de calcular o saldo e inserir a movimentação.

Quando uma compra contém múltiplos produtos diferentes, os locks devem ser adquiridos em ordem crescente de `product_id`, conforme a hierarquia de locks do ADR-002 (D-3), para evitar deadlocks entre compras concorrentes.

Cada item de compra que gera ENTRY para o mesmo produto deve ser processado com o mesmo padrão de lock. Se uma compra contém múltiplos itens do mesmo produto, cada item gera sua própria ENTRY separada (não consolidadas), para preservar a rastreabilidade individual de unidade comercial, fator de conversão e preço. Ver seção 12.3.

---

# 6. Modelo Conceitual

## 6.1 Entidades

```
purchases
  id (PK)
  purchased_at (TIMESTAMP WITH TIME ZONE)
  created_at (TIMESTAMP WITH TIME ZONE)

purchase_items
  id (PK)
  purchase_id (FK → purchases.id, RESTRICT)
  product_id (FK → products.id, RESTRICT)
  commercial_unit (VARCHAR, nullable)
  conversion_factor (DECIMAL, > 0)
  commercial_quantity (DECIMAL, > 0)
  commercial_unit_price (DECIMAL, >= 0, 2 casas decimais)
```

## 6.2 Relações

```
Purchase 1 ──── N PurchaseItem
PurchaseItem N ──── 1 Product
PurchaseItem N ──── 1 InventoryMovement (ENTRY gerada)
```

Cada `PurchaseItem` gera exatamente uma `InventoryMovement` do tipo ENTRY.

Se uma compra contém múltiplos itens do mesmo produto, cada item gera sua própria ENTRY (não consolidadas), para preservar a rastreabilidade individual de unidade comercial, fator de conversão e preço.

**Decisão aprovada:** Itens do mesmo produto geram ENTRY separadas (não consolidadas), para preservar a rastreabilidade individual. Confirmado pelo Product Owner. Ver seção 12.3.

## 6.3 Campos excluídos do M6

Os seguintes campos **não** fazem parte do M6:

* `supplier_id` em `purchases` — fornecedores ficam fora do M6;
* `status` em `purchases` — não há fluxo de rascunho;
* `notes` em `purchases` — pode ser adicionado futuramente;
* `lot_id` em `purchase_items` — lotes ficam para marco posterior;
* `expiry_date` em `purchase_items` — validade fica para marco posterior;
* `invoice_number` em `purchases` — notas fiscais fora do escopo.

---

# 7. Fluxos

## 7.1 Criar Compra Recebida

```
Operador inicia criação de compra
    ↓
Informa data de aquisição (opcional; padrão: data/hora atual)
    ↓
Adiciona um ou mais itens:
  - Seleciona produto ativo
  - Informa unidade comercial (opcional)
  - Informa fator de conversão (obrigatório, > 0)
  - Informa quantidade comercial (obrigatório, > 0)
  - Informa preço por unidade comercial (obrigatório, >= 0)
    ↓
Validações:
  - Produto existe e está ativo (PUR-006)
  - Fator de conversão > 0 (PUR-002)
  - Quantidade comercial > 0 (PUR-002)
  - Preço >= 0 (PUR-003)
  - quantidade_base = quantidade_comercial × fator_de_conversão
  - quantidade_base respeita regras de UN inteiro / decimal (PUR-005)
    ↓
Início da transação atômica (PUR-011):
  - Persiste Purchase com purchased_at
  - Para cada item, em ordem:
    - Lock do produto (SELECT FOR UPDATE) — PUR-012
    - Calcula unit_cost = commercial_unit_price / fator_de_conversão (PUR-004)
    - Cria InventoryMovement ENTRY com:
      - quantity = quantidade_base
      - unit_cost = unit_cost calculado
      - type = ENTRY
      - sale_id = NULL
      - purchase_id = id da compra (rastreabilidade)
    - Cria PurchaseItem
    ↓
Sucesso: retorna compra com itens e ENTRY geradas
Falha: reverte toda a transação, retorna erro com detalhes
```

## 7.2 Consultar Compras

```
Operador solicita lista de compras
    ↓
Filtros opcionais:
  - purchased_at >= data_inicial
  - purchased_at <= data_final
    ↓
Retorna lista de compras com:
  - id
  - purchased_at
  - itens (com produto, unidade comercial, quantidade, preço)
    ↓
Ordenação: purchased_at descendente (mais recente primeiro)
```

## 7.3 Consultar Compra Individual

```
Operador solicita detalhes de uma compra
    ↓
Retorna:
  - id
  - purchased_at
  - created_at
  - lista de itens com:
    - product_id, product_name, base_unit
    - commercial_unit
    - conversion_factor
    - commercial_quantity
    - commercial_unit_price
    - calculated_base_quantity (quantidade_base)
    - calculated_unit_cost (unit_cost da ENTRY)
```

---

# 8. Validações

## 8.1 Validações de entrada

| Campo | Regra | Erro esperado |
|-------|-------|---------------|
| `purchased_at` | Opcional; se informado, não pode ser nulo | "Data de aquisição inválida." |
| Itens | Lista não vazia (mínimo 1 item) | "A compra deve conter pelo menos um item." |
| `product_id` | Produto deve existir | "Produto não encontrado." |
| `product_id` | Produto deve estar ativo (PUR-006) | "Não é possível comprar produto inativo." |
| `conversion_factor` | Obrigatório, > 0 | "O fator de conversão deve ser maior que zero." |
| `commercial_quantity` | Obrigatório, > 0 | "A quantidade comercial deve ser maior que zero." |
| `commercial_unit_price` | Obrigatório, >= 0, 2 casas decimais | "O preço de aquisição deve ser maior ou igual a zero." |
| `commercial_unit` | Texto livre, opcional | — |

## 8.2 Validações de negócio

| Regra | Condição | Erro esperado |
|-------|----------|---------------|
| PUR-005 | `quantidade_base` fracionária com `base_unit = UN` | "Produto {nome}: a conversão resultou em quantidade fracionária ({qty}) para unidade UN." |
| INV-008 | Produto inativo bloqueia ENTRY | "Não é possível comprar produto inativo." |
| PUR-011 | Falha em qualquer item invalida toda a compra | "Falha ao registrar compra: {detalhe do item falhado}." |

## 8.3 Validações herdadas de ENTRY

As validações de ENTRY existentes em `inventory/service.py` (`create_movement`) aplicam-se às ENTRY geradas pelo M6:

* `quantity > 0` para ENTRY;
* `unit_cost` não negativo quando informado;
* produto ativo obrigatório;
* validação de UN inteiro vs. KG/G/L/ML decimal;
* concorrência via `SELECT FOR UPDATE` (ADR-001).

---

# 9. Tratamento de Erros

## 9.1 Erros de validação de entrada

Retornam HTTP 422 (Unprocessable Entity) com detalhes do campo inválido.

## 9.2 Erros de regra de negócio

Retornam HTTP 409 (Conflict) com mensagem descritiva da regra violada.

Exemplos:

* Produto inativo: "Não é possível comprar produto inativo."
* Quantidade fracionária em UN: "Produto X: a conversão resultou em quantidade fracionária (24.5) para unidade UN."
* Item duplicado com conversão inválida: mensagem específica do item.

## 9.3 Falha transacional

Se a criação de uma ENTRY falhar durante o processamento de uma compra com múltiplos itens:

* A transação é revertida integralmente (PUR-011).
* Nem a compra nem nenhuma ENTRY são persistidas.
* O erro retornado indica qual item falhou e por quê.

## 9.4 Produto não encontrado

Retorna HTTP 404 (Not Found): "Produto não encontrado."

---

# 10. Rastreabilidade

Cada ENTRY gerada por uma compra deve ser rastreável de volta à compra de origem.

**Decisão aprovada:** Adicionar coluna `purchase_id` (FK → purchases.id, nullable, SET NULL) em `inventory_movements`. Confirmado pelo Product Owner. Ver seção 12.2.

* ENTRY gerada por compra: `purchase_id` populado.
* ENTRY manual (M1): `purchase_id = NULL`.
* OUTPUT de venda (M5): `purchase_id = NULL`, `sale_id` populado.
* ADJUSTMENT: `purchase_id = NULL`.

Esta alteração é compatível com o modelo existente: `sale_id` já segue o mesmo padrão (nullable, SET NULL).

---

# 11. Impacto no Custo Médio Ponderado

As ENTRY geradas pelo M6 populam `unit_cost` obrigatoriamente (PUR-004). Isso alimenta diretamente o cálculo de custo médio ponderado existente (`inventory/service.py`, `product_average_costs`):

```
custo_médio = SUM(qty × unit_cost das ENTRY com unit_cost não-NULL) / SUM(qty das ENTRY com unit_cost não-NULL)
```

Como o M6 sempre popula `unit_cost`, as ENTRY de compra participam do cálculo de custo médio.

Compras com preço zero (`commercial_unit_price = 0`) geram `unit_cost = 0`, que participa do cálculo da média (reduzindo o custo médio ponderado).

Este comportamento é consistente com `business-contract.md` §19.2: custos ausentes (NULL) são ignorados; custos zero participam do cálculo.

---

# 12. Decisões do Product Owner

As seguintes decisões foram confirmadas pelo Product Owner:

## 12.1 Mecanismo de correção de compras

**Decisão: Opção A aprovada — Compra complementar + ajuste manual.**

Quando uma compra foi registrada com erro, a correção é feita por uma nova compra complementar. A compra original permanece inalterada. Se necessário, o operador usa o fluxo de ajuste de estoque (ADJUSTMENT) separadamente.

**Justificativa:** Abordagem mais simples e segura. A Opção B (estorno com ENTRY reversa) foi rejeitada para o M6 devido ao risco de violar INV-006 ou comprometer reservas ativas (RES-001 a RES-012).

**Nota:** Se o estoque da compra errada já foi reservado ou consumido por vendas, o ajuste negativo pode ser rejeitado pelo sistema para proteger reservas ativas. Neste caso, o operador registra a compra correta e usa ajuste apenas quando o saldo permitir.

## 12.2 Rastreabilidade de ENTRY para compra

**Decisão: Opção A aprovada — `purchase_id` em `inventory_movements`.**

Adicionar coluna `purchase_id` (FK → purchases.id, nullable, SET NULL) em `inventory_movements` para rastreabilidade direta no histórico de movimentações.

**Justificativa:** Consistência com `sale_id`, que já segue o mesmo padrão (nullable, SET NULL) em `inventory_movements` (ADR-002, D-2). A migração é de baixo risco (coluna nullable).

## 12.3 Consolidação de itens do mesmo produto

**Decisão: Opção A aprovada — ENTRY separada por item.**

Se uma compra contém múltiplos itens do mesmo produto, cada item gera sua própria ENTRY separada, preservando a rastreabilidade individual de unidade comercial, fator de conversão e preço.

**Justificativa:** A Opção B (consolidação) perderia a granularidade de preço por item. Se dois itens do mesmo produto têm fatores de conversão ou preços diferentes, consolidar em uma ENTRY perderia essa informação.

## 12.4 `commercial_unit` como campo opcional

**Decisão: Manter opcional.**

A unidade comercial (`commercial_unit`) permanece opcional. Se o operador não informa, o sistema trata a quantidade como já estando na unidade-base (fator de conversão = 1).

**Justificativa:** Simplifica o caso comum onde a unidade comercial é a mesma que a unidade-base (ex: compra de chocolate por unidade). Exigir `commercial_unit` adicionaria fricção sem benefício claro para o caso comum.

---

# 13. Critérios de Aceitação

## AC-M6-001 — Criação de compra com um item

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

## AC-M6-002 — Criação de compra com múltiplos itens

**Dado** produtos ativos Chocolate (UN) e Suco (L)
**Quando** o operador registra uma compra com 2 itens:
- Item 1: Chocolate, "caixa", fator 24, qty 2, preço 48.00
- Item 2: Suco, "fardo", fator 12, qty 1, preço 36.00
**Então** a compra é registrada com sucesso
**E** são criadas 2 ENTRY:
- Chocolate: `quantity = 48`, `unit_cost = 2.00`
- Suco: `quantity = 12`, `unit_cost = 3.00`

## AC-M6-003 — Rejeição de compra com produto inativo

**Dado** um produto inativo
**Quando** o operador tenta registrar uma compra contendo esse produto
**Então** a compra não é registrada
**E** nenhuma ENTRY é criada
**E** o erro indica que o produto está inativo

## AC-M6-004 — Rejeição de conversão fracionária em UN

**Dado** um produto ativo com `base_unit = UN`
**Quando** o operador registra uma compra com:
- fator de conversão: 2.5
- quantidade comercial: 1
**Então** a compra não é registrada
**E** nenhuma ENTRY é criada
**E** o erro indica que a conversão resultou em quantidade fracionária

## AC-M6-005 — Preço zero aceito

**Dado** um produto ativo
**Quando** o operador registra uma compra com `commercial_unit_price = 0.00`
**Então** a compra é registrada com sucesso
**E** a ENTRY é criada com `unit_cost = 0.00`

## AC-M6-006 — Preço negativo rejeitado

**Dado** um produto ativo
**Quando** o operador tenta registrar uma compra com `commercial_unit_price < 0`
**Então** a compra não é registrada
**E** o erro indica que o preço deve ser não negativo

## AC-M6-007 — Fator de conversão zero rejeitado

**Quando** o operador tenta registrar uma compra com `conversion_factor = 0`
**Então** a compra não é registrada
**E** o erro indica que o fator deve ser maior que zero

## AC-M6-008 — Atomicidade: falha em um item invalida toda a compra

### 8a — Falha na validação de entrada

**Dado** produtos A (ativo) e B (inativo)
**Quando** o operador registra uma compra com itens de A e B
**Então** a compra não é registrada
**E** nenhuma ENTRY é criada para nenhum produto
**E** o estoque de A não é alterado

### 8b — Falha durante a persistência transacional

**Dado** uma compra com 2 itens válidos de produtos ativos
**Quando** a criação da primeira ENTRY ocorre com sucesso, mas a criação da segunda ENTRY falha (ex: violação de constraint de banco)
**Então** toda a transação é revertida
**E** a compra não é persistida
**E** a primeira ENTRY é revertida e não permanece no banco
**E** nenhum registro parcial da operação é deixado no banco

## AC-M6-009 — Custo médio ponderado atualizado

**Dado** um produto com ENTRY anterior: qty 100, unit_cost 2.00
**Quando** o operador registra uma compra: qty_base 50, unit_cost 3.00
**Então** o custo médio ponderado do produto é recalculado
**E** o custo médio é `(100 × 2.00 + 50 × 3.00) / (100 + 50) = 2.33`

## AC-M6-010 — `reference_price` não alterado pela compra

**Dado** um produto com `reference_price = 5.00`
**Quando** o operador registra uma compra com `unit_cost = 2.00`
**Então** o `reference_price` do produto permanece `5.00`

## AC-M6-011 — Consulta de compras por período

**Dado** compras registradas em diferentes datas
**Quando** o operador filtra por `purchased_at` entre duas datas
**Então** apenas as compras dentro do período são retornadas

## AC-M6-012 — Consulta de compra individual com itens

**Dado** uma compra registrada com 3 itens
**Quando** o operador consulta a compra pelo ID
**Então** a compra é retornada com todos os 3 itens e seus detalhes

## AC-M6-013 — Compra sem itens rejeitada

**Quando** o operador tenta registrar uma compra sem itens
**Então** a compra não é registrada
**E** o erro indica que a compra deve conter pelo menos um item

## AC-M6-014 — Concorrência: ENTRY de compra respeita lock de produto

**Dado** duas requisições concorrentes de compra do mesmo produto
**Quando** ambas tentam criar ENTRY simultaneamente
**Então** as operações são serializadas pelo lock do produto
**E** o saldo final reflete corretamente ambas as entradas
**E** nenhuma ENTRY é perdida ou duplicada

## AC-M6-015 — Unidade comercial opcional

**Dado** um produto ativo com `base_unit = UN`
**Quando** o operador registra uma compra sem informar `commercial_unit`:
- fator de conversão: 1
- quantidade comercial: 10
- preço: 2.00
**Então** a compra é registrada com sucesso
**E** a ENTRY é criada com `quantity = 10`, `unit_cost = 2.00`

## AC-M6-016 — `purchased_at` padrão

**Quando** o operador registra uma compra sem informar `purchased_at`
**Então** a compra é registrada com `purchased_at` igual à data/hora atual do servidor

## AC-M6-017 — Conversão com KG

**Dado** um produto ativo com `base_unit = KG`
**Quando** o operador registra uma compra com:
- unidade comercial: "saco"
- fator de conversão: 5
- quantidade comercial: 3
- preço: 25.00
**Então** a compra é registrada com sucesso
**E** a ENTRY é criada com `quantity = 15.0`, `unit_cost = 5.00`

## AC-M6-018 — Compras não podem ser excluídas

**Dado** uma compra registrada com ENTRY geradas
**Quando** o operador tenta excluir a compra
**Então** a exclusão é rejeitada
**E** a compra e suas ENTRY permanecem intactas
**E** as ENTRY geradas pela compra não podem ser excluídas individualmente

## AC-M6-019 — Correção por compra complementar

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

## AC-M6-020 — Rastreabilidade de ENTRY para compra via `purchase_id`

**Dado** uma compra registrada com 2 itens
**Quando** o operador consulta o histórico de movimentações de um dos produtos
**Então** as ENTRY geradas pela compra mostram `purchase_id` populado
**E** é possível identificar a compra de origem de cada ENTRY
**E** as ENTRY manuais (M1) mostram `purchase_id = NULL`

## AC-M6-021 — Itens do mesmo produto geram ENTRY separadas

**Dado** um produto ativo com `base_unit = UN`
**Quando** o operador registra uma compra com 2 itens do mesmo produto:
- Item 1: "caixa", fator 24, qty 1, preço 48.00
- Item 2: "caixa", fator 24, qty 1, preço 54.00
**Então** a compra é registrada com sucesso
**E** são criadas 2 ENTRY separadas:
- ENTRY 1: `quantity = 24`, `unit_cost = 2.00`
- ENTRY 2: `quantity = 24`, `unit_cost = 2.25`
**E** ambas as ENTRY referenciam a mesma compra via `purchase_id`

---

# 14. Referências

| Documento | Seção | Conteúdo Referenciado |
|-----------|-------|----------------------|
| `business-contract.md` | §4.3 | Unidade comercial vs. unidade de estoque |
| `business-contract.md` | §6 | Custo pertence ao contexto de aquisição |
| `business-contract.md` | §6.1 | `reference_price` independente do custo |
| `business-contract.md` | §7 | Compra conceitual |
| `business-contract.md` | §8.1 | Regras de quantidade para ENTRY |
| `business-contract.md` | §19 | Custo e precificação |
| `business-contract.md` | §36 | Regras formais INV-001 a INV-008, PROD-001 |
| `business-contract.md` | §37 | Política RES-001 a RES-012 |
| `business-contract.md` | §38 | Decisões pendentes de compras |
| `roadmap.md` | §14.1 | Fase 2: Gestão de Compras |
| `ADR-001` | §2 | Concorrência de estoque com SELECT FOR UPDATE |
| `ADR-002` | D-2 | OUTPUT + sale_id em inventory_movements |
| `m1-products-inventory/specification.md` | §14-16 | Modelo de estoque e movimentações |
| `m5-payments/specification.md` | §6-10 | Política de reserva e baixa |

---

# 15. Notas de Implementação

## 15.1 Migração de banco de dados

O M6 requer, no mínimo:

1. Tabela `purchases` (nova).
2. Tabela `purchase_items` (nova).
3. Coluna `purchase_id` em `inventory_movements` (nova, nullable, FK com SET NULL) — **sujeito à decisão 12.2**.

## 15.2 API proposta

Endpoints sugeridos:

| Método | Caminho | Descrição |
|--------|---------|-----------|
| POST | `/api/v1/purchases` | Criar compra recebida |
| GET | `/api/v1/purchases` | Listar compras (com filtros opcionais) |
| GET | `/api/v1/purchases/{id}` | Detalhes de uma compra |

## 15.3 Integração com `create_movement`

O M6 deve reutilizar `inventory/service.py:create_movement()` para gerar as ENTRY, garantindo que todas as validações existentes (INV-006, INV-008, UN inteiro, etc.) sejam aplicadas automaticamente.

A função `create_movement` deve ser estendida para aceitar um parâmetro `purchase_id` (int | None), análogo ao parâmetro `sale_id` já existente, para permitir a rastreabilidade de ENTRY geradas por compra (decisão 12.2).

O parâmetro `use_savepoint` deve ser configurado adequadamente para que a transação atômica da compra (PUR-011) envolva todos os itens.

## 15.4 Precisão decimal

Todos os cálculos de quantidade e custo devem usar `Decimal` (Python) / `NUMERIC` (PostgreSQL) para evitar erros de arredondamento de ponto flutuante.

O `unit_cost` é arredondado para duas casas decimais com `quantize(Decimal("0.01"))`.

A `quantidade_base` é calculada como `commercial_quantity × conversion_factor` sem arredondamento intermediário. A validação de UN inteiro é aplicada ao resultado final.

---

# 16. Status do Documento

Este documento é um **rascunho** e está pendente de aprovação final.

As decisões do Product Owner (seção 12) foram registradas e confirmadas:

* 12.1 — Correção de compras: Opção A aprovada.
* 12.2 — Rastreabilidade: Opção A aprovada (`purchase_id` em `inventory_movements`).
* 12.3 — Consolidação de itens: Opção A aprovada (ENTRY separada por item).
* 12.4 — `commercial_unit` opcional: confirmado.

O documento está pronto para aprovação final e subsequente implementação.

---

# 17. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|----------|
| 0.1 | 2026-10-15 | Especificação inicial criada. |
| 0.2 | 2026-10-15 | Decisões 12.1–12.4 registradas como aprovadas. Contradição PUR-012 vs §6.2 corrigida. INV-006 removido da tabela de validações. Fluxo 7.1 reordenado. Nota sobre reservas ativas adicionada em PUR-009. Referência `business-concept.md` corrigida. Critérios AC-M6-019 a AC-M6-021 adicionados. AC-M6-018 estendido para cobrir ENTRY. |
| 0.3 | 2026-10-15 | Ajustes da auditoria final independente: PUR-012 com ordem de lock por `product_id` (ADR-002 D-3). §15.3 com nota de extensão de `create_movement` para `purchase_id`. AC-M6-008 dividido em 8a (falha de entrada) e 8b (falha transacional intermediária). AC-M6-019 enriquecido com valores numéricos concretos. |

---

*Fim da especificação do M6.*
