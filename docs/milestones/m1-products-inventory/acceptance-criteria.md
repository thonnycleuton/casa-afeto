# Critérios de Aceitação do Marco M1 — Produtos e Estoque

**Versão do documento:** 0.1
**Status:** Pronto para implementação
**Marco:** M1 — Produtos e Estoque (Products & Inventory)

---

# 1. Finalidade

Este documento define os critérios objetivos de aceitação para M1 — Produtos e Estoque (Products & Inventory).

Os critérios traduzem a especificação e os casos de uso de M1 em condições observáveis e testáveis.

Um critério é considerado atendido somente quando o comportamento esperado puder ser demonstrado por testes automatizados e/ou validação manual.

A implementação deve satisfazer estes critérios sem introduzir comportamento fora do escopo aprovado de M1.

---

# 2. Regras de aceitação

## AC-01 — Criação do produto

**Dado** que não existe um produto com a identidade informada
**Quando** o operador cria um produto com nome válido e unidade base de estoque válida
**Então** o sistema cria o produto
**E** o produto fica ativo
**E** seu saldo de estoque é zero
**E** nenhuma movimentação de estoque é criada.

---

## AC-02 — Nome do produto é obrigatório

**Dado** que o operador está criando um produto
**Quando** o operador envia o produto sem um nome válido
**Então** o sistema rejeita a operação
**E** nenhum produto é criado.

---

## AC-03 — Unidade base do produto é obrigatória

**Dado** que o operador está criando um produto
**Quando** o operador envia o produto sem uma unidade base de estoque válida
**Então** o sistema rejeita a operação
**E** nenhum produto é criado.

---

## AC-04 — Edição do produto

**Dado** que existe um produto
**Quando** o operador altera informações editáveis válidas do produto
**Então** o produto é atualizado
**E** sua identidade permanece inalterada
**E** movimentações existentes de estoque continuam associadas ao mesmo produto.

---

## AC-05 — Ativação do produto

**Dado** que um produto está inativo
**Quando** o operador ativa o produto
**Então** o produto torna-se ativo
**E** seu saldo de estoque permanece inalterado
**E** seu histórico de estoque permanece inalterado.

---

## AC-06 — Desativação do produto

**Dado** que um produto está ativo
**Quando** o operador desativa o produto
**Então** o produto torna-se inativo
**E** seu saldo de estoque permanece inalterado
**E** seu histórico de estoque permanece inalterado
**E** o produto não está disponível para novas operações que exijam um produto ativo.

---

## AC-07 — A desativação não exclui dados históricos

**Dado** que um produto possui histórico de estoque
**Quando** o produto é desativado
**Então** o produto permanece acessível em contextos administrativos/históricos
**E** suas movimentações de estoque continuam disponíveis
**E** seu saldo de estoque permanece inalterado.

---

# 3. Listagem e busca de produtos

## AC-08 — Listagem de produtos

**Dado** que existem vários produtos
**Quando** o operador abre a lista de produtos
**Então** o sistema exibe os produtos
**E** cada produto expõe pelo menos o nome, a unidade base, o estado ativo e o saldo atual de estoque.

---

## AC-09 — Produtos inativos permanecem visíveis

**Dado** que existe um produto inativo
**Quando** o operador visualiza a lista de gestão de produtos
**Então** o produto inativo continua visível
**E** seu estado inativo é identificável.

---

## AC-10 — Busca de produto

**Dado** que existem produtos
**Quando** o operador busca usando parte ou totalidade do nome do produto
**Então** o sistema retorna produtos correspondentes de acordo com a busca definida.

---

## AC-11 — Busca sem resultados

**Dado** que nenhum produto corresponde à busca informada
**Quando** o operador executa a busca
**Então** o sistema retorna um resultado vazio
**E** o sistema não reporta isso como erro da aplicação.

---

# 4. Entrada de estoque

## AC-12 — Adicionar estoque

**Dado** que existe um produto ativo com saldo atual
**Quando** o operador adiciona uma quantidade válida positiva
**Então** uma movimentação de entrada de estoque é criada
**E** o saldo do produto aumenta nessa quantidade.

Exemplo:

```text
Antes: 5
Entrada: +20
Depois: 25
```

---

## AC-13 — Adicionar estoque a produto com saldo zero

**Dado** que existe um produto ativo sem estoque
**Quando** o operador adiciona 20 unidades
**Então** o saldo torna-se 20
**E** existe exatamente uma movimentação correspondente de estoque.

---

## AC-14 — Entrada de estoque inválida

**Dado** que um operador está adicionando estoque
**Quando** a quantidade informada é inválida
**Então** a operação é rejeitada
**E** nenhuma movimentação de estoque é criada
**E** o saldo anterior permanece inalterado.

---

## AC-15 — A entrada de estoque exige um produto existente

**Dado** que não existe produto para a referência solicitada
**Quando** o operador tenta adicionar estoque
**Então** a operação é rejeitada
**E** nenhuma movimentação de estoque é criada.

---

## AC-16 — Produto inativo não pode receber entrada normal de estoque

**Dado** que um produto está inativo
**Quando** o operador tenta realizar uma entrada normal de estoque
**Então** a operação é rejeitada
**E** nenhuma movimentação de estoque é criada
**E** o saldo atual de estoque permanece inalterado.

---

# 5. Ajuste de estoque

## AC-17 — Ajuste positivo de estoque

**Dado** que um produto ativo tem saldo atual de 17
**Quando** o operador aplica um ajuste de +2
**Então** uma movimentação de ajuste é criada
**E** o saldo resultante é 19.

---

## AC-18 — Ajuste negativo de estoque

**Dado** que um produto ativo tem saldo atual de 20
**Quando** o operador aplica um ajuste de -3
**Então** uma movimentação de ajuste é criada
**E** o saldo resultante é 17.

---

## AC-19 — Ajuste não pode criar estoque negativo

**Dado** que um produto ativo tem saldo atual de 2
**Quando** o operador tenta um ajuste de -3
**Então** a operação é rejeitada
**E** nenhuma movimentação de ajuste é criada
**E** o saldo permanece 2.

---

## AC-20 — Ajuste igual ao saldo atual

**Dado** que um produto ativo tem saldo atual de 5
**Quando** o operador aplica um ajuste de -5
**Então** a operação é aceita
**E** uma movimentação de ajuste de -5 é criada
**E** o saldo resultante é 0.

Zero em estoque é válido.

---

## AC-21 — Ajuste inválido

**Dado** que um operador está realizando um ajuste de estoque
**Quando** o ajuste informado é inválido
**Então** a operação é rejeitada
**E** nenhuma movimentação é criada
**E** o saldo existente permanece inalterado.

---

## AC-22 — Ajuste exige um produto existente

**Dado** que não existe produto para a referência solicitada
**Quando** o operador tenta um ajuste de estoque
**Então** a operação é rejeitada
**E** nenhuma movimentação de estoque é criada.

---

## AC-23 — Produto inativo não pode receber ajuste normal

**Dado** que um produto está inativo
**Quando** o operador tenta um ajuste normal de estoque
**Então** a operação é rejeitada
**E** nenhuma movimentação de estoque é criada
**E** o saldo existente permanece inalterado.

---

# 6. Histórico de estoque

## AC-24 — A movimentação de estoque é preservada

**Dado** que um produto possui uma entrada de estoque
**Quando** o operador visualiza seu histórico de estoque
**Então** a entrada está presente
**E** sua quantidade e tipo de movimentação são preservados.

---

## AC-25 — Múltiplas movimentações são preservadas

**Dado** que um produto tem as seguintes movimentações:

```text
+20
-3
+5
```

**Quando** o operador visualiza o histórico de estoque
**Então** as três movimentações estão presentes
**E** suas quantidades permanecem inalteradas
**E** seus tipos de movimentação são preservados.

---

## AC-26 — Correções criam novas movimentações

**Dado** que um produto possui um histórico de estoque existente
**Quando** o operador realiza uma correção de estoque
**Então** uma nova movimentação de ajuste é criada
**E** movimentações anteriores permanecem inalteradas.

---

## AC-27 — O saldo de estoque reflete o histórico de movimentações

**Dado** que um produto tem movimentações:

```text
+20
-3
+5
-2
```

**Quando** o saldo atual de estoque é calculado
**Então** o saldo é 20.

---

# 7. Disponibilidade de estoque

## AC-28 — Produto está disponível quando a quantidade é suficiente

**Dado** que um produto tem 10 unidades disponíveis
**Quando** a disponibilidade é verificada para 4 unidades
**Então** o sistema informa que a quantidade solicitada está disponível
**E** a falta é zero
**E** o estoque não é modificado.

---

## AC-29 — Produto está insuficiente quando a quantidade não é suficiente

**Dado** que um produto tem 2 unidades disponíveis
**Quando** a disponibilidade é verificada para 5 unidades
**Então** o sistema informa estoque insuficiente
**E** a falta é de 3 unidades
**E** o estoque não é modificado.

---

## AC-30 — Estoque insuficiente não cria saldo negativo

**Dado** que um produto tem 2 unidades disponíveis
**Quando** a disponibilidade é verificada para 5 unidades
**Então** o sistema não deve criar uma movimentação de estoque -3
**E** o saldo de estoque permanece 2.

---

## AC-31 — Estoque insuficiente não invalida o produto

**Dado** que um produto ativo tem saldo zero
**Quando** a disponibilidade é verificada para uma quantidade positiva
**Então** o produto permanece válido
**E** o sistema informa estoque insuficiente em vez de tratar o produto como inválido.

---

# 8. Integridade do estoque

## AC-32 — Operação rejeitada de estoque não tem efeitos colaterais

**Dado** que uma operação de estoque é inválida
**Quando** a operação é rejeitada
**Então** nenhuma movimentação de estoque é criada
**E** o saldo do produto permanece inalterado
**E** o histórico existente de estoque permanece inalterado.

---

## AC-33 — O saldo de estoque não pode ficar negativo

**Dado** que qualquer saldo atual de estoque seja maior ou igual a zero
**Quando** uma operação de estoque resultaria em saldo negativo
**Então** a operação é rejeitada
**E** o saldo resultante permanece não negativo.

---

## AC-34 — Estoque zero é válido

**Dado** que um produto tem estoque
**Quando** o estoque é reduzido exatamente a zero
**Então** a operação é aceita
**E** o saldo resultante é zero
**E** o produto continua sendo um produto ativo válido.

---

## AC-35 — Histórico de estoque não é reescrito

**Dado** que um produto tem movimentações de estoque anteriores
**Quando** um ajuste posterior é realizado
**Então** as movimentações anteriores retêm seus valores originais
**E** o ajuste é representado por uma nova movimentação.

---

# 9. Relação entre produto e estoque

## AC-36 — Cada movimentação de estoque pertence a um produto

**Dado** que uma movimentação de estoque é criada com sucesso
**Então** ela referencia um produto existente
**E** a movimentação não pode existir sem uma referência válida ao produto.

---

## AC-37 — A desativação do produto não altera o estoque

**Dado** que um produto ativo tem saldo de 15
**Quando** o produto é desativado
**Então** o saldo permanece 15
**E** nenhuma movimentação de estoque é criada.

---

## AC-38 — A reativação do produto não altera o estoque

**Dado** que um produto inativo tem saldo de 15
**Quando** o produto é reativado
**Então** o saldo permanece 15
**E** nenhuma movimentação de estoque é criada.

---

# 10. Cenário de aceitação de ponta a ponta

## AC-39 — Fluxo operacional completo de M1

**Dado** que o sistema não possui o produto Chocolate

**Quando** o operador:

1. cria Chocolate com unidade base `UN`;
2. adiciona 20 unidades;
3. aplica um ajuste de -3;
4. verifica o saldo do estoque;
5. verifica a disponibilidade para 20 unidades;
6. tenta um ajuste de -18;
7. visualiza o histórico de movimentações;
8. desativa Chocolate;

**Então**:

```text
Produto:
Chocolate
Ativo:
Não

Saldo de estoque:
17 UN
```

**E** o histórico contém:

```text
ENTRY       +20
ADJUSTMENT   -3
```

**E** o ajuste rejeitado `-18` não aparece no histórico.

**E** a verificação de disponibilidade para 20 unidades informa:

```text
Disponível: 17
Solicitado: 20
Falta: 3
```

**E** o produto permanece presente na gestão de produtos.

**E** o estoque permanece 17.

---

# 11. Aceitação do escopo

## AC-40 — Nenhum recurso futuro de estoque é requerido

M1 não deve ser considerado incompleto porque o sistema não implementa:

* compras;
* itens de compra;
* fornecedores;
* lotes de estoque;
* vencimento;
* FEFO;
* reposição;
* gestão de perdas;
* produção;
* estoque reservado;
* vendas;
* pagamento;
* dedução de estoque relacionada a cestas.

Esses recursos são explicitamente fora do escopo de M1.

---

# 11.1. Preço de referência do produto

## AC-41 — Criar produto com preço de referência

**Dado** que o operador cria um produto com `reference_price` positivo e duas casas decimais
**Então** o valor é persistido
**E** o produto é criado com sucesso.

---

## AC-42 — Criar produto sem preço de referência

**Dado** que o operador cria um produto sem `reference_price`
**Então** o produto é criado com `reference_price = null`
**E** o produto é criado com sucesso.

---

## AC-43 — Editar preço de referência

**Dado** um produto existente
**Quando** o operador define ou altera `reference_price` para um valor válido
**Então** o novo valor é persistido.

---

## AC-44 — Rejeitar preço de referência negativo

**Dado** que o operador tenta definir `reference_price` com valor negativo
**Então** a operação é rejeitada
**E** o `reference_price` não é alterado.

---

## AC-45 — Rejeitar preço de referência com mais de duas casas decimais

**Dado** que o operador tenta definir `reference_price` com precisão superior a duas casas
**Então** a operação é rejeitada
**E** o `reference_price` não é alterado.

---

# 12. Expectativas de testes automatizados

Cada critério de aceitação envolvendo comportamento de negócio determinístico deve ser coberto por testes automatizados quando tecnicamente apropriado.

No mínimo, os testes automatizados devem cobrir:

* criação de produto;
* edição de produto;
* ativação/desativação;
* entrada de estoque;
* ajuste positivo;
* ajuste negativo;
* saldo zero;
* rejeição de saldo resultante negativo;
* histórico de movimentações;
* cálculo do saldo;
* verificações de disponibilidade;
* operações inválidas sem efeitos colaterais.

Os testes devem verificar o comportamento observável em vez da estrutura interna de implementação.

---

# 13. Expectativas de validação manual

Depois que os testes automatizados passarem, o operador deve validar manualmente o fluxo operacional principal.

A validação manual deve confirmar:

* criação de produtos;
* visibilidade dos produtos;
* entrada de estoque;
* ajuste de estoque;
* saldo de estoque;
* histórico de movimentações;
* aviso/estado de estoque insuficiente;
* rejeição de estoque negativo;
* desativação de produtos;
* preservação do estoque após a desativação.

A lista detalhada de verificação pertence a:

```text
docs/milestones/m1-products-inventory/validation.md
```

---

# 14. Decisão de Aceitação

M1 só é aceito quando:

1. Todos os critérios de aceitação aplicáveis forem aprovados.
2. Os testes automatizados passarem.
3. Nenhuma regressão conhecida for introduzida.
4. A validação manual passar.
5. Nenhum comportamento de negócio não aprovado tiver sido introduzido.
6. A implementação permanecer dentro do escopo de M1.
7. O usuário aprovar explicitamente o marco.

Uma implementação que apenas compila ou passa nos testes unitários não é suficiente por si só.

O comportamento de negócio também deve satisfazer os critérios de aceitação.

---

# 15. Rastreabilidade

A cadeia de documentação de M1 é:

```text
Contrato de Negócio
        ↓
Especificação de M1
        ↓
Casos de Uso de M1
        ↓
Critérios de Aceitação de M1
        ↓
Implementação
        ↓
Testes Automatizados
        ↓
Validação Manual
```

Todo comportamento de negócio de M1 deve ser rastreável por meio dessa cadeia.

Se a implementação revelar um requisito que não possa ser rastreado até uma especificação existente ou decisão aprovada, o agente deve parar e esclarecer o requisito antes de ampliar o escopo.

---

# 16. Princípio Final de Aceitação

A implementação está correta quando o comportamento de negócio documentado é observável e verificável.

> **Se os critérios de aceitação dizem que algo deve acontecer, isso deve acontecer.**
>
> **Se os critérios de aceitação não exigem algo, M1 não precisa implementá-lo.**
