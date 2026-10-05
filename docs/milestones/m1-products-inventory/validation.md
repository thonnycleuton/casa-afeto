# Casa Afeto — Validação Manual de M1

**Marco:** M1 — Produtos e Estoque (Products & Inventory)
**Documento:** Validação manual
**Versão:** 0.1
**Status:** Rascunho
**Depende de:** `specification.md`, `use-cases.md`, `acceptance-criteria.md`

---

## 1. Finalidade

Este documento define o procedimento de validação manual para M1 — Produtos e Estoque (Products & Inventory).

O objetivo é verificar que o sistema implementado se comporta corretamente do ponto de vista de um operador da Casa Afeto.

Este documento é intencionalmente operacional.

Ele não define novas regras de negócio. Fornece um procedimento repetível para validar as regras já definidas em:

* `docs/domain/business-contract.md`
* `docs/milestones/m1-products-inventory/specification.md`
* `docs/milestones/m1-products-inventory/use-cases.md`
* `docs/milestones/m1-products-inventory/acceptance-criteria.md`

---

## 2. Princípios de validação

A validação manual deve verificar:

1. O comportamento esperado de negócio funciona.
2. Operações inválidas são rejeitadas com segurança.
3. O estoque não pode ficar negativo.
4. As movimentações históricas de estoque são preservadas.
5. A ativação/desativação do produto se comporta conforme especificado.
6. Nenhuma funcionalidade não relacionada é necessária para completar M1.
7. Operações rejeitadas não criam efeitos colaterais não intencionais.

O validador deve testar o sistema por meio de sua interface normal de usuário sempre que possível.

Inspeção do banco de dados pode ser usada quando necessário para investigar uma falha, mas manipulação do banco não deve ser usada para fazer um cenário de validação passar.

---

# 3. Pré-condições

Antes de iniciar a validação:

* A aplicação está em execução.
* O banco de dados está disponível.
* A aplicação pode criar e persistir produtos.
* A aplicação pode criar e persistir movimentações de estoque.
* Dados de teste anteriores não interferem na validação.

Se o ambiente contiver dados existentes, use produtos de teste claramente identificáveis.

Produto recomendado para teste:

> **Chocolate Test**

Unidade base:

> **UN**

Segundo produto opcional:

> **Suco Test**

Unidade base:

> **UN**

---

# 4. Convenção de resultado da validação

Cada cenário deve ser marcado como:

* **PASS** — o comportamento corresponde ao resultado esperado.
* **FAIL** — o comportamento difere do resultado esperado.
* **BLOCKED** — a validação não pode ser realizada por causa de um problema não relacionado do ambiente ou da implementação.

Registre observações relevantes quando um cenário falhar.

Não altere o resultado esperado apenas porque a implementação se comporta de forma diferente.

Se o comportamento esperado em si parecer incorreto ou incompleto, pare e revise a especificação antes de alterar a implementação.

---

# 5. Gestão de produtos

## VAL-M1-01 — Criar produto

### Etapas

1. Abra a área de gestão de produtos.
2. Crie um produto chamado `Chocolate Test`.
3. Defina a unidade base como `UN`.
4. Salve o produto.

### Resultado esperado

* O produto é criado com sucesso.
* O produto aparece na lista de produtos.
* O produto fica ativo por padrão, conforme a especificação atual.
* O produto não possui estoque, a menos que o estoque seja adicionado explicitamente.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-02 — Dados obrigatórios do produto

### Etapas

Tente criar um produto sem:

1. Nome.
2. Unidade base.

### Resultado esperado

O sistema rejeita a operação inválida e indica claramente a informação obrigatória ausente.

Nenhum produto incompleto é criado.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-03 — Editar produto

### Etapas

1. Abra `Chocolate Test`.
2. Altere o nome para `Chocolate Test Updated`.
3. Salve.
4. Reabra o produto.

### Resultado esperado

* O novo nome é persistido.
* O produto continua sendo o mesmo produto.
* O estoque existente não é alterado pela mudança de nome.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-04 — Desativar produto

### Etapas

1. Desative `Chocolate Test Updated`.
2. Retorne à lista de produtos.

### Resultado esperado

* O produto fica inativo.
* O produto não é excluído.
* O produto permanece visível onde produtos históricos/inativos devem ser visíveis.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-05 — Reativar produto

### Etapas

1. Reative o produto previamente desativado.
2. Retorne à lista de produtos.

### Resultado esperado

* O produto volta a ficar ativo.
* O estoque existente permanece inalterado.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

# 6. Entrada de estoque

## VAL-M1-06 — Adicionar estoque inicial

### Etapas

1. Verifique que `Chocolate Test Updated` esteja ativo.
2. Adicione `20 UN` ao estoque.
3. Salve a operação.
4. Abra o saldo de estoque.

### Resultado esperado

O saldo do produto é:

> **20 UN**

Existe uma movimentação correspondente de estoque.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-07 — Adicionar estoque adicional

### Etapas

1. Adicione mais `10 UN`.
2. Salve.
3. Verifique o saldo.

### Resultado esperado

O saldo fica:

> **30 UN**

A movimentação anterior permanece preservada.

Agora deve haver pelo menos duas movimentações de estoque associadas ao produto.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

# 7. Ajustes de estoque

## VAL-M1-08 — Ajuste positivo

### Etapas

1. Realize um ajuste positivo de estoque de `5 UN`.
2. Salve.
3. Verifique o saldo.

### Resultado esperado

O saldo fica:

> **35 UN**

Uma nova movimentação de ajuste é criada.

Movimentações anteriores permanecem inalteradas.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-09 — Ajuste negativo

### Etapas

1. Realize um ajuste negativo de `3 UN`.
2. Salve.
3. Verifique o saldo.

### Resultado esperado

O saldo fica:

> **32 UN**

Uma nova movimentação de ajuste é criada.

Movimentações anteriores permanecem inalteradas.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-10 — Ajuste igual ao saldo atual

### Etapas

1. Registre um ajuste negativo igual ao saldo atual.
2. Salve.
3. Verifique o saldo.

### Resultado esperado

A operação é aceita.

O saldo resultante é:

> **0 UN**

Zero em estoque é válido.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-11 — Tentativa de criar estoque negativo

### Etapas

Supondo que o saldo atual seja `0 UN`:

1. Tente um ajuste negativo de `1 UN`.
2. Envie a operação.

### Resultado esperado

A operação é rejeitada.

O estoque permanece:

> **0 UN**

Nenhuma movimentação representando a operação rejeitada é criada.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

# 8. Histórico de estoque

## VAL-M1-12 — Verificar histórico de movimentações

### Etapas

Abra o histórico de estoque para `Chocolate Test Updated`.

Revise todas as movimentações criadas nos cenários anteriores.

### Resultado esperado

O histórico mostra as movimentações individuais em vez de apenas o saldo atual.

A sequência deve refletir as operações realizadas.

Por exemplo:

| Operação            | Quantidade |
| ------------------- | ---------: |
| Entrada inicial     |       +20 |
| Entrada adicional  |       +10 |
| Ajuste positivo    |        +5 |
| Ajuste negativo    |        -3 |
| Ajuste de saldo    |       -32 |

O saldo resultante deve ser:

> **0 UN**

A operação negativa rejeitada não deve aparecer como uma movimentação válida de estoque.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-13 — Dados históricos são preservados

### Etapas

1. Altere o nome do produto novamente.
2. Revise o histórico de estoque.
3. Revise o saldo atual do produto.

### Resultado esperado

Alterar as informações do produto não exclui nem reescreve movimentações históricas de estoque.

O histórico permanece disponível.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

# 9. Disponibilidade de estoque

## VAL-M1-14 — Estoque suficiente

### Etapas

1. Adicione `10 UN` a `Chocolate Test`.
2. Verifique a disponibilidade para `5 UN`.

### Resultado esperado

O sistema informa que há estoque suficiente disponível.

O estoque permanece:

> **10 UN**

Verificar disponibilidade não modifica o estoque.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-15 — Estoque insuficiente

### Etapas

Com `10 UN` disponíveis:

1. Verifique a disponibilidade para `15 UN`.

### Resultado esperado

O sistema informa estoque insuficiente.

O produto permanece válido.

O estoque permanece:

> **10 UN**

Nenhum estoque negativo é criado.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

# 10. Desativação do produto e estoque

## VAL-M1-16 — A desativação não altera o estoque

### Etapas

1. Verifique que `Chocolate Test` tenha `10 UN`.
2. Desative o produto.
3. Verifique seu saldo de estoque.

### Resultado esperado

O produto fica inativo, mas seu estoque permanece:

> **10 UN**

A desativação não exclui nem modifica o estoque.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-17 — Comportamento do produto inativo

### Etapas

Com o produto inativo:

1. Tente uma entrada normal de estoque.
2. Tente um ajuste normal de estoque.

### Resultado esperado

O sistema segue o comportamento definido pela especificação atual de M1 para produtos inativos.

Se a operação for rejeitada, nenhuma movimentação de estoque é criada.

Se a implementação revelar que o comportamento de negócio para produtos inativos ainda não foi suficientemente definido, pare a validação e sinalize o comportamento para revisão da especificação, em vez de inventar uma regra durante a validação.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

# 11. Operações rejeitadas e efeitos colaterais

## VAL-M1-18 — Operação rejeitada de estoque não tem efeitos colaterais

### Etapas

1. Registre o saldo atual.
2. Tente uma operação inválida de estoque.
3. Envie-a.
4. Recarregue o estoque.
5. Revise o histórico de movimentações.

### Resultado esperado

* A operação é rejeitada.
* O saldo permanece inalterado.
* Nenhuma movimentação inválida é criada.
* Movimentações históricas existentes permanecem inalteradas.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

# 12. Fluxo operacional completo de M1

## VAL-M1-19 — Fluxo completo de produto para estoque

Este cenário valida o fluxo principal de M1 como uma sequência operacional única.

### Etapas

1. Crie um novo produto:

   * Nome: `Suco Test`
   * Unidade base: `UN`
2. Adicione `20 UN`.
3. Verifique saldo = `20 UN`.
4. Adicione `10 UN`.
5. Verifique saldo = `30 UN`.
6. Realize ajuste `-5 UN`.
7. Verifique saldo = `25 UN`.
8. Verifique disponibilidade para `20 UN`.
9. Verifique estoque suficiente.
10. Verifique disponibilidade para `30 UN`.
11. Verifique estoque insuficiente.
12. Revise o histórico de movimentações.

### Resultado esperado

O sistema mantém corretamente o estado do estoque ao longo do fluxo completo.

Saldo final:

> **25 UN**

O histórico contém todas as movimentações aceitas.

Verificações de disponibilidade não modificam o estoque.

Nenhuma operação cria estoque negativo.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

# 13. Verificações de Regressão

Após concluir os cenários de validação, faça uma verificação básica de regressão.

## VAL-M1-20 — Persistência de Dados

### Etapas

1. Feche ou recarregue a aplicação.
2. Volte à lista de produtos.
3. Abra o produto de teste.
4. Verifique o saldo de estoque.
5. Verifique o histórico de estoque.

### Resultado Esperado

Todos os dados aceitos anteriormente permanecem persistidos.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

## VAL-M1-21 — Nenhuma Alteração de Dados Não Intencional

### Etapas

Revise os produtos de teste e seus estoques após todos os cenários.

### Resultado Esperado

Somente as operações realizadas intencionalmente durante a validação afetaram os dados de teste.

Não há movimentações de estoque nem alterações de produto inesperadas.

### Resultado

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Observações:

---

# 14. Verificação de Escopo

As funcionalidades a seguir **não** devem ser necessárias para concluir M1:

* gestão de compras;
* itens de compra;
* fornecedores;
* lotes de estoque;
* datas de vencimento;
* seleção FEFO;
* vendas;
* cestas;
* templates de cesta;
* clientes;
* pagamentos;
* confirmação de pagamento;
* dedução de estoque por vendas;
* estoque reservado;
* fluxo de reposição;
* gestão de perdas;
* produção/receitas;
* notificações;
* painéis avançados;
* análises avançadas.

Se a validação exigir qualquer uma das funcionalidades acima, pare e determine se:

1. M1 foi implementado incorretamente com uma dependência de funcionalidade futura; ou
2. a especificação realmente precisa ser alterada.

Não resolva o problema ampliando silenciosamente o escopo de M1.

---

# 15. Lista de Verificação Final da Validação

Antes de aceitar M1, confirme:

* [ ] Produtos podem ser criados.
* [ ] As informações obrigatórias do produto são validadas.
* [ ] Produtos podem ser editados.
* [ ] Produtos podem ser ativados/desativados.
* [ ] A desativação não exclui informações históricas.
* [ ] É possível adicionar estoque.
* [ ] É possível realizar ajustes positivos de estoque.
* [ ] É possível realizar ajustes negativos quando há estoque suficiente.
* [ ] Estoque zero é válido.
* [ ] Não é possível criar estoque físico negativo.
* [ ] As movimentações de estoque são preservadas.
* [ ] O saldo de estoque reflete o histórico de movimentações.
* [ ] É possível verificar a disponibilidade sem alterar o estoque.
* [ ] Estoque insuficiente é informado sem criar estoque negativo.
* [ ] Operações rejeitadas não criam efeitos colaterais não intencionais.
* [ ] Os dados persistem após recarregar/reiniciar a aplicação.
* [ ] M1 pode ser operado sem exigir marcos futuros.

---

# 16. Resumo da Validação

**Data da validação:** __________________

**Ambiente:** __________________

**Versão da aplicação / commit:** __________________

**Validador:** __________________

**Resultado:**

* [ ] ACEITO
* [ ] ACEITO COM PROBLEMAS
* [ ] REJEITADO
* [ ] BLOCKED

### Problemas Encontrados

| ID | Cenário | Descrição | Gravidade | Status |
| -- | ------- | --------- | --------- | ------ |
|    |          |             |          |        |
|    |          |             |          |        |
|    |          |             |          |        |

---

# 17. Decisão de Aceitação

M1 só deve ser considerado concluído quando:

1. A implementação satisfizer os critérios de aceitação de M1.
2. Os cenários de validação manual passarem ou houver exceções explicitamente revisadas.
3. Não restar nenhum problema crítico de integridade de dados.
4. O estoque físico não puder se tornar negativo.
5. As movimentações históricas de estoque permanecerem preservadas.
6. Nenhuma ampliação de escopo não aprovada tiver sido introduzida.
7. O operador puder executar com sucesso o fluxo completo de M1.

A decisão final de aceitação cabe ao proprietário humano do produto.

---

# 18. Rastreabilidade

O fluxo de validação segue:

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
        ↓
Aprovação Humana
```

A validação manual não substitui os testes automatizados.

Os testes automatizados verificam o comportamento da implementação de forma consistente.

A validação manual verifica se o comportamento implementado funciona corretamente do ponto de vista do operador.

---

# 19. Princípio Orientador

> Valide o comportamento de negócio, não a implementação.

O propósito deste documento não é provar que o código funciona internamente.

O propósito é verificar se a Casa Afeto pode realizar com segurança as operações definidas para M1 — Produtos e Estoque (Products & Inventory).

Se o sistema se comportar de forma diferente da especificação, investigue a divergência antes de alterar o código ou a especificação.
