# Contrato de Negócio da Casa Afeto

**Versão do documento:** 0.6
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

### 6.1 Preço de Referência

Um produto pode ter um **preço de referência** (`reference_price`), que é uma propriedade comercial definida deliberadamente pelo Casa Afeto. O preço de referência não varia automaticamente conforme o preço pago em uma compra. Ele pode ser definido antes do produto existir fisicamente no estoque. Quando ausente, o produto não pode participar de um cálculo confiável de precificação de cestas até que o valor seja definido.

O `reference_price` representa o **preço da unidade comercial** do produto — ou seja, o preço da caixa, pacote ou saco que o operador compra. Por exemplo, uma caixa de chocolate com 12 unidades pode ter `reference_price = R$59,90`.

### 6.2 Fator de Conversão Comercial

Um produto pode ter um **fator de conversão comercial** (`commercial_conversion_factor`), que indica quantas unidades-base existem na unidade comercial.

Exemplo:

```text
Produto: Chocolate
Unidade base: UN
Preço de referência: R$ 59,90 (preço da caixa)
Fator de conversão: 12 (1 caixa = 12 unidades)

Preço por unidade-base = 59,90 / 12 = R$ 4,99
```

Quando o fator de conversão está definido, o sistema calcula o preço por unidade-base como:

```
preço_unidade_base = reference_price / commercial_conversion_factor
```

Quando o fator de conversão **não** está definido, o `reference_price` já é considerado o preço por unidade-base.

O fator de conversão deve ser maior que zero. Valores negativos ou zero são rejeitados.

### 6.3 Uso na Precificação de Cestas

O cálculo do custo de referência da cesta e do preço sugerido usa o **preço por unidade-base** de cada produto, não o `reference_price` bruto.

Exemplo:

```text
Template com:
- 2 unidades de chocolate (reference_price=R$59,90, fator=12)
- 3 unidades de croissant (reference_price=R$63,98, fator=10)

Preço por unidade-base:
- Chocolate: 59,90 / 12 = R$ 4,99
- Croissant: 63,98 / 10 = R$ 6,40

Custo de referência da cesta:
(2 × 4,99) + (3 × 6,40) = 9,98 + 19,20 = R$ 29,18

Preço sugerido:
2 × 29,18 = R$ 58,36
```

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
Confirmação financeira da venda
    ↓
Reserva de estoque acionada (seção 37)
    ↓
Baixa física no início da preparação (seção 37)
```

A política de reserva e baixa de estoque associada às vendas está formalizada na seção 37. A confirmação financeira aciona a reserva, e a baixa física ocorre no início da preparação.

A autorização financeira da transição `RASCUNHO → CONFIRMADA` pertence ao M5, conforme as regras de pagamento e de dados obrigatórios de entrega já aprovadas.

Esta seção não deve ser interpretada como autorização para deduzir estoque automaticamente na confirmação da venda — a baixa física ocorre no início da preparação, conforme a política aprovada.

A política de estoque negativo (`INV-006`) aplica-se a todas as movimentações de estoque, incluindo as baixas físicas definidas na seção 37.

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

Um **Template de Cesta** é a **cesta-base** — o molde reutilizável que define a composição padrão e o preço de venda de uma cesta.

O Template é a **origem comercial** de uma venda. Ao adicionar uma cesta a uma venda, a composição e o preço do Template são copiados para a cesta da venda (`SaleBasket`), que passa a ser independente.

Um template possui um nome, uma composição de produtos e quantidades, um preço de venda e um estado ativo/inativo. Um template novo nasce ativo por padrão; não há estado DRAFT no M2.

Um template pode ser salvo sem itens e editado posteriormente. Um template ativo vazio não pode ser usado para criar uma cesta em venda até possuir ao menos um item.

Templates podem ser criados, consultados, editados, ativados e desativados. Um template inativo continua persistido e consultável, mas não pode ser usado para criar uma cesta em venda.

Um template que contenha um produto inativo não pode ser usado para criar uma cesta em venda até que a composição seja corrigida explicitamente pelo usuário. A referência ao produto inativo permanece no template e não é removida nem substituída automaticamente.

Cada produto aparece no máximo uma vez na composição. Ao incluir novamente produto que já exista no template, sua quantidade é incrementada. Ao substituir item por produto já presente, as quantidades são agregadas na linha única do produto.

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

# 14. Cesta Concreta (removida)

A entidade "Cesta concreta" foi removida do projeto. Não há caso de uso real para uma cesta persistida fora do contexto de venda.

Existem apenas **2 tipos de cestas**:

1. **Template de Cesta** — o molde reutilizável com composição + preço
2. **Cesta da Venda** (`SaleBasket`) — a concretização do template na venda, editável sem alterar o template

**A personalização comercial acontece na cesta da venda (`SaleBasket`).**

---

# 15. Independência entre Template e Cesta da Venda

Quando uma cesta é adicionada a uma venda a partir de um Template, a composição e o preço são copiados naquele momento. O `origin_template_id` opcional identifica apenas a origem; não é uma referência viva à composição.

Alterações futuras no Template não adicionam, removem ou alteram produtos, quantidades ou preços das cestas já adicionadas a vendas. Alterações na cesta da venda também não modificam o Template.

Exemplo:

```text
Template:
Chocolate × 2
Suco × 1
Preço: R$ 50,00

        ↓ adicionado à venda

Cesta da Venda:
Chocolate × 2
Suco × 1
Preço: R$ 50,00

        ↓ template alterado

Template:
Chocolate × 1
Suco × 2
Preço: R$ 60,00
```

A cesta da venda existente permanece:

```text
Chocolate × 2
Suco × 1
Preço: R$ 50,00
```

A cesta da venda pode ser personalizada independentemente: adicionar itens, remover itens, alterar quantidades — sem afetar o Template.

---

# 16. Personalização da Cesta da Venda

A personalização comercial acontece na **cesta da venda** (`SaleBasket`), não na Cesta concreta do M2.

Quando uma cesta é adicionada a uma venda a partir de um Template, o operador pode personalizar a composição da cesta da venda:

* adicionar um produto;
* remover um produto;
* alterar a quantidade;
* substituir um produto.

A personalização pode ser necessária por causa de:

* preferência do cliente;
* disponibilidade de produtos;
* decisões operacionais.

A personalização da cesta da venda segue as regras de alteração de composição por estado definidas na seção 26.

Uma cesta da venda pode conter um produto mesmo quando o estoque atual é insuficiente, desde que a falta esteja visível.

Uma cesta da venda que contenha um produto posteriormente desativado continua persistida e editável. O item não é removido automaticamente. O usuário pode mantê-lo na composição ou removê-lo e pode editar os demais itens. Um produto inativo não pode ser incluído em novas composições. A interface deve identificar claramente o produto inativo já presente. Não há substituição automática; substituir é uma ação explícita por outro produto ativo.

O usuário também pode alterar a quantidade de um item já existente cujo produto foi desativado. Cada produto aparece no máximo uma vez por composição; incluir novamente um produto ativo já presente incrementa sua quantidade. Ao substituir item por produto já presente, as quantidades são agregadas em uma única linha.

---

# 17. Venda sem Template

Uma cesta pode ser adicionada a uma venda sem usar um Template de Cesta.

Isso permite que a Casa Afeto crie cestas personalizadas ou excepcionais diretamente na venda, sem antes criar um template reutilizável.

A cesta da venda criada sem Template possui `origin_template_id = NULL`.

---

# 18. Unidade base e identificação de produtos nas composições

As composições de templates e cestas referenciam produtos por sua identidade (`product_id`), não pelo nome. Renomear um produto não cria outro produto, não duplica referências, não altera quantidades e não cria histórico de nomes no M2. A interface pode apresentar o nome atual do produto.

A referência em uma composição não é uma movimentação de estoque. Portanto, ela não impede a alteração da unidade base que o M1 permite enquanto o produto não possui movimentações. A quantidade armazenada continua sendo interpretada na unidade base atual do produto; M2 não converte quantidades nem mantém histórico de unidades.

Templates e cestas podem conter produtos sem estoque suficiente. A disponibilidade é informativa; sua consulta não reserva estoque, não altera saldo e não cria movimentações. M2 não realiza dedução de estoque.

---

# 19. Custo e precificação

1. **Custo de aquisição nas entradas:** nas entradas de estoque (tipo ENTRY), é registrado opcionalmente o custo unitário de aquisição do produto com precisão de duas casas decimais. Valores negativos são rejeitados.
2. **Custo médio ponderado (controle interno):** o custo médio unitário do produto é calculado ponderando quantidades e custos das entradas com custo registrado. Custos desconhecidos (ausentes) são ignorados no cálculo da média e não são tratados como zero. Este valor é mantido para controle interno de custos e não é usado para precificação de cestas.
3. **Custo de referência da cesta:** obtido pela soma de `quantidade × preço_por_unidade_base` de cada produto na composição, onde `preço_por_unidade_base = reference_price / commercial_conversion_factor` (ou `reference_price` quando o fator não está definido). Se algum produto não possuir `reference_price` definido, o custo de referência da cesta é considerado indisponível / não confiável.
4. **Preço sugerido:** calculado como 2 × custo de referência da cesta quando todos os itens possuem `reference_price` definido e a composição não está vazia.
5. **Autonomia de precificação e persistência:** o preço de venda da cesta é definido ou aceito pelo operador. O preço salvo não é sobrescrito automaticamente quando o preço de referência muda. Ao editar a composição ou solicitar nova sugestão, o custo de referência e a sugestão são recalculados dinamicamente sem alterar o preço já fixado.
6. **Precisão monetária:** o preço possui precisão de duas casas decimais. Valores negativos são estritamente rejeitados. O preço zero (`0.00`) é permitido para brindes/cortesias e é semanticamente distinto de preço não informado (`null`).
7. **Preservação de registros preexistentes:** registros históricos existentes de movimentações e composições são preservados sem custos retroativos fictícios.


---

# 20. Venda

Uma **Venda** representa a transação comercial operacional vinculada a um Cliente.

Uma venda contém:

* um Cliente;
* uma ou mais cestas da venda;
* um estado operacional;
* um total calculado a partir dos preços registrados das cestas;
* histórico operacional aplicável.

Uma nova venda só pode ser criada e salva quando vinculada a um cliente ativo.

Se o cliente se tornar inativo depois da criação, o vínculo da venda existente é preservado. Isso não autoriza a criação de novas vendas para clientes inativos.

Os detalhes funcionais de M4 pertencem a:

```text
docs/milestones/m4-sales/specification.md
```

---

# 21. Cestas da Venda e Informações de Entrega

Uma venda pode conter várias cestas, inclusive várias baseadas na mesma origem.

Cada cesta da venda possui, de forma independente:

* composição;
* destinatário;
* endereço de entrega;
* data de entrega;
* horário de entrega;
* preço acordado registrado.

Várias cestas da mesma venda podem compartilhar o mesmo endereço, mas isso não elimina sua independência operacional.

O destinatário não precisa ser modelado como entidade independente na implementação inicial.

---

# 22. Composição e Preço Acordado da Cesta na Venda

Ao adicionar uma cesta à venda, a composição e o preço do Template de origem são copiados naquele momento e passam a ser independentes do Template.

O preço vigente do Template é copiado no momento da adição.

Alterações posteriores na cesta da venda não modificam o Template. Alterações posteriores no Template também não modificam a cesta já adicionada à venda.

O preço acordado de cada cesta pode ser ajustado manualmente somente enquanto a venda estiver em `RASCUNHO`.

Alterações de composição não recalculam automaticamente o preço acordado.

Renegociações excepcionais posteriores à confirmação não fazem parte do fluxo normal do M4.

---

# 23. Total da Venda

O total da venda é a soma dos preços registrados de todas as cestas que a compõem.

Esse total deve ser recalculado quando os preços registrados das cestas mudarem.

Alterar a composição de uma cesta sem alterar seu preço não recalcula automaticamente o total.

---

# 24. Ciclo Operacional da Venda

Os estados operacionais oficiais da venda são:

```text
RASCUNHO
   ↓
CONFIRMADA
   ↓
EM PREPARAÇÃO
   ↓
PRONTA
   ↓
ENTREGUE
```

Uma venda também pode se tornar:

```text
CANCELADA
```

Os estados representam o ciclo operacional da venda e não se confundem com o estado dos pagamentos.

No fluxo normal, a venda não deve pular etapas.

`CONFIRMADA → EM PREPARAÇÃO` exige ação explícita do usuário.

`PRONTA → EM PREPARAÇÃO` só ocorre por reabertura explícita, auditável e com justificativa.

---

# 25. `RASCUNHO` e Confirmação Financeira

`RASCUNHO` é o estado inicial da venda.

Uma venda em `RASCUNHO` pode ser alterada e pode ter dados de entrega incompletos.

Antes da confirmação financeira, todas as cestas precisam ter destinatário, endereço, data e horário de entrega preenchidos.

A transição `RASCUNHO → CONFIRMADA` faz parte do contrato funcional da venda, mas sua autorização financeira pertence ao marco de pagamentos.

No modelo aprovado para a Fase 1:

* o M4 define a estrutura e as restrições operacionais da venda;
* o M5 registra pagamentos;
* o M5 verifica se o total pago atingiu pelo menos 50% do valor da venda;
* o M5 autoriza a transição financeira para `CONFIRMADA`.

O M4 não registra pagamentos, não calcula valores pagos e não implementa uma segunda lógica independente de confirmação financeira.

**Relação entre confirmação financeira e estado operacional:** O modelo atual de estados operacionais é mantido sem criar um novo estado persistido. `RASCUNHO` permanece como estado da venda enquanto a confirmação financeira não tiver sido efetivada, mesmo quando os dados de entrega estiverem completos e houver pagamentos registrados. A confirmação financeira só pode ser efetivada quando o pagamento registrado atingir pelo menos 50% do valor da venda e a reserva integral de estoque for concluída com sucesso, conforme a operação atômica definida na seção 37 (RES-001). Se faltar estoque para reservar integralmente, a venda permanece em `RASCUNHO`, o pagamento recebido permanece registrado e o sistema informa os produtos e as quantidades faltantes. A interface pode comunicar que a venda aguarda confirmação financeira por insuficiência de estoque, sem criar um novo estado persistido. O M4 não pode efetivar a confirmação financeira independentemente do M5.

---

# 26. Alterações de Composição por Estado

Em `CONFIRMADA`, é permitido adicionar itens, remover itens e alterar quantidades na composição das cestas da venda.

Em `EM PREPARAÇÃO`, as mesmas alterações continuam permitidas, mas exigem confirmação explícita antes do salvamento, com aviso de que itens podem já ter sido separados ou preparados.

Em `PRONTA`, alterações diretas de composição ficam bloqueadas até reabertura explícita da venda.

Vendas `ENTREGUE` ou `CANCELADA` não aceitam alterações comerciais de composição pelo fluxo normal.

Toda alteração de composição deve preservar histórico não apagável pelo fluxo normal, registrando composição anterior, composição nova, identificador textual do operador responsável e data/hora. A ausência do identificador textual bloqueia o salvamento da alteração.

Alterar composição não altera automaticamente o preço acordado.

Quando uma venda possui reserva ou baixa ativa, as alterações de composição seguem a política de diferença definida na seção 37:

- Adições e aumentos exigem reserva atômica da diferença de quantidades. Se a venda já iniciou a preparação, a baixa física da diferença ocorre quando o operador marca explicitamente como preparada a cesta cuja composição foi alterada, sem repetir baixas anteriores.
- Reduções e remoções liberam somente as quantidades ainda reservadas. Quantidades já baixadas fisicamente não geram entradas automáticas de estoque nem são consideradas recuperadas por inferência.

---

# 27. Preparação por Cesta e Venda `PRONTA`

Cada cesta pode ser marcada individualmente como preparada.

A preparação é uma condição operacional. Ela não representa entrega.

A venda só passa para `PRONTA` quando todas as suas cestas estiverem marcadas como preparadas.

Se a composição de uma cesta mudar durante `EM PREPARAÇÃO`, sua marcação anterior de preparação é invalidada.

Cestas não alteradas preservam sua preparação concluída.

A transição `CONFIRMADA → EM PREPARAÇÃO` inicia a baixa física de todos os produtos da venda, conforme a política de reserva e baixa definida na seção 37. A baixa é atômica e não permite estoque negativo. A entrega subsequente de cestas não executa nova movimentação de estoque.

Quando a composição de uma cesta é alterada durante `EM PREPARAÇÃO` e a cesta é marcada como preparada, a baixa física das quantidades adicionais reservadas ocorre nesse momento, atomicamente com a liberação das reservas correspondentes. Se a baixa física falhar ou não houver estoque físico suficiente, a cesta não pode ser marcada como preparada e não pode ocorrer baixa parcial nem atualização parcial das reservas.

---

# 28. Reabertura de Venda `PRONTA`

Uma venda `PRONTA` pode ser reaberta somente por ação explícita do usuário.

A justificativa e o identificador textual do operador responsável são obrigatórios.

O registro de auditoria da reabertura deve incluir, no mínimo:

* justificativa obrigatória;
* identificador textual do operador responsável;
* data/hora da reabertura.

A ausência de justificativa ou de identificador textual bloqueia a reabertura. O identificador textual é uma declaração operacional fornecida na interface e não pressupõe autenticação de usuários.

A reabertura retorna a venda para `EM PREPARAÇÃO`.

Por si só, a reabertura não altera preços, não cancela a venda e não executa ajustes automáticos de estoque.

A reabertura não repete baixas físicas já realizadas durante a preparação anterior, conforme a política de reserva e baixa definida na seção 37.

---

# 29. Entrega por Cesta e Venda `ENTREGUE`

Cada cesta é marcada como entregue por ação explícita do usuário.

Data e horário agendados não constituem prova de entrega.

Cada registro de entrega deve identificar obrigatoriamente:

* a cesta entregue;
* o identificador textual do operador responsável pelo registro;
* a data/hora do registro.

A submissão sem o identificador textual do responsável é rejeitada pela validação. O identificador textual constitui declaração operacional sem autenticação.

Quando todas as cestas da venda estiverem entregues, o status da venda muda automaticamente para `ENTREGUE`.

O fluxo normal do M4 não inclui assinatura, fotografia ou comprovante adicional de entrega.

---

# 30. Cancelamento da Venda

O cancelamento é permitido em `RASCUNHO`, `CONFIRMADA`, `EM PREPARAÇÃO` e `PRONTA`, desde que nenhuma cesta tenha sido entregue.

Se qualquer cesta já tiver sido entregue, o cancelamento pelo fluxo normal é bloqueado, mesmo que outras cestas permaneçam pendentes.

Cestas já preparadas não impedem o cancelamento quando nenhuma entrega foi registrada.

Uma venda cancelada não deve ser excluída.

Venda, cestas e históricos devem permanecer preservados.

O cancelamento segue a política de reserva e baixa definida na seção 37:

* Antes do início da preparação: a reserva integral é liberada sem movimentação física fictícia.
* Após o início da preparação: as reservas remanescentes são liberadas, exige-se conferência dos produtos já baixados fisicamente, e somente as quantidades fisicamente recuperadas e aproveitáveis são reintegradas mediante movimentação registrada.

O histórico, o responsável e o motivo do cancelamento são preservados.

Uma venda `ENTREGUE` não pode ser cancelada pelo fluxo normal.

---

# 31. Pagamentos

Pagamentos pertencem ao escopo funcional do M5.

O negócio pode registrar um ou mais pagamentos vinculados a uma venda, mantendo as informações financeiras separadas do estado operacional da venda.

O contrato de negócio aprovado para a confirmação é:

> A autorização financeira da transição `RASCUNHO → CONFIRMADA` depende de pagamento de pelo menos 50% do valor total da venda e da validação dos dados obrigatórios de entrega de todas as cestas.

As regras detalhadas de pagamento e sua futura especificação pertencem ao marco correspondente.

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

### BASKET-005 — Cesta concreta removida

A entidade "Cesta concreta" foi removida do projeto. Existem apenas Template de Cesta (molde reutilizável) e Cesta da Venda (SaleBasket). A personalização comercial acontece na cesta da venda.

### BASKET-006 — Cesta vazia

Uma cesta sem itens pode ser criada e salva. Remover todos os itens de uma cesta existente e salvá-la vazia também é permitido.

### BASKET-007 — Cópia da composição do template

Ao adicionar uma cesta a uma venda a partir de um template ativo utilizável, os itens, quantidades e preço do template são copiados naquele momento. A cesta da venda passa a ser independente do template, embora possa guardar o identificador do template de origem (`origin_template_id`). Alterações no template não afetam cestas de venda existentes.

### BASKET-008 — Produtos inativos em composições

Desativar um produto não remove nem altera referências existentes em templates ou cestas. Essas composições permanecem consultáveis e editáveis; produtos inativos não podem ser incluídos em novas composições. A substituição de um item inativo é sempre explícita.

### BASKET-009 — Template inativo

Um template inativo permanece persistido, consultável, editável e reativável, mas não pode ser usado para criar uma nova cesta.

### BASKET-010 — Template com produto inativo

Um template que contenha um produto inativo não pode ser usado para criar uma nova cesta. A composição existente é preservada e requer correção explícita pelo usuário antes de voltar a ser utilizável.

### BASKET-011 — Estoque em cestas e templates

A consulta de disponibilidade de produtos em M2 é informativa. Estoque insuficiente não bloqueia a composição, e criar ou editar templates e cestas não reserva nem deduz estoque nem cria movimentações.

### BASKET-012 — Identidade, nome e unidade de produto nas composições

Composições referenciam produtos por `product_id`. Renomear o produto não altera a identidade ou quantidade da referência. Referenciar um produto em uma composição não conta como movimentação de estoque para a regra M1 de mutabilidade da unidade base; quantidades são interpretadas na unidade base atual, sem conversão ou histórico de unidades em M2.

### BASKET-013 — Template vazio e estado inicial

Um template novo nasce ativo por padrão e não possui estado DRAFT. Um template pode ser salvo sem itens e editado posteriormente. Um template ativo vazio não pode originar uma nova cesta até possuir ao menos um item.

### BASKET-014 — Produto único por composição

Cada `product_id` aparece no máximo uma vez em cada composição de template ou cesta. Incluir novamente produto já existente incrementa sua quantidade; substituir item por produto já existente agrega as quantidades em uma única linha.

### BASKET-015 — Edição de item com produto inativo

Uma composição existente que referencia produto desativado pode manter o item, alterar sua quantidade ou removê-lo. A inclusão nova do produto inativo continua proibida.

### BASKET-016 — Preço de venda manual da cesta-modelo

Cada cesta-modelo pode ter preço de venda definido manualmente e persistido, com precisão de duas casas decimais. Valores negativos e valores com precisão superior a duas casas decimais são estritamente inválidos e rejeitados. O preço zero (`0.00`) é permitido para representar brindes ou cortesias e é semanticamente distinto de preço ausente (`null`). Cestas-modelo sem preço podem permanecer cadastradas e ativas no M2.

### BASKET-017 — Sem cálculo automático de preço em M2

M2 não calcula preço sugerido ou final automaticamente. A referência custo × 2 é apenas conceitual e não se torna regra computável. Cestas preexistentes não recebem preços fictícios ou automáticos.

### BASKET-018 — Pré-requisito de preço para uso em venda

Uma cesta-modelo sem preço de venda definido não pode ser adicionada a uma venda no M4 até que o preço seja definido.

### BASKET-019 — Snapshot de preço ao adicionar à venda

Ao adicionar uma cesta-modelo à venda, o preço vigente é copiado para o item da venda e passa a ser histórico imutável frente a mudanças futuras no preço da origem.

### SALE-001 — Cliente Ativo para Nova Venda

Uma nova venda só pode ser criada e salva quando vinculada a um cliente ativo.

### SALE-002 — Venda Exige Cesta

Uma venda deve conter pelo menos uma cesta.

### SALE-003 — Várias Cestas por Venda

Uma venda pode conter várias cestas.

### SALE-004 — Dados Independentes por Cesta na Venda

Cada cesta da venda possui composição, destinatário, endereço, data de entrega, horário de entrega e preço acordado próprios.

### SALE-005 — Cópia Independente da Composição na Venda

Ao adicionar uma cesta à venda a partir de um Template, a composição e o preço do Template são copiados e passam a ser independentes do Template. A cesta da venda pode ser personalizada sem afetar o Template.

### SALE-006 — Preço Acordado por Cesta

O preço vigente da origem é copiado quando a cesta é adicionada à venda. O preço acordado pode ser ajustado manualmente somente em `RASCUNHO` e fica bloqueado a partir de `CONFIRMADA` no fluxo normal.

### SALE-007 — Total da Venda

O total da venda é a soma dos preços registrados de suas cestas e deve ser recalculado quando esses preços mudarem.

### SALE-008 — Estados Operacionais da Venda

Os estados operacionais oficiais da venda são `RASCUNHO`, `CONFIRMADA`, `EM PREPARAÇÃO`, `PRONTA`, `ENTREGUE` e `CANCELADA`.

### SALE-009 — Alterações de Composição Após a Confirmação

Uma venda em `CONFIRMADA` ou `EM PREPARAÇÃO` pode ter a composição de suas cestas alterada no fluxo normal, respeitando as restrições por estado e preservando histórico não apagável com identificador textual do operador responsável.

### SALE-010 — Preparação por Cesta

Cada cesta pode ser marcada individualmente como preparada, e a venda só passa para `PRONTA` quando todas as cestas estiverem preparadas.

### SALE-011 — Reabertura Auditável de Venda `PRONTA`

Uma venda `PRONTA` só pode ser reaberta por ação explícita, com justificativa obrigatória e registro de auditoria contendo identificador textual do operador responsável e data/hora.

### SALE-012 — Entrega por Cesta

Cada cesta é marcada como entregue por ação explícita do usuário com identificador textual do operador responsável, e a venda passa automaticamente para `ENTREGUE` quando todas as cestas estiverem entregues.

### SALE-013 — Cancelamento da Venda

O cancelamento é permitido em `RASCUNHO`, `CONFIRMADA`, `EM PREPARAÇÃO` e `PRONTA` desde que nenhuma cesta tenha sido entregue. A venda cancelada deve ser preservada, não excluída.

### AUDIT-001 — Identificação Provisória do Operador Responsável

Nas operações que exigem auditoria operacional em M4 (alteração de composição de cestas, reabertura de venda pronta e registro individual de entrega), o operador informará seu nome ou identificador por meio de entrada textual. Essa informação é persistida junto ao evento como declaração operacional. Não há sistema de autenticação, controle de permissões ou sessão de usuário como parte deste mecanismo.

### AUDIT-002 — Rejeição de Operação Auditada sem Responsável

A submissão de alterações de composição, reaberturas de venda pronta ou registros de entrega sem o preenchimento do identificador textual do operador responsável deve ser rejeitada pela validação de entrada, impedindo o salvamento da operação.

### PAY-001 — Pagamentos Pertencem ao M5

O registro de pagamentos e a autorização financeira da confirmação da venda pertencem ao marco de pagamentos.

### PAY-002 — Limite para Confirmação da Venda

A transição `RASCUNHO → CONFIRMADA` depende de pagamento de pelo menos 50% do valor total da venda e da validação dos dados obrigatórios de entrega de todas as cestas.

### INV-001 — Estoque Baseado em Movimentações

As alterações de estoque são representadas por meio de movimentações de estoque.

### INV-002 — Preservação do Histórico de Estoque

Correções de estoque devem preservar o histórico original de movimentações.

### INV-003 — Seleção Permitida com Estoque Insuficiente

Um produto com estoque insuficiente pode ser selecionado para uma cesta ou venda antes da confirmação financeira, desde que a falta seja claramente indicada.

### INV-004 — Reserva e Baixa Seguem Política Aprovada

A reserva de estoque e a baixa física associadas às vendas seguem a política formal definida na seção 37. Operações de venda não movimentam estoque de forma automática ou implícita fora dos eventos e condições explicitamente definidos pela política.

### INV-005 — Alterações de Composição Seguem Política de Diferença

Alterações na composição de uma venda após a reserva seguem as regras de diferença de quantidades definidas pela política de reserva e baixa: adições e aumentos exigem reserva atômica da diferença; reduções e remoções liberam a diferença reservada sem gerar movimentação física fictícia.

### INV-006 — Proibição de Estoque Físico Negativo

O sistema não deve criar uma movimentação de estoque que faça o saldo de estoque físico disponível de um produto se tornar negativo. Esse invariante é absoluto e se aplica estritamente a operações de estoque concorrentes (`ADR-001`).

### INV-007 — Preparação Inicia Baixa Física

No início da preparação de uma venda, o sistema executa a baixa física das quantidades necessárias de todos os produtos da venda, de forma atômica, sem permitir estoque negativo. A entrega de uma cesta não executa nova movimentação de estoque.

### INV-008 — Produtos Inativos Não Podem Receber Operações de Estoque

Um produto inativo não pode receber nenhuma Entrada ou Ajuste de estoque. O produto deve ser reativado antes de modificar o estoque. A reativação não altera o estoque.

### PROD-001 — Unidades Base Controladas e Mutabilidade

A `base_unit` de um produto é um valor controlado e deve ser um destes: `UN`, `KG`, `G`, `L`, `ML`. A `base_unit` só pode ser editada enquanto o produto não tiver movimentações de estoque. Depois que houver uma movimentação, a `base_unit` será imutável.

### PROD-002 — Nome do Produto Não Exclusivo

Os nomes dos produtos não precisam ser exclusivos em M1. Vários produtos podem ter o mesmo nome.

### SEARCH-001 — Semântica da Busca de Produtos

A busca de produtos não diferencia maiúsculas de minúsculas e corresponde a substrings do nome do produto. Funcionalidades avançadas de busca (busca aproximada, classificação, índice de texto completo) estão fora do escopo.

---

# 37. Política de Reserva e Baixa de Estoque Associada às Vendas

Esta seção formaliza a política aprovada pelo Product Owner sobre reserva, baixa física, alterações de composição e cancelamento de vendas.

A política distingue explicitamente os seguintes conceitos:

1. **Pagamento registrado:** registro de um pagamento recebido pela venda. O pagamento persiste independentemente do resultado da confirmação financeira.
2. **Confirmação financeira da venda:** autorização da transição `RASCUNHO → CONFIRMADA`, condicionada ao pagamento mínimo de 50% e à disponibilidade integral dos produtos necessários para reserva.
3. **Reserva de estoque:** alocação lógica das quantidades necessárias dos produtos da venda, impedindo que sejam reservadas para outras vendas. A reserva não é baixa física.
4. **Baixa física:** dedução real do saldo de estoque físico, registrada como movimentação de estoque.
5. **Liberação de reserva:** devolução das quantidades reservadas para o pool disponível, sem movimentação física.
6. **Reintegração física:** retorno de produtos ao estoque mediante confirmação física e movimentação registrada.

### Responsabilidade conceitual por etapa

A confirmação financeira e a reserva de estoque pertencem ao marco de pagamentos (M5). A baixa física no início da preparação pertence ao fluxo operacional de vendas, integrado ao marco que implementar a política de estoque.

Nenhuma dessas responsabilidades é atribuída automaticamente ao M4, que define a estrutura operacional da venda.

### Regras da política

### RES-001 — Confirmação Financeira e Reserva como Operação Atômica

A confirmação financeira e a reserva de estoque constituem uma única operação atômica executada nesta ordem:

1. Verificar se o pagamento registrado atingiu pelo menos 50% do valor total da venda.
2. Verificar a disponibilidade integral de todos os produtos necessários para reserva.
3. Reservar todas as quantidades necessárias.
4. Efetivar a confirmação financeira da venda.

Se qualquer validação ou reserva falhar, a confirmação financeira e a reserva integral não são efetivadas. O pagamento já recebido permanece registrado. A política impede reservas parciais: se um produto não puder ser reservado, nenhuma quantidade é reservada.

### RES-002 — Bloqueio por Estoque Insuficiente

Se faltar estoque para reservar integralmente os produtos da venda, a confirmação financeira é bloqueada. O sistema informa quais produtos e quantidades estão faltantes. O pagamento recebido permanece registrado, mas a venda não é confirmada financeiramente e nenhuma reserva é criada.

### RES-003 — Pagamento Registrado Independente da Confirmação

Um pagamento recebido deve continuar registrado mesmo quando a venda não puder ser confirmada financeiramente por falta de estoque. Pagamento registrado e confirmação financeira da venda são conceitos distintos.

### RES-004 — Reserva Não é Baixa Física

A reserva de estoque não representa baixa física. O saldo de estoque físico permanece inalterado enquanto os produtos estiverem apenas reservados.

### RES-005 — Baixa Física e Liberação da Reserva no Início da Preparação

No início da preparação (`CONFIRMADA → EM PREPARAÇÃO`), o sistema executa atomicamente:

1. A baixa física das quantidades necessárias de todos os produtos da venda, registrada como movimentação de estoque.
2. A liberação das reservas correspondentes, pois as quantidades baixadas fisicamente deixam de estar reservadas.

O estoque físico é atualizado por movimentações registradas, sem permitir saldo físico negativo. Se a operação falhar, não há baixa parcial nem atualização parcial das reservas: toda a transação é revertida.

### RES-006 — Adições e Aumentos Exigem Reserva da Diferença

Adições de itens e aumentos de quantidade em uma venda com reserva ou baixa ativa exigem disponibilidade e reserva atômica somente da diferença de quantidades. Se não houver estoque suficiente para a diferença, a alteração é rejeitada sem modificar a composição ou a reserva existentes.

A regra distingue três situações:

- **Quantidades ainda reservadas:** produtos reservados mas ainda não baixados fisicamente. Adições reservam a diferença; a baixa física ocorre quando o operador marca explicitamente como preparada a cesta cuja composição foi alterada.
- **Quantidades já baixadas fisicamente:** produtos cuja baixa física já foi registrada. Adições de quantidade reservam a diferença, mas não alteram as quantidades já baixadas.
- **Baixa física de quantidades adicionais:** quando uma adição ou aumento é reservado após o início da preparação, a baixa física da diferença ocorre quando o operador marca explicitamente como preparada a cesta cuja composição foi alterada. A baixa física e a liberação das reservas correspondentes ocorrem atomicamente. Se a baixa física falhar ou não houver estoque físico suficiente, a cesta não pode ser marcada como preparada e não pode ocorrer baixa parcial nem atualização parcial das reservas. Quantidades já baixadas fisicamente em etapas anteriores nunca podem ser baixadas novamente.

### RES-007 — Reduções e Remoções Liberam a Reserva

Reduções de quantidade e remoções de itens liberam somente as quantidades ainda reservadas, sem gerar movimentação física fictícia.

A remoção ou redução de quantidades já baixadas fisicamente não pode gerar entrada automática de estoque. Quantidades já baixadas fisicamente não são liberadas por redução ou remoção: não geram entradas automáticas de estoque nem são consideradas recuperadas por inferência. Sua eventual reintegração exige conferência física e movimentação registrada.

### RES-008 — Quantidades Já Baixadas Não Geram Entradas Automáticas

Quantidades já baixadas fisicamente não geram entradas automáticas de estoque por alterações de composição. Qualquer reintegração exige confirmação física e movimentação registrada.

### RES-009 — Reabertura Não Repete Baixas

A reabertura de uma venda `PRONTA` para `EM PREPARAÇÃO` não pode repetir baixas físicas já realizadas durante a preparação anterior. Quantidades já baixadas fisicamente nunca podem ser baixadas novamente.

### RES-010 — Cancelamento Antes da Preparação

No cancelamento de uma venda antes do início da preparação, a reserva integral é liberada sem movimentação física fictícia.

### RES-011 — Cancelamento Após o Início da Preparação

No cancelamento de uma venda após o início da preparação:

1. As reservas remanescentes (produtos reservados mas ainda não baixados) são liberadas.
2. Exige-se conferência dos produtos já baixados fisicamente.
3. Somente as quantidades fisicamente recuperadas e aproveitáveis são reintegradas ao estoque, mediante movimentação de estoque registrada.
4. O histórico, o responsável e o motivo do cancelamento são preservados.

### RES-012 — Proibição de Cancelamento com Entrega

Manutenção da proibição vigente: o cancelamento de uma venda é bloqueado quando alguma cesta já tiver sido entregue.

---

# 38. Decisões de Negócio em Aberto

Os tópicos a seguir permanecem intencionalmente sem resolução e não devem ser transformados em suposições pela implementação.

### Autenticação e Controle de Acesso

O mecanismo aprovado para o M4 é estritamente uma declaração textual do operador no momento da operação auditada. Não há módulos de usuários, login, senhas, papéis ou sessões. A implementação de um modelo seguro de autenticação e controle de acesso permanece fora do escopo atual e exigirá decisão e especificação próprias.

### Custo do Estoque/Seleção de Lotes

A estratégia provisória é preferir o lote com vencimento mais próximo ao consumir estoque.

A implementação exata do cálculo de custos será definida quando a gestão de lotes for introduzida.

### Custo e Precificação de Cestas

M1 fornece `reference_price` como propriedade comercial do produto, representando o preço da unidade comercial (caixa, pacote, saco). O `commercial_conversion_factor` indica quantas unidades-base há na unidade comercial. M2 calcula o custo de referência da cesta a partir de `preço_por_unidade_base × quantidade`, onde `preço_por_unidade_base = reference_price / commercial_conversion_factor` (ou `reference_price` quando o fator não está definido). O preço sugerido é 2 × custo de referência. O `unit_cost` em entradas de estoque permanece para controle interno de custos.

### Gestão de Compras

Fluxos detalhados de compra, informações de fornecedores, documentos de compra e campos relacionados ainda não foram definidos.

### Produção Interna

O processo de produção para produtos feitos internamente ainda não foi definido.

### Tratamento de Perdas e Vencimentos

Fluxos detalhados para perdas, danos, vencimentos e consumo interno ainda não foram definidos.

---

# 39. Oportunidades de Negócio Futuras

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

# 40. Política de Mudanças

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

# 41. Princípio Orientador de Negócio

O sistema existe para apoiar a operação real da Casa Afeto.

Portanto:

> **O comportamento de negócio deve ser explícito, as informações históricas devem ser preservadas e o sistema deve permanecer simples o bastante para evoluir conforme o negócio aprende.**

O sistema deve modelar o que a Casa Afeto decidiu fazer hoje sem implementar prematuramente tudo o que a Casa Afeto talvez queira fazer no futuro.
