# ADR-004: Fator de Conversão Comercial do Produto

**Status:** Approved
**Date:** 2026-10-19
**Deciders:** Product Owner

---

## 1. Context

No modelo original, cada produto tinha um `reference_price` que representava o preço por unidade base de estoque (`base_unit`).

### Problema Identificado

Na prática comercial da Casa Afeto, os produtos são comprados em unidades comerciais que podem diferir da unidade de estoque:

* Uma caixa de barras de cereal contém 20 barras, mas o estoque é gerido por barra (UN);
* Um pacote de café contém 500g, mas o estoque é gerido por grama (G);
* Um fardo de sucos contém 12 garrafas, mas o estoque é gerido por garrafa (UN).

O `reference_price` sozinho não conseguia representar esta diferença entre unidade comercial e unidade de estoque.

### Exemplo do Problema

```
Produto: Barra de cereal
Unidade de estoque: UN (barra)
Compra: 1 caixa com 20 barras por R$40,00

Sem commercial_conversion_factor:
  reference_price = 40.00  →  Errado! O preço é por caixa, não por barra.

Com commercial_conversion_factor:
  reference_price = 40.00  →  Preço da caixa
  commercial_conversion_factor = 20  →  20 barras por caixa
  preço_por_unidade_base = 40.00 / 20 = 2.00  →  Correto!
```

---

## 2. Decision

Adicionar `commercial_conversion_factor` como campo opcional no modelo `Product`.

### Definição

O `commercial_conversion_factor` indica **quantas unidades-base existem na unidade comercial**.

* Se um produto é comprado por caixa e a unidade base é UN: `commercial_conversion_factor = quantidade_por_caixa`
* Se um produto é comprado por pacote de 500g e a unidade base é G: `commercial_conversion_factor = 500`
* Se o produto não tem fator de conversão: `commercial_conversion_factor = NULL` e `reference_price` é o preço por unidade base

### Fórmula

```
preço_por_unidade_base = reference_price / commercial_conversion_factor
```

Quando `commercial_conversion_factor` não está definido:

```
preço_por_unidade_base = reference_price
```

### Impacto no Cálculo de Cestas

O custo de referência da cesta é calculado usando `preço_por_unidade_base` para cada item:

```
custo_referencia = Σ(quantidade × preço_por_unidade_base) para cada item na cesta
```

O preço sugerido da cesta é `2 × custo_referencia` quando todos os itens têm `reference_price` definido.

### Implementação

* Campo `commercial_conversion_factor` adicionado ao modelo `Product` como `Float` opcional;
* Constraint de validação: quando definido, deve ser maior que zero;
* Adicionado em schemas e service;
* Migração de banco de dados criada;
* Teste `test_commercial_conversion_factor.py` criado.

---

## 3. Consequences

### Positive

* Representação correta do preço do produto quando a unidade comercial difere da unidade de estoque;
* Cálculo preciso do custo de referência das cestas;
* Preço sugerido da cesta reflete o custo real dos ingredientes;
* Campo opcional — produtos sem fator de conversão continuam funcionando normalmente.

### Trade-offs

* Nova coluna no banco de dados requer migração;
* Lógica de precificação de cestas precisa considerar o fator de conversão;
* O operador precisa entender a diferença entre unidade comercial e unidade de estoque ao cadastrar produtos.

---

## 4. Alternatives Considered

1. **Manter apenas `reference_price`:** Rejeitado. Não conseguia representar a diferença entre unidade comercial e unidade de estoque.
2. **Adicionar `commercial_unit` como campo separado:** Rejeitado. Adicionaria complexidade sem benefício adicional — o fator numérico é suficiente.
3. **`commercial_conversion_factor` como campo opcional:** Selecionado. Simples, retrocompatível, e cobre o caso de uso principal.

---

## 5. Documentation Updates

* `docs/domain/business-contract.md`: Seção 6.2 adicionada com definição do fator de conversão;
* `docs/domain/business-rules.md`: Regras de precificação atualizadas;
* Modelo `Product` atualizado com novo campo e constraint.
