# Casos de Uso do Marco M1 — Produtos e Estoque

**Versão do documento:** 0.1
**Status:** Pronto para implementação
**Marco:** M1 — Produtos e Estoque (Products & Inventory)

---

# 1. Finalidade

Este documento descreve os casos de uso voltados para o usuário do M1 — Produtos e Estoque (Products & Inventory).

Ele traduz a especificação de M1 em fluxos operacionais concretos.

Esses casos de uso descrevem:

* quem executa uma operação;
* o que o usuário deseja realizar;
* o fluxo normal;
* fluxos alternativos relevantes;
* o comportamento esperado de negócio.

Eles não prescrevem:

* endpoints de API;
* implementação de banco de dados;
* arquitetura de frontend;
* comportamento específico da framework;
* estrutura interna de serviço.

Esses são detalhes de implementação.

---

# 2. Atores

M1 tem um ator principal:

### Operador da Casa Afeto

A pessoa responsável por gerenciar produtos e estoque físico.

O operador pode:

* cadastrar produtos;
* manter informações do produto;
* ativar/desativar produtos;
* registrar entradas de estoque;
* corrigir estoque;
* inspecionar estoque;
* inspecionar histórico de estoque.

Nenhum papel separado ou modelo de permissão é exigido por M1.

---

# 3. Visão geral dos casos de uso

```text
Gestão de Produtos
│
├── UC-M1-01 Criar Produto
├── UC-M1-02 Editar Produto
├── UC-M1-03 Ativar Produto
├── UC-M1-04 Desativar Produto
├── UC-M1-05 Listar Produtos
└── UC-M1-06 Buscar Produtos

Gestão de Estoque
│
├── UC-M1-07 Adicionar Estoque
├── UC-M1-08 Ajustar Estoque
├── UC-M1-09 Visualizar Saldo de Estoque
├── UC-M1-10 Visualizar Histórico de Estoque
└── UC-M1-11 Verificar Disponibilidade de Estoque
```

---

# 4. UC-M1-01 — Criar produto

## Objetivo

Permitir que o operador registre um novo produto.

## Pré-condições

Nenhuma.

## Fluxo principal

1. O operador abre a área de gestão de produtos.
2. O operador escolhe criar um produto.
3. O sistema solicita as informações do produto.
4. O operador informa o nome do produto.
5. O operador seleciona ou informa a unidade base de estoque (`base_unit`: `UN`, `KG`, `G`, `L`, `ML`).
6. O operador pode informar opcionalmente o preço de referência (`reference_price`) com duas casas decimais.
7. O operador envia o produto.
8. O sistema valida as informações:
   - O nome do produto deve ser não vazio;
   - A unidade base deve ser uma de `UN`, `KG`, `G`, `L`, `ML` (`BD-01`);
   - Se `reference_price` for informado, não pode ser negativo e deve ter no máximo duas casas decimais.
9. O sistema cria o produto.
9. O produto fica inicialmente ativo.
10. O sistema confirma a criação com sucesso.

Nomes de produtos não são **obrigatórios como únicos** em M1 (`PROD-002`). Dois produtos distintos podem ter o mesmo nome.

## Exemplo

```text
Nome: Chocolate
Unidade base: UN
Preço de referência: 5.00
```

Resultado:

```text
Produto: Chocolate
Unidade: UN
Ativo: Sim
Saldo de estoque: 0
Preço de referência: 5.00
```

## Fluxos alternativos

### A1 — Nome ausente

Se o operador não fornecer um nome de produto:

1. O sistema rejeita a operação.
2. O sistema indica que o nome do produto é obrigatório.
3. Nenhum produto é criado.

### A2 — Unidade inválida

Se a unidade base informada não estiver entre `UN`, `KG`, `G`, `L`, `ML`:

1. O sistema rejeita a operação.
2. O sistema informa ao operador que apenas `UN`, `KG`, `G`, `L` e `ML` são unidades válidas.
3. Nenhum produto é criado.

### A3 — Preço de referência negativo

Se o operador informar `reference_price` com valor negativo:

1. O sistema rejeita a operação.
2. O sistema informa ao operador que o preço de referência não pode ser negativo.
3. Nenhum produto é criado.

### A4 — Preço de referência com mais de duas casas decimais

Se o operador informar `reference_price` com mais de duas casas decimais:

1. O sistema rejeita a operação.
2. O sistema informa ao operador que o preço de referência deve ter no máximo duas casas decimais.
3. Nenhum produto é criado.

## Pós-condições

Existe um novo produto ativo com saldo zero de estoque.

Nenhuma movimentação de estoque é criada.

---

# 5. UC-M1-02 — Editar produto

## Objetivo

Permitir que o operador atualize as informações do produto.

## Pré-condições

* O produto existe.

## Fluxo principal

1. O operador abre o produto.
2. O sistema exibe suas informações atuais.
3. O operador altera informações editáveis (por exemplo, nome, `base_unit` se permitido, ou `reference_price`).
4. O operador salva as alterações.
5. O sistema valida as alterações:
   - O nome deve ser não vazio;
   - Se `base_unit` foi alterada, o produto deve ter **zero movimentações de estoque** (`BD-02`);
   - Se `base_unit` foi alterada, o novo valor deve ser um de `UN`, `KG`, `G`, `L`, `ML`;
   - Se `reference_price` foi alterado, não pode ser negativo e deve ter no máximo duas casas decimais.
6. O sistema persiste o produto atualizado.
7. O sistema confirma a atualização.

## Exemplo

```text
Antes:
Chocolate (UN, reference_price: 5.00)

Depois:
Chocolate (UN, reference_price: 7.50)
```

## Fluxos alternativos

### A1 — Produto não existe

O sistema informa que o produto solicitado não foi encontrado.

Nenhuma alteração é feita.

### A2 — Informação inválida

O sistema rejeita a alteração e explica o problema de validação.

As informações anteriores do produto permanecem inalteradas.

### A3 — Tentativa de editar a unidade base quando existem movimentações de estoque

Se o operador tentar alterar `base_unit` em um produto que tenha pelo menos uma movimentação de estoque:

1. O sistema rejeita a alteração de `base_unit`.
2. O sistema informa ao operador que `base_unit` não pode ser alterada após o registro de movimentações de estoque (`BD-02`).
3. A `base_unit` existente permanece inalterada.

### A4 — Preço de referência inválido

Se o operador tentar definir `reference_price` com valor negativo ou mais de duas casas decimais:

1. O sistema rejeita a alteração de `reference_price`.
2. O sistema informa ao operador a regra de validação violada.
3. O `reference_price` existente permanece inalterado.

## Comportamento importante

A edição de um produto não deve alterar seu histórico de estoque.

Por exemplo:

```text
Histórico de estoque:

+20 Chocolate
-3 Chocolate

Renomear:
Chocolate → Premium Chocolate

O histórico permanece associado ao mesmo produto.
```

---

# 6. UC-M1-03 — Ativar produto

## Objetivo

Tornar um produto inativo disponível para novas operações.

## Pré-condições

* O produto existe.
* O produto está atualmente inativo.

## Fluxo principal

1. O operador abre o produto inativo.
2. O operador escolhe ativá-lo.
3. O sistema altera o estado do produto para ativo.
4. O sistema confirma a operação.

## Pós-condições

O produto está ativo.

Seu estoque e movimentações históricas permanecem inalterados.

---

# 7. UC-M1-04 — Desativar produto

## Objetivo

Impedir que um produto seja selecionado para novas atividades operacionais.

## Pré-condições

* O produto existe.
* O produto está atualmente ativo.

## Fluxo principal

1. O operador abre o produto.
2. O operador escolhe desativá-lo.
3. O sistema altera o estado do produto para inativo.
4. O sistema confirma a operação.

## Comportamento importante

A desativação não:

* exclui o produto;
* exclui o estoque;
* exclui movimentações de estoque;
* altera o saldo de estoque.

Exemplo:

```text
Chocolate
Ativo: Sim
Estoque: 15

Desativar

Chocolate
Ativo: Não
Estoque: 15
```

## Pós-condições

O produto está inativo.

Operações futuras que exigem um produto ativo não devem permitir que ele seja selecionado.

---

# 8. UC-M1-05 — Listar produtos

## Objetivo

Permitir que o operador visualize produtos cadastrados.

## Pré-condições

Nenhuma.

## Fluxo principal

1. O operador abre a lista de produtos.
2. O sistema recupera os produtos disponíveis.
3. O sistema exibe cada produto.
4. O operador pode identificar pelo menos:

   * nome;
   * unidade base;
   * estado ativo/inativo;
   * saldo atual de estoque.

## Comportamento importante

Produtos inativos permanecem visíveis na gestão de produtos.

A desativação não os remove de visualizações históricas ou administrativas.

## Estado vazio

Se não existirem produtos, o sistema deve indicar claramente que nenhum produto foi cadastrado.

---

# 9. UC-M1-06 — Buscar produtos

## Objetivo

Permitir que o operador encontre um produto pelo nome.

## Pré-condições

Nenhuma.

## Fluxo principal

1. O operador abre a lista de produtos.
2. O operador digita um termo de busca.
3. O sistema busca os nomes dos produtos de forma insensível a maiúsculas e minúsculas usando correspondência por substring (`SEARCH-001`, `BD-08`).
4. O sistema exibe os produtos correspondentes.

## Exemplo

Busca:

```text
choc
```

Correspondências (`choc`, `Choc`, `CHOC`, `ChoC`):

```text
Chocolate
Chocolate Premium
Chocolate Branco
```

## Fluxo alternativo

### A1 — Sem resultados

O sistema informa ao operador que nenhum produto correspondente foi encontrado.

Nenhum erro é gerado apenas porque a busca não encontrou resultados.

---

# 10. UC-M1-07 — Adicionar estoque

## Objetivo

Registrar uma entrada física positiva de estoque (`ENTRY`).

## Pré-condições

* O produto existe.
* O produto está ativo.

## Fluxo principal

1. O operador seleciona um produto.
2. O sistema exibe o saldo atual de estoque.
3. O operador escolhe adicionar estoque.
4. O operador informa a quantidade.
5. O operador envia a operação.
6. O sistema valida a quantidade (`BD-03`):
   - A quantidade deve ser maior que zero (> 0);
   - Se a unidade base do produto for `UN`, a quantidade deve ser um inteiro positivo;
   - Se a unidade base do produto for `KG`, `G`, `L` ou `ML`, a quantidade deve ser um decimal positivo.
7. O sistema cria uma movimentação de estoque do tipo `ENTRY`.
8. O sistema atualiza ou deriva o saldo de estoque.
9. O sistema exibe o saldo resultante.

## Exemplo

Atual:

```text
Chocolate = 5 UN
```

O operador informa:

```text
+20 UN
```

Resultado:

```text
Chocolate = 25 UN
```

O histórico de movimentações contém:

```text
ENTRY +20
```

## Fluxos Alternativos

### A1 — Quantidade inválida

Se a quantidade for inválida (zero, negativa ou um valor decimal para um produto cuja unidade é `UN`):

1. O sistema rejeita a operação.
2. O sistema informa ao operador a regra de validação.
3. Nenhuma movimentação é criada.
4. O estoque permanece inalterado.

### A2 — Produto não encontrado

O sistema rejeita a operação.

Nenhuma movimentação é criada.

### A3 — Produto inativo

O sistema rejeita a entrada de estoque para um produto inativo (`INV-008`, `BD-07`).

A operação é rejeitada sem criar uma movimentação. O produto deve ser reativado antes.

## Pós-condições

Existe uma nova movimentação positiva de estoque.

O saldo de estoque do produto aumentou pela quantidade especificada.

---

# 11. UC-M1-08 — Ajustar Estoque

## Objetivo

Corrigir o estoque registrado para corresponder à quantidade física (`ADJUSTMENT`).

## Pré-condições

* O produto existe.
* O produto está ativo.

## Fluxo Principal

1. O operador seleciona um produto.
2. O sistema exibe o saldo atual.
3. O operador escolhe ajustar o estoque.
4. O operador especifica o ajuste de quantidade com sinal (`BD-04`):
   - A quantidade não pode ser zero;
   - Valores positivos aumentam o estoque; valores negativos o diminuem;
   - Se `base_unit` for `UN`, a quantidade deve ser um número inteiro;
   - Se `base_unit` for `KG`, `G`, `L` ou `ML`, a quantidade pode ser decimal.
5. O operador envia o ajuste.
6. O sistema calcula o saldo resultante: `current_balance + adjustment`.
7. O sistema verifica se o saldo resultante não será negativo (`INV-006`).
8. Com serialização transacional (`ADR-001`), o sistema cria uma movimentação `ADJUSTMENT`.
9. O sistema atualiza ou deriva o saldo.
10. O sistema exibe o saldo resultante.

## Exemplo de Ajuste Positivo

Atual:

```text
Chocolate = 17 UN
```

Contagem física:

```text
Chocolate = 19 UN
```

Ajuste:

```text
+2
```

Resultado:

```text
Chocolate = 19 UN
```

## Exemplo de Ajuste Negativo

Atual:

```text
Chocolate = 20 UN
```

Contagem física:

```text
Chocolate = 17 UN
```

Ajuste:

```text
-3
```

Resultado:

```text
Chocolate = 17 UN
```

## Fluxos Alternativos

### A1 — O ajuste criaria estoque negativo

Atual:

```text
Chocolate = 2 UN
```

Ajuste solicitado:

```text
-3
```

O sistema deve:

1. rejeitar o ajuste;
2. informar ao operador que o estoque resultante ficaria negativo;
3. não criar nenhuma movimentação;
4. preservar o saldo atual.

Resultado:

```text
Chocolate = 2 UN
```

### A2 — Quantidade inválida

Se a quantidade for zero ou se for informada uma quantidade decimal para um produto cuja unidade é `UN`:

1. O sistema rejeita a operação.
2. Nenhuma movimentação é criada.
3. O saldo permanece inalterado.

### A3 — Produto não encontrado

O sistema rejeita a operação.

Nenhuma movimentação é criada.

### A4 — Produto inativo

O sistema rejeita o ajuste de estoque para um produto inativo (`INV-008`, `BD-07`).

Nenhuma movimentação é criada. O produto deve ser reativado antes.

## Segurança em Operações Concorrentes

Ajustes simultâneos direcionados ao mesmo produto são serializados no nível da transação do banco de dados (`ADR-001`). Dois ajustes negativos concorrentes que, individualmente, pareçam válidos com base em um saldo desatualizado não podem ser confirmados se seu efeito combinado produzir um saldo negativo.

## Comportamento Importante

Um ajuste nunca reescreve uma movimentação de estoque anterior.

Exemplo:

```text
Histórico:

+20
-3
```

Se for necessária outra correção de `-2`:

```text
Histórico:

+20
-3
-2
```

As movimentações existentes permanecem inalteradas.

---

# 12. UC-M1-09 — Visualizar Saldo de Estoque

## Objetivo

Permitir que o operador veja o estoque físico atual de um produto.

## Pré-condições

* O produto existe.

## Fluxo Principal

1. O operador seleciona um produto.
2. O sistema calcula ou recupera o saldo atual.
3. O sistema exibe:

   * produto;
   * unidade base;
   * quantidade atual.

## Exemplo

```text
Produto: Chocolate
Unidade: UN
Estoque disponível: 17
```

## Estoque Vazio

Se não houver nenhuma movimentação de estoque:

```text
Estoque disponível: 0
```

A ausência de estoque não deve ser tratada como um erro.

---

# 13. UC-M1-10 — Visualizar Histórico de Estoque

## Objetivo

Permitir que o operador entenda como o saldo atual de estoque foi formado.

## Pré-condições

* O produto existe.

## Fluxo Principal

1. O operador seleciona um produto.
2. O operador abre o histórico de estoque.
3. O sistema recupera as movimentações de estoque do produto.
4. O sistema exibe as movimentações em ordem cronológica.
5. O operador consegue identificar o efeito de cada movimentação.

## Exemplo

```text
Chocolate

Data        Tipo          Quantidade
-----------------------------------
10/09       ENTRY          +20
11/09       ADJUSTMENT      -3
12/09       ADJUSTMENT      +2
```

Saldo atual:

```text
19
```

## Comportamento Importante

Movimentações históricas não devem desaparecer por causa de correções posteriores.

O sistema deve preservar a auditabilidade das alterações de estoque.

---

# 14. UC-M1-11 — Verificar Disponibilidade de Estoque

## Objetivo

Determinar se um produto tem estoque suficiente para a quantidade solicitada.

## Pré-condições

* O produto existe.

## Fluxo Principal

1. Uma operação futura solicita uma quantidade de um produto.
2. O sistema obtém o saldo atual de estoque.
3. O sistema compara a quantidade disponível com a quantidade solicitada.
4. O sistema informa o resultado.

## Exemplo — Disponível

```text
Disponível: 10
Necessário:  4

Resultado:
Available
Falta: 0
```

## Exemplo — Insuficiente

```text
Disponível: 2
Necessário: 5

Resultado:
Estoque insuficiente
Falta: 3
```

## Comportamento Importante

Um resultado de estoque insuficiente não modifica o estoque.

Ele não cria uma movimentação negativa.

Ele não impede que o produto seja incluído em uma cesta futura ou em uma venda em rascunho.

O processo futuro de confirmação da venda determinará se há estoque suficiente antes de deduzi-lo.

---

# 15. Regras de Negócio Comuns aos Casos de Uso

As regras a seguir se aplicam a vários casos de uso.

## 15.1 Estoque Físico Não Negativo

Nenhum caso de uso pode criar uma movimentação de estoque que produza um saldo físico negativo.

```text
Atual = 2
Redução solicitada = 3

Resultado:
Rejeitada
```

---

## 15.2 Movimentações Históricas São Preservadas

Nenhuma operação de produto ou estoque pode reescrever movimentações de estoque anteriores. As correções são representadas por novas movimentações.

As correções são representadas por novas movimentações.

---

## 15.3 A Desativação do Produto Não é Destrutiva

Desativar um produto não:

* exclui o produto;
* exclui o estoque;
* exclui o histórico;
* altera o saldo atual.

---

## 15.4 Estoque Insuficiente Não Torna o Produto Inválido

Um produto com estoque insuficiente continua sendo um produto válido.

Exemplo:

```text
Produto existe: Sim
Ativo: Sim
Estoque: 0
```

O produto continua válido.

Sua disponibilidade apenas indica:

```text
Estoque insuficiente
```

---

## 15.5 O Estoque Não é Reservado

M1 não reserva estoque.

Verificar a disponibilidade não altera o estoque.

Criar um produto não altera o estoque.

A operação futura de confirmação da venda será responsável pela dedução efetiva.

---

# 16. Cenário Operacional Comum

O cenário a seguir combina os principais casos de uso de M1.

## Cenário

A Casa Afeto começa sem estoque de Chocolate.

### Etapa 1 — Criar Produto

```text
Chocolate
Unidade: UN
```

Estoque:

```text
0
```

### Etapa 2 — Adicionar Estoque

O operador recebe 20 unidades.

```text
+20
```

Estoque:

```text
20
```

### Etapa 3 — Correção Física

O operador conta o estoque e encontra apenas 17 unidades.

```text
-3
```

Estoque:

```text
17
```

Histórico:

```text
+20
-3
```

### Etapa 4 — Verificar Disponibilidade

Uma cesta futura exige:

```text
20 Chocolate
```

O sistema informa:

```text
Disponível: 17
Necessário: 20
Falta: 3
```

O estoque permanece:

```text
17
```

### Etapa 5 — Repor Estoque

O operador recebe mais 10 unidades.

```text
+10
```

Estoque:

```text
27
```

### Etapa 6 — Verificar Novamente

Necessário:

```text
20
```

Disponível:

```text
27
```

Resultado:

```text
Disponível
```

### Etapa 7 — Desativar Produto

O operador decide que o produto não deve mais ser usado.

Produto:

```text
Ativo: Não
```

O estoque permanece:

```text
27
```

O histórico permanece intacto.

---

# 17. Exemplo de Operação Inválida

A operação a seguir nunca deve ser permitida.

Atual:

```text
Estoque = 5
```

A solicitação do operador:

```text
Ajuste = -8
```

O sistema calcula:

```text
5 - 8 = -3
```

Como o estoque físico não pode se tornar negativo:

```text
Operação = Rejeitada
```

O estado resultante permanece:

```text
Estoque = 5
```

Nenhuma movimentação `-8` é criada.

---

# 18. Interação com Marcos Futuros

M1 estabelece o comportamento de estoque usado por marcos posteriores.

### M2 — Cestas (Baskets)

M2 pode:

* selecionar produtos;
* consultar a disponibilidade;
* avisar sobre estoque insuficiente.

M2 não deve deduzir estoque.

### M4 — Vendas (Sales)

M4 pode criar vendas em rascunho que contenham produtos com estoque insuficiente.

M4 não deve deduzir estoque apenas porque uma venda existe.

### M5 — Pagamentos (Payments)

M5 usará o comportamento de estoque de M1 ao confirmar vendas.

Antes da confirmação:

```text
Verificar disponibilidade
```

Se houver estoque suficiente:

```text
Deduzir estoque
```

Se o estoque for insuficiente:

```text
Não criar estoque negativo
A confirmação não pode prosseguir
```

O próprio M1 não implementa esses fluxos futuros.

---

# 19. Princípios de Tratamento de Erros

Erros devem ser apresentados em termos de negócio.

Prefira:

```text
"Estoque insuficiente. Disponível: 2 UN. Necessário: 5 UN."
```

em vez de:

```text
"Violação de restrição: inventory_balance >= 0"
```

Detalhes técnicos devem ser registrados em log ou tratados internamente quando apropriado.

O usuário deve receber informações suficientes para entender qual ação é necessária.

---

# 20. Rastreabilidade dos Casos de Uso

| Caso de Uso                               | Seção da Especificação       | Regras de Negócio                                |
| ----------------------------------------- | ---------------------------- | ------------------------------------------------ |
| UC-M1-01 Criar Produto                    | Produto                      | PROD-001, PROD-002                               |
| UC-M1-02 Editar Produto                   | Edição de Produto            | PROD-001 (mutabilidade), preservação histórica   |
| UC-M1-03 Ativar Produto                   | Ativação de Produto          | ativação de produto                              |
| UC-M1-04 Desativar Produto                | Ativação de Produto          | desativação não destrutiva, INV-008              |
| UC-M1-05 Listar Produtos                  | Listagem de Produtos         | —                                                |
| UC-M1-06 Buscar Produtos                  | Busca de Produtos            | SEARCH-001                                       |
| UC-M1-07 Adicionar Estoque                | Entrada de Estoque            | INV-001, INV-008                                 |
| UC-M1-08 Ajustar Estoque                  | Ajuste de Estoque             | INV-001, INV-002, INV-006, INV-008               |
| UC-M1-09 Visualizar Saldo de Estoque      | Saldo de Estoque             | INV-001                                          |
| UC-M1-10 Visualizar Histórico de Estoque  | Histórico de Movimentações   | INV-002                                          |
| UC-M1-11 Verificar Disponibilidade        | Disponibilidade de Estoque   | INV-003, INV-006                                 |

---

# 21. Limites da Implementação

Esses casos de uso definem comportamentos de negócio observáveis.

Eles não exigem uma implementação técnica específica.

A implementação não deve introduzir comportamento de negócio adicional apenas porque um framework técnico torna isso conveniente.

Se uma decisão técnica alterar algum desses comportamentos, o agente deve identificar o conflito antes da implementação.

---

# 22. Conclusão dos Casos de Uso de M1

A documentação dos casos de uso está completa quando todas as operações de M1 dentro do escopo têm:

* um ator definido;
* um objetivo definido;
* pré-condições definidas, quando aplicável;
* um fluxo normal;
* fluxos alternativos/de erro relevantes;
* pós-condições definidas, quando aplicável;
* rastreabilidade até a especificação de M1.

O próximo artefato é:

```text
docs/milestones/m1-products-inventory/acceptance-criteria.md
```

Os critérios de aceitação traduzirão esses casos de uso em condições objetivas e testáveis para determinar se a implementação está correta.
