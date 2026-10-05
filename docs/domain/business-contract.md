# Contrato de Negócio da Casa Afeto

**Versão do documento:** 0.3
**Status:** Ativo

---

## 1. Finalidade

Este documento descreve o comportamento atual de negócio da Casa Afeto que deve orientar o desenvolvimento do Sistema de Gestão de Vendas.

Ele representa decisões de negócio já estabelecidas.

Não é uma especificação de implementação.

Quando forem necessários detalhes de implementação, as especificações de marcos e decisões de arquitetura devem defini-los sem alterar o comportamento de negócio documentado aqui.

---

## 2. Visão Geral do Negócio

Casa Afeto vende cestas de café da manhã personalizadas e cestas de presente.

O fluxo operacional é aproximadamente:

```text
Cliente entra em contato com a Casa Afeto
        ↓
Escolhe uma cesta
        ↓
Cesta é personalizada, se necessário
        ↓
Data de entrega é combinada
        ↓
Pagamento é recebido
        ↓
Cesta é preparada
        ↓
Cesta é entregue
```

O sistema vai suportar esta operação por meio de:

* Produtos
* Estoque
* Templates de Cesta
* Cestas
* Clientes
* Vendas
* Pagamentos

---

## 3. Cliente

Um **Cliente** é a pessoa que realiza a compra.

Um cliente pode comprar uma ou mais cestas ao longo do tempo.

O cliente está associado a uma Venda.

Informações do destinatário não precisam ser representadas como uma entidade separada de Cliente ou Pessoa durante a implementação inicial.

---

## 4. Produto

Um **Produto** é um item que pode ser usado como parte de uma cesta.

Exemplos incluem:

* barras de cereal;
* chocolate;
* suco;
* bolo;
* café;
* canecas;
* cartões;
* materiais de embalagem.

### 4.1 Unidade Base de Estoque

Todo produto possui uma unidade base de estoque (`base_unit`).

`base_unit` é um valor controlado. M1 suporta exatamente:

* `UN` — unidade
* `KG` — quilograma
* `G` — grama
* `L` — litro
* `ML` — mililitro

M1 não implementa conversão genérica de unidades nem um catálogo configurável de unidades. Todas as quantidades de estoque em M1 são expressas na `base_unit` do produto.

### 4.2 Mutabilidade da Unidade Base

A `base_unit` de um produto só pode ser alterada enquanto o produto não possui **nenhuma movimentação de estoque**.

Uma vez que o produto tenha pelo menos uma movimentação de estoque, sua `base_unit` se torna imutável para preservar o significado semântico das movimentações históricas.

### 4.3 Nome do Produto

Nomes de produtos não são **obrigatoriamente únicos** em M1. Dois produtos distintos podem compartilhar o mesmo nome.

A unidade comercial de compra pode diferir da unidade de estoque.

Por exemplo:

```text
Compra:
1 caixa de barras de cereal

Caixa:
24 unidades

Estoque:
+24 UN
```

O fator de conversão pode variar conforme a aquisição.

---

## 5. Ativação do Produto

Produtos podem ser ativados ou desativados.

Um produto desativado não deve ser selecionável para novas atividades operacionais onde produtos ativos são exigidos.

Um produto inativo não pode receber **nenhuma** Entrada ou Ajuste de Estoque. Se um operador precisar modificar o estoque de um produto inativo, o produto deve primeiro ser reativado. A reativação não modifica o estoque.

A desativação não exclui informações históricas envolvendo o produto.

---

## 6. Custo do Produto

Um produto pode ser adquirido a preços diferentes ao longo do tempo.

Exemplo:

```text
Aquisição normal:
Cereal bar = R$ 2,50 / unidade

Aquisição especial:
Cereal bar = R$ 1,80 / unidade
```

Custos históricos de aquisição não devem ser sobrescritos.

O custo do produto, portanto, pertence ao contexto de aquisição/estoque e não deve ser tratado como uma única propriedade permanente do Produto.

O modelo futuro de lote de estoque permitirá que diferentes quantidades do mesmo produto tenham custos de aquisição diferentes.

---

## 7. Compra

Uma **Compra** representa uma aquisição de produtos pela Casa Afeto.

Uma compra contém um ou mais itens de compra.

Um item de compra pode usar uma unidade comercial diferente da unidade de estoque do produto.

Exemplo:

```text
Item de compra:
1 caixa

Conversão:
1 caixa = 24 unidades

Quantidade de estoque:
24 unidades
```

O preço real de aquisição deve ser preservado.

Gestão de compras não faz parte da implementação inicial da Fase 1.

---

## 8. Estoque

Estoque representa o material físico disponível para produtos.

Conceitualmente, o estoque é baseado em movimentações.

Exemplos de movimentações incluem:

```text
Compra / Entrada       +20
Venda / Consumo        -3
Ajuste                 -2
```

O sistema deve preservar o histórico de movimentações de estoque.

O saldo atual é derivado das movimentações relevantes de estoque.

### 8.1 Regras de Quantidade para Entrada de Estoque

Uma `ENTRY` adiciona estoque físico.

Regras:
* quantidade DEVE ser maior que zero (> 0);
* quantidade NÃO DEVE ser zero;
* quantidade NÃO DEVE ser negativa;
* `UN` aceita apenas quantidades inteiras positivas;
* `KG`, `G`, `L` e `ML` aceitam quantidades decimais positivas.

---

## 9. Correção de Estoque

O estoque pode precisar ser corrigido quando a quantidade registrada no sistema difere da quantidade física.

Correções devem preservar as informações históricas.

O sistema não deve reescrever movimentações anteriores de estoque para fazer o histórico parecer diferente.

Em vez disso, uma nova movimentação de ajuste representa a correção.

### 9.1 Regras de Quantidade para Ajuste de Estoque

Um `ADJUSTMENT` representa uma correção no estoque físico:
* quantidade NÃO DEVE ser zero;
* valores positivos aumentam o estoque;
* valores negativos diminuem o estoque;
* `UN` aceita apenas quantidades inteiras;
* `KG`, `G`, `L` e `ML` aceitam quantidades decimais;
* um ajuste negativo nunca deve causar que o saldo físico resultante fique negativo.

Exemplo:

```text
Saldo registrado: 20
Saldo físico: 17

Ajuste:
-3
```

As movimentações originais permanecem inalteradas.

---

## 10. Disponibilidade do Estoque

A disponibilidade do estoque é relevante quando os produtos são usados em cestas e vendas.

Um produto pode ser selecionado para uma cesta mesmo quando o estoque disponível atual é insuficiente.

No entanto, a falta de estoque deve ficar claramente visível ao usuário.

Exemplo:

```text
Disponível: 2
Solicitado: 5
Falta: 3
```

O produto permanece válido, mas o usuário precisa saber que ele não tem estoque suficiente para a operação.

---

## 11. Política para Estoque Negativo

O sistema **não deve permitir que o estoque físico se torne negativo** (`INV-006`).

Esse invariante é absoluto. Uma movimentação de estoque nunca deve ser criada se fizer com que o saldo de estoque físico disponível de um produto se torne negativo.

Além disso, esse invariante **deve ser mantido durante operações concorrentes de estoque**. Modificações simultâneas que afetem o estoque do mesmo produto devem ser executadas transacionalmente, serializando a validação e a inserção da movimentação (`ADR-001`).

Por exemplo:

```text
Estoque:
Chocolate = 1

Consumo necessário:
Chocolate × 3
```

O sistema não deve criar:

```text
Chocolate = -2
```

Em vez disso, a falta deve ser identificada e a operação rejeitada.

A distinção entre planejamento comercial e estoque físico é importante.

### Composição de Cesta/Venda

Uma cesta ou venda pode conter um produto para o qual não há estoque suficiente.

Isso representa uma necessidade futura.

### Movimentação de Estoque

Uma dedução de estoque físico só pode ocorrer quando houver estoque suficiente.

Portanto:

```text
Criação da cesta
    ↓
Pode conter produto sem estoque suficiente
    ↓
Aviso exibido
    ↓
Estoque permanece inalterado
```

e:

```text
Confirmação da venda
    ↓
Estoque necessário verificado
    ↓
Há estoque suficiente?
    ├── Sim → deduzir estoque
    └── Não → bloquear confirmação
```

Uma venda não pode ser confirmada enquanto não for possível atender ao estoque necessário.

Esta política não exige que o sistema implemente reposição automática.

Uma funcionalidade futura poderá identificar produtos que precisam ser comprados para atender às vendas pendentes.

---

# 12. Lotes de Estoque

O modelo futuro de estoque deve oferecer suporte a vários lotes do mesmo produto.

Lotes diferentes podem ter:

* custos de aquisição diferentes;
* quantidades diferentes;
* datas de vencimento diferentes.

Exemplo:

```text
Chocolate

Lote A
Quantidade: 10
Custo unitário: R$ 2,50
Vencimento: 2026-11-10

Lote B
Quantidade: 20
Custo unitário: R$ 1,80
Vencimento: 2026-10-20
```

A política de negócio provisória atual é preferir o lote com vencimento mais próximo ao selecionar estoque para consumo.

Conceitualmente, isso é semelhante a FEFO.

Esta política é provisória e poderá mudar conforme o negócio evoluir.

A gestão de lotes não faz parte da implementação inicial da Fase 1.

---

# 13. Template de Cesta

Um **Template de Cesta** representa uma composição padrão reutilizável para uma cesta.

Um template contém produtos e quantidades.

Exemplo:

```text
Clássica de Café da Manhã

Café × 1
Suco × 1
Chocolate × 2
Bolo × 1
```

Templates podem ser ativados ou desativados.

---

# 14. Cesta

Uma **Cesta** é uma cesta concreta preparada para uma venda específica.

Uma cesta pode:

* ser criada a partir de um template;
* ser criada sem um template;
* ter sua composição personalizada;
* conter várias unidades do mesmo produto.

Exemplo:

```text
Chocolate × 3
Suco × 1
Bolo × 1
```

Não é obrigatório que uma cesta mantenha a mesma composição de seu template.

---

# 15. Independência entre Cesta e Template

Quando uma cesta é criada a partir de um template, ela recebe sua própria composição concreta.

Alterações futuras no template não devem modificar cestas existentes.

Exemplo:

```text
Template:
Chocolate × 2
Suco × 1

        ↓

Cesta:
Chocolate × 2
Suco × 1

        ↓ template alterado

Template:
Chocolate × 1
Suco × 2
```

A cesta existente permanece:

```text
Chocolate × 2
Suco × 1
```

---

# 16. Personalização da Cesta

Uma cesta concreta pode ser personalizada após sua criação.

A personalização pode incluir:

* adicionar um produto;
* remover um produto;
* alterar a quantidade;
* substituir um produto.

A personalização pode ser necessária por causa de:

* preferência do cliente;
* disponibilidade de produtos;
* decisões operacionais.

Uma cesta pode conter um produto mesmo quando o estoque atual é insuficiente, desde que a falta esteja visível.

---

# 17. Cesta sem Template

Uma cesta pode ser criada sem usar um Template de Cesta.

Isso permite que a Casa Afeto crie cestas personalizadas ou excepcionais sem antes criar um template reutilizável.

---

# 18. Custo da Cesta

O custo de uma cesta é determinado pelos produtos e quantidades que a compõem.

Como os custos de aquisição dos produtos podem variar, o cálculo do custo deverá, futuramente, considerar o contexto relevante de estoque/aquisição.

A estratégia detalhada de seleção de lotes e cálculo de custos será especificada quando os lotes de estoque forem implementados.

---

# 19. Precificação da Cesta

Atualmente, a Casa Afeto usa aproximadamente 2× o custo dos produtos como referência comum de precificação.

Isso é uma **sugestão**, não uma regra obrigatória de precificação.

Conceitualmente:

```text
Custo da Cesta
    ↓
Preço Sugerido
    ↓
Preço Final de Venda
```

O usuário pode definir manualmente o preço final de venda.

Exemplo:

```text
Custo:             R$ 85
Preço sugerido:    R$ 170

Possíveis preços finais:
R$ 155
R$ 170
R$ 185
```

O preço final de venda é controlado pelo usuário.

Se a composição da cesta mudar, o custo e o preço sugerido devem ser recalculados.

O preço final pode continuar sendo controlado/sobrescrito manualmente.

---

# 20. Venda

Uma **Venda** representa uma transação comercial com um Cliente.

Uma venda contém:

* um Cliente;
* uma ou mais Cestas;
* informações no nível da venda;
* informações de pagamento associadas à venda.

Uma venda deve conter pelo menos uma cesta.

Uma venda pode conter várias cestas.

---

# 21. Informações de Entrega da Cesta

Cada cesta pode ter suas próprias informações de entrega/destinatário.

Isso inclui, conforme necessário:

* destinatário;
* endereço de entrega;
* data de entrega;
* observações relevantes.

Várias cestas na mesma venda podem compartilhar o mesmo endereço.

O destinatário não precisa ser modelado como uma entidade Cliente independente durante a implementação inicial.

---

# 22. Ciclo de Vida da Venda

O ciclo de vida operacional da venda é representado por status.

O modelo inicial de status é:

```text
DRAFT
  ↓
CONFIRMED
  ↓
PREPARING
  ↓
READY
  ↓
DELIVERED
```

Uma venda também pode se tornar:

```text
CANCELLED
```

A implementação exata das transições de status pertence à especificação do marco relevante.

Os status representam o estado operacional e não devem ser confundidos com o estado do pagamento.

---

# 23. Venda em Rascunho

Uma venda em rascunho representa uma venda em preparação que ainda não foi confirmada.

Uma venda em rascunho pode ser alterada.

A criação de uma venda em rascunho não deduz estoque.

---

# 24. Confirmação da Venda

Uma venda é confirmada quando as condições de negócio necessárias são atendidas.

A exigência de pagamento é:

> Uma venda é confirmada quando pelo menos 50% de seu valor total tiver sido pago.

Exemplo:

```text
Total da venda: R$ 200

Pago:
R$ 100

Percentual pago:
50%

Resultado:
A venda pode ser confirmada.
```

A disponibilidade de estoque também é obrigatória.

Uma venda não pode ser confirmada se não for possível atender ao estoque necessário.

Portanto:

```text
Requisitos para confirmação

Pelo menos 50% pago
        E
Estoque necessário disponível
        ↓
A venda pode ser confirmada
```

---

# 25. Dedução de Estoque na Confirmação da Venda

Quando uma venda é confirmada, o estoque necessário é deduzido.

Exemplo:

```text
Antes da confirmação:

Chocolate = 20
Suco      = 8

Venda:

Chocolate × 2
Suco × 1

Após a confirmação:

Chocolate = 18
Suco      = 7
```

A dedução representa o consumo/compromisso físico do estoque para a venda confirmada.

O sistema nunca deve criar uma movimentação que faça o estoque físico ficar negativo.

---

# 26. Alterações Após a Confirmação

Uma venda confirmada pode ser modificada.

Quando a composição da cesta mudar após a confirmação, o estoque deve ser ajustado de acordo com a diferença entre a composição original e a nova.

Exemplo:

```text
Original:

Chocolate × 2
Suco × 1

Nova:

Biscoito × 2
Suco × 1
```

Ajuste de estoque:

```text
Chocolate +2
Biscoito  -2
```

A movimentação original de estoque permanece no histórico.

O sistema não deve reescrever a movimentação original.

Se não for possível atender à nova composição por falta de estoque, o sistema não deve criar uma movimentação de estoque negativo.

---

# 27. Cancelamento da Venda

Uma venda confirmada pode ser cancelada posteriormente.

Uma venda cancelada não deve ser excluída.

Suas informações históricas devem permanecer disponíveis.

O cancelamento não implica automaticamente que 100% do estoque anteriormente deduzido retorne ao estoque.

A situação física deve determinar o que realmente aconteceu.

Por exemplo:

```text
Produto devolvido fisicamente
    → pode ser adicionado novamente ao estoque

Produto consumido
    → permanece consumido

Produto perdido/danificado
    → pode exigir um ajuste
```

O tratamento detalhado de perdas, devoluções e vencimentos está fora do escopo inicial da Fase 1.

---

# 28. Pagamento

O sistema oferece suporte aos seguintes métodos de pagamento:

* PIX;
* Cartão.

Uma venda pode ter um ou mais registros de pagamento.

As informações de pagamento devem ser acompanhadas separadamente do status operacional da venda.

---

# 29. Comprovante de Pagamento

Um pagamento pode ter um comprovante associado.

O comprovante permite que a Casa Afeto documente o pagamento recebido.

O comportamento exato de armazenamento e tratamento de arquivos será definido pela especificação de implementação relevante.

---

# 30. Separação entre Status do Pagamento e da Venda

O status do pagamento e o status da venda são conceitos separados.

Por exemplo:

```text
Venda:
CONFIRMED

Pagamento:
50% pago
50% pendente
```

Portanto, uma venda pode ser confirmada enquanto ainda houver um saldo pendente.

---

# 31. Regra de Pagamento para Entrega

O saldo restante deve ser integralmente pago antes da entrega.

Portanto:

```text
Confirmada
    ↓
Saldo pendente
    ↓
Pagamento restante
    ↓
100% pago
    ↓
Entrega
```

Uma venda não deve ser entregue enquanto houver saldo pendente.

---

# 32. Venda de Produtos Individuais

Vendas de produtos individuais estão fora do escopo inicial.

O modelo atual de vendas é centrado em cestas.

O sistema não deve implementar um fluxo separado de venda de produtos, a menos que seja introduzido um requisito de negócio concreto.

---

# 33. Produtos Produzidos Internamente

A Casa Afeto pode produzir produtos internamente, como bolos.

Atualmente, o negócio não tem um processo de produção suficientemente definido para formalizar essa área.

Funcionalidades futuras de produção podem envolver:

* receitas;
* ingredientes;
* quantidades produzidas;
* custos de produção;
* vencimento;
* movimentações de estoque da produção.

Essas capacidades estão fora do escopo inicial.

A arquitetura atual não deve implementá-las prematuramente.

---

# 34. Perdas, Quebras, Vencimentos e Uso Interno

No futuro, produtos podem ser:

* perdidos;
* danificados;
* vencidos;
* consumidos internamente;
* usados por motivos que não sejam uma venda.

As regras de negócio para essas situações ainda não estão totalmente definidas.

O modelo de estoque deve permitir que tipos futuros de movimentação representem essas situações.

Fluxos detalhados devem ser introduzidos somente quando os requisitos de negócio correspondentes estiverem definidos.

---

# 35. Datas Afetivas

A Casa Afeto pretende, futuramente, manter datas relevantes associadas a clientes ou destinatários.

Exemplos:

* aniversário;
* aniversário de casamento;
* outras datas importantes.

Uma funcionalidade futura poderá usar essas datas para apoiar o contato proativo com clientes e o envio de lembretes.

Essa funcionalidade está fora do escopo inicial da Fase 1.

---

# 36. Regras de Negócio Estabelecidas

As regras a seguir foram estabelecidas explicitamente.

### BASKET-001 — Criação de Cesta

Uma cesta pode ser criada a partir de um template ou sem um template.

### BASKET-002 — Quantidades Múltiplas de Produtos

Uma cesta pode conter várias unidades do mesmo produto.

### BASKET-003 — Independência entre Cesta e Template

Alterar um Template de Cesta não deve modificar cestas existentes criadas a partir desse template.

### BASKET-004 — Personalização de Cesta

Uma cesta concreta pode ser personalizada após sua criação.

### SALE-001 — Venda Exige Cesta

Uma venda deve conter pelo menos uma cesta.

### SALE-002 — Várias Cestas por Venda

Uma venda pode conter várias cestas.

### SALE-003 — Modificação de Venda Confirmada

Uma venda confirmada pode ser modificada.

### SALE-004 — Preservação de Venda Cancelada

Uma venda cancelada deve ser preservada, não excluída.

### SALE-005 — Diferença de Estoque Após Confirmação

Alterações em uma venda confirmada devem ajustar o estoque de acordo com a diferença de composição.

### PAY-001 — Métodos de Pagamento Suportados

Os métodos de pagamento suportados são PIX e Cartão.

### PAY-002 — Limite para Confirmação da Venda

Uma venda pode ser confirmada quando pelo menos 50% de seu valor total tiver sido pago.

### PAY-003 — Pagamento Integral Antes da Entrega

Uma venda deve estar integralmente paga antes da entrega.

### INV-001 — Estoque Baseado em Movimentações

As alterações de estoque são representadas por meio de movimentações de estoque.

### INV-002 — Preservação do Histórico de Estoque

Correções de estoque devem preservar o histórico original de movimentações.

### INV-003 — Seleção Permitida com Estoque Insuficiente

Um produto com estoque insuficiente pode ser selecionado para uma cesta ou venda antes da confirmação, desde que a falta seja claramente indicada.

### INV-004 — Dedução de Estoque na Confirmação

Uma venda confirmada gera as deduções de estoque necessárias.

### INV-005 — Diferença de Estoque em Alterações de Venda Confirmada

Alterações em uma venda confirmada geram ajustes de estoque com base na diferença de composição.

### INV-006 — Proibição de Estoque Físico Negativo

O sistema não deve criar uma movimentação de estoque que faça o saldo de estoque físico disponível de um produto se tornar negativo. Esse invariante é absoluto e se aplica estritamente a operações de estoque concorrentes (`ADR-001`).

### INV-007 — Confirmação Exige Estoque Disponível

Uma venda não pode ser confirmada enquanto não for possível atender ao estoque necessário.

### INV-008 — Produtos Inativos Não Podem Receber Operações de Estoque

Um produto inativo não pode receber nenhuma Entrada ou Ajuste de estoque. O produto deve ser reativado antes de modificar o estoque. A reativação não altera o estoque.

### PROD-001 — Unidades Base Controladas e Mutabilidade

A `base_unit` de um produto é um valor controlado e deve ser um destes: `UN`, `KG`, `G`, `L`, `ML`. A `base_unit` só pode ser editada enquanto o produto não tiver movimentações de estoque. Depois que houver uma movimentação, a `base_unit` será imutável.

### PROD-002 — Nome do Produto Não Exclusivo

Os nomes dos produtos não precisam ser exclusivos em M1. Vários produtos podem ter o mesmo nome.

### SEARCH-001 — Semântica da Busca de Produtos

A busca de produtos não diferencia maiúsculas de minúsculas e corresponde a substrings do nome do produto. Funcionalidades avançadas de busca (busca aproximada, classificação, índice de texto completo) estão fora do escopo.

---

# 37. Decisões de Negócio em Aberto

Os tópicos a seguir permanecem intencionalmente sem resolução e não devem ser transformados em suposições pela implementação.

### Custo do Estoque/Seleção de Lotes

A estratégia provisória é preferir o lote com vencimento mais próximo ao consumir estoque.

A implementação exata do cálculo de custos será definida quando a gestão de lotes for introduzida.

### Gestão de Compras

Fluxos detalhados de compra, informações de fornecedores, documentos de compra e campos relacionados ainda não foram definidos.

### Produção Interna

O processo de produção para produtos feitos internamente ainda não foi definido.

### Tratamento de Perdas e Vencimentos

Fluxos detalhados para perdas, danos, vencimentos e consumo interno ainda não foram definidos.

---

# 38. Oportunidades de Negócio Futuras

As capacidades a seguir poderão ser consideradas após a estabilização do sistema operacional central:

* gestão de compras;
* lotes de estoque;
* acompanhamento de vencimentos;
* consumo de estoque baseado em FEFO;
* alertas de vencimento;
* gestão de reposição;
* datas afetivas;
* lembretes para clientes;
* integrações de comunicação;
* produção interna;
* receitas;
* precificação avançada;
* gestão do relacionamento com clientes;
* painéis operacionais;
* relatórios avançados.

Essas oportunidades não devem ser implementadas apenas por constarem neste documento.

Cada capacidade futura exige sua própria decisão de negócio e escopo de implementação.

---

# 39. Política de Mudanças

Este documento representa o entendimento atual do negócio.

As regras de negócio podem mudar conforme a Casa Afeto usa o sistema e descobre novos requisitos.

Quando uma regra de negócio mudar:

1. A mudança deve ser identificada explicitamente.
2. Este documento deve ser atualizado.
3. As especificações dos marcos afetados devem ser revisadas.
4. A implementação existente deve ser avaliada quanto ao impacto.
5. Os testes devem ser atualizados quando necessário.
6. Os dados históricos devem ser considerados antes de introduzir mudanças destrutivas.

O agente não deve alterar silenciosamente o comportamento de negócio com base em suposições.

---

# 40. Princípio Orientador de Negócio

O sistema existe para apoiar a operação real da Casa Afeto.

Portanto:

> **O comportamento de negócio deve ser explícito, as informações históricas devem ser preservadas e o sistema deve permanecer simples o bastante para evoluir conforme o negócio aprende.**

O sistema deve modelar o que a Casa Afeto decidiu fazer hoje sem implementar prematuramente tudo o que a Casa Afeto talvez queira fazer no futuro.
