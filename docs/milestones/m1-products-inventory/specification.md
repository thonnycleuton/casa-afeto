# M1 — Especificação de Produtos e Estoque

**Versão do documento:** 0.1
**Status:** Pronto para implementação
**Marco:** M1 — Produtos e Estoque (Products & Inventory)
**Fase:** 1 — Operações Centrais (Core Operations)

---

# 1. Finalidade

M1 estabelece as capacidades básicas de Produto e Estoque exigidas pelo sistema da Casa Afeto.

O marco deve permitir que a Casa Afeto:

* cadastre produtos;
* gerencie a disponibilidade de produtos;
* mantenha o estoque físico;
* registre entradas de estoque;
* registre ajustes de estoque;
* visualize saldos atuais de estoque;
* visualize o histórico de movimentações de estoque;
* identifique estoque insuficiente.

M1 é a base para os marcos de Cestas, Vendas e Pagamentos.

---

# 2. Escopo

## 2.1 Dentro do escopo

M1 inclui:

### Produto

* criar produto;
* editar produto;
* ativar produto;
* desativar produto;
* listar produtos;
* buscar produtos;
* identificar a unidade de estoque do produto.

### Estoque

* registrar entradas positivas de estoque;
* registrar ajustes de estoque;
* calcular o saldo atual de estoque;
* exibir a disponibilidade de estoque;
* exibir o histórico de movimentações de estoque;
* impedir estoque físico negativo.

---

# 3. Explicitamente fora do escopo

O seguinte não deve ser implementado como parte de M1:

* entidade/fluxo de Compra;
* entidade/fluxo de PurchaseItem;
* gestão de fornecedores;
* InventoryLot;
* datas de vencimento;
* FEFO;
* consumo automático de estoque;
* dedução de estoque relacionada a vendas;
* dedução de estoque relacionada a cestas;
* estoque reservado;
* solicitações de reposição;
* alertas de vencimento;
* fluxo de gestão de perdas;
* produção;
* receitas;
* produção interna;
* gestão de pagamentos;
* vendas;
* cestas;
* clientes;
* notificações;
* painéis;
* análises avançadas de estoque.

Se a implementação parecer exigir uma dessas capacidades, o agente deve parar e determinar se o requisito é genuinamente necessário para M1.

Não deve expandir o escopo silenciosamente.

---

# 4. Dependências

M1 depende de:

* `docs/product/vision.md`
* `docs/product/roadmap.md`
* `docs/domain/business-contract.md`
* `AGENTS.md`

Nenhum outro marco é necessário.

---

# 5. Conceitos de domínio

M1 introduz dois conceitos principais:

```text
Produto
Estoque
```

O estoque é representado por meio de movimentações em vez de uma operação que apenas sobrescreve uma quantidade em estoque.

Conceitualmente:

```text
Produto
   │
   └── Movimentações de Estoque
             │
             ├── Entrada
             └── Ajuste
```

O saldo atual representa a quantidade física resultante.

---

# 6. Produto

## 6.1 Definição de produto

Um Produto representa um item que pode ser usado pela Casa Afeto em seus processos operacionais.

Exemplos:

* Chocolate
* Juice
* Coffee
* Cereal Bar
* Mug
* Card
* Cake
* Packaging

M1 não distingue entre produtos comprados e produtos produzidos internamente.

Essa distinção pertence a funcionalidade futura.

---

# 7. Requisitos de dados do produto

Um produto deve conter, no mínimo:

| Campo       | Obrigatório | Descrição                                                           |
| ----------- | ----------: | ------------------------------------------------------------------- |
| `id`        |         Sim | Identificador único do produto                                      |
| `name`      |         Sim | Nome do produto                                                     |
| `base_unit` |         Sim | Unidade controlada usada no estoque (`UN`, `KG`, `G`, `L`, `ML`)     |
| `active`    |         Sim | Se o produto está disponível para novas operações (inicialmente true) |

A implementação pode conter metadados técnicos, como:

* data de criação;
* data de atualização.

Esses campos são detalhes de implementação e não alteram o modelo de negócio.

---

# 8. Nome do produto

O nome do produto é obrigatório.

O sistema deve rejeitar um produto sem um nome significativo.

Nomes de produtos não são obrigatoriamente únicos em M1 (`PROD-002`). Dois produtos distintos podem ter o mesmo nome. Nenhuma restrição UNIQUE do banco de dados é aplicada ao nome do produto.

As regras exatas de validação para espaços em branco, tamanho máximo e caracteres permitidos devem seguir as convenções técnicas existentes do projeto.

---

# 9. Unidade base do estoque

Todo produto deve ter uma unidade base de estoque (`base_unit`).

### 9.1 Valores controlados da unidade

`base_unit` é um valor controlado (`PROD-001`). M1 suporta exatamente:

* `UN` — unidade
* `KG` — quilograma
* `G` — grama
* `L` — litro
* `ML` — mililitro

Qualquer outro valor de unidade deve ser rejeitado. M1 não implementa conversão genérica de unidades nem um catálogo configurável de unidades. Todas as quantidades em M1 são expressas na `base_unit` do produto.

### 9.2 Mutabilidade da unidade base

A `base_unit` de um produto só pode ser alterada enquanto o produto não possui movimentações de estoque.

Uma vez que o produto tenha pelo menos uma movimentação de estoque, sua `base_unit` torna-se imutável para preservar o significado semântico das movimentações históricas.

---

# 10. Ativação do produto

Produtos podem estar ativos ou inativos.

## Ativo

Um produto ativo está disponível para atividades operacionais e operações de estoque. Quando criado, um produto fica ativo por padrão.

## Inativo

Um produto inativo não pode ser selecionado para novas operações operacionais.

Além disso, um produto inativo **não pode receber nenhuma Entrada ou Ajuste de Estoque** (`INV-008`). Se um operador precisar modificar o estoque de um produto inativo, o produto deve ser reativado primeiro. A reativação não modifica o estoque.

A desativação não deve:

* excluir o produto;
* excluir o estoque;
* excluir movimentações de estoque;
* alterar informações históricas.

Referências históricas existentes a um produto inativo devem permanecer válidas.

---

# 11. Edição do produto

O usuário pode editar as informações do produto.

A edição de um produto não deve reescrever movimentações históricas de estoque. Por exemplo, alterar o nome de um produto não deve modificar os registros históricos de movimentação; eles continuam referenciando o mesmo produto.

### Regra de edição da unidade base

A `base_unit` de um produto só pode ser atualizada enquanto o produto não possui **movimentações de estoque**. Depois que qualquer movimentação de estoque tiver sido registrada para o produto, a edição da `base_unit` deve ser rejeitada.

---

# 12. Listagem de produtos

O sistema deve fornecer uma listagem de produtos.

A listagem deve permitir ao usuário identificar pelo menos:

* nome do produto;
* unidade base de estoque;
* estado ativo/inativo;
* saldo atual de estoque.

A representação exata na interface é um detalhe de implementação.

---

# 13. Busca de produtos

O sistema deve permitir que os produtos sejam pesquisados por nome (`SEARCH-001`).

Comportamento da busca:
* correspondência sem diferenciar maiúsculas e minúsculas;
* correspondência por substring no nome do produto.

Exemplos: `choc`, `Choc`, `CHOC` e `ChoC` correspondem a `Chocolate`.

M1 não exige e não deve implementar:
* busca difusa;
* infraestrutura de busca em texto completo;
* ranqueamento de relevância;
* filtros avançados;
* infraestrutura de indexação de busca.

---

# 14. Modelo de estoque

O estoque é representado como uma sequência de movimentações.

Conceitualmente:

```text
Estado inicial
    ↓
Movimento +20
    ↓
Saldo = 20
    ↓
Movimento -3
    ↓
Saldo = 17
```

O sistema deve preservar cada movimentação.

O saldo atual não deve exigir reescrita do histórico.

---

# 15. Movimentação de estoque

Uma movimentação de estoque representa uma mudança na quantidade física do produto.

M1 exige as seguintes categorias de movimentação:

### Entrada

Adiciona quantidade física (`ENTRY`).

Regras (`BD-03`):
* A quantidade DEVE ser maior que zero (> 0);
* A quantidade NÃO DEVE ser zero nem negativa;
* `UN` aceita apenas quantidades inteiras positivas (decimais rejeitados);
* `KG`, `G`, `L` e `ML` aceitam quantidades decimais positivas.

Exemplo:
```text
+20 Chocolate (UN)
+0.5 Leite (L)
```

### Ajuste

Corrige a quantidade física registrada (`ADJUSTMENT`).

Um ajuste pode ser positivo ou negativo.

Regras (`BD-04`):
* A quantidade NÃO DEVE ser zero (0 rejeitado);
* Valores positivos aumentam o estoque; valores negativos diminuem o estoque;
* `UN` aceita apenas quantidades inteiras (decimais rejeitados);
* `KG`, `G`, `L` e `ML` aceitam quantidades decimais;
* Um ajuste negativo nunca deve fazer com que o saldo físico resultante fique negativo.

Exemplo:
```text
+3 Chocolate (UN)
-2 Chocolate (UN)
-0.25 Farinha (KG)
```

M1 não implementa tipos de movimentação para venda, compra, vencimento, perdas ou produção.

---

# 16. Dados da movimentação de estoque

Uma movimentação deve conter, no mínimo:

| Campo        | Obrigatório | Descrição                            |
| ------------ | ----------: | ------------------------------------ |
| `id`         |         Sim | Identificador único da movimentação  |
| `product_id` |         Sim | Produto afetado                     |
| `quantity`   |         Sim | Mudança de quantidade (com sinal)   |
| `type`       |         Sim | Categoria da movimentação (`ENTRY` / `ADJUSTMENT`) |
| `created_at` |         Sim | Data de criação da movimentação      |

A quantidade da movimentação deve preservar seu sinal ou de outra forma representar de forma inequívoca a direção da movimentação.

```text
ENTRY       +20
ADJUSTMENT   -3
```

### Campos explicitamente excluídos (fora do escopo de M1)

O modelo de dados M1 para `InventoryMovement` exclui estritamente campos especulativos:
* `reason`
* `notes`
* `reference`
* `user_id`
* `sale_id`
* `lot_id`

Esses pertencem a marcos futuros e não devem ser adicionados aos modelos de M1.

---

# 17. Imutabilidade da movimentação

Uma vez que uma movimentação de estoque tenha sido registrada, ela não deve ser reescrita silenciosamente para alterar o histórico de estoque.

O histórico de estoque é importante.

Se uma movimentação incorreta foi registrada, a correção deve ser representada por outra movimentação.

Exemplo:

```text
Original:

+20

Correção:

-3

Saldo atual:

17
```

A movimentação original `+20` permanece parte do histórico.

---

# 18. Saldo de estoque

O saldo de estoque de um produto é a quantidade resultante de suas movimentações de estoque.

Conceitualmente:

```text
Saldo =
somatório(todas as movimentações de estoque aplicáveis)
```

Exemplo:

```text
+20
-3
+5
-2

Saldo = 20
```

A implementação pode manter um saldo materializado/atual para desempenho, se necessário, mas essa otimização não pode substituir o histórico de movimentações como fonte de verdade.

Para M1, a implementação correta mais simples deve ser preferida.

---

# 19. Política de estoque negativo

O estoque físico nunca deve ficar negativo (`INV-006`).

Esse invariante é absoluto. Antes de criar uma movimentação de estoque negativa, o sistema deve verificar que o saldo resultante permaneça maior ou igual a zero.

Além disso, esse invariante **deve valer sob operações concorrentes** (`BD-05`, `ADR-001`). Condições de corrida em que ajustes ou entradas concorrentes avaliam um saldo antigo e produzem um saldo negativo devem ser evitadas por meio de isolamento de transação no banco e bloqueio por linha (`SELECT FOR UPDATE` ou equivalente).

Exemplo:

```text
Saldo atual = 5

Ajuste = -3

Resultado = 2

Permitido
```

Mas:

```text
Saldo atual = 2

Ajuste = -3

Resultado = -1

Rejeitado
```

A operação rejeitada não deve criar uma movimentação.

---

# 20. Estoque insuficiente

M1 deve expor se um produto possui estoque insuficiente para uma quantidade solicitada.

Exemplo:

```text
Disponível: 2
Solicitado:  5

Falta: 3
```

O sistema deve ser capaz de representar esse estado sem modificar o estoque.

Isso é importante porque funcionalidade futura de cestas e vendas pode precisar registrar uma demanda antes que o estoque fique disponível.

M1, portanto, não deve tratar "estoque insuficiente" como equivalente a "produto inválido".

---

# 21. Entrada de estoque

M1 deve fornecer uma forma de adicionar estoque físico manualmente.

Exemplo:

```text
Produto: Chocolate
Quantidade: 20
```

Resultado:

```text
Saldo de estoque: 20
```

A operação cria uma movimentação de estoque.

O sistema não deve apenas sobrescrever o saldo anterior.

---

# 22. Ajuste de estoque

M1 deve fornecer uma forma de corrigir o estoque físico.

Exemplo:

```text
Registrado:
20

Físico:
17

Ajuste:
-3

Novo saldo:
17
```

Ajustes positivos também são permitidos:

```text
Registrado:
17

Físico:
19

Ajuste:
+2

Novo saldo:
19
```

Os ajustes devem preservar o histórico de movimentações.

---

# 23. Histórico de movimentações de estoque

O sistema deve fornecer uma forma de inspecionar as movimentações associadas a um produto.

No mínimo, o histórico deve permitir ao usuário identificar:

* data/hora;
* tipo de movimentação (`ENTRY` ou `ADJUSTMENT`);
* mudança de quantidade;
* produto.

Cada movimentação preserva sua quantidade histórica, tipo e timestamp. Um saldo em execução ou resultante por linha de movimentação **não é obrigatório** e não é armazenado. O saldo atual é obtido por meio da capacidade de saldo de estoque.

O sistema deve apresentar as movimentações em uma ordem cronológica clara.

A apresentação exata é uma decisão de implementação.

---

# 24. Integridade transacional e concorrência do estoque

As mudanças de estoque devem ser atômicas do ponto de vista do negócio.

Para uma operação de estoque:

```text
Validar entrada
    ↓
Bloquear o estado de estoque do produto (SELECT FOR UPDATE)
    ↓
Calcular saldo e validar que o saldo resultante >= 0
    ↓
Criar movimentação imutável
    ↓
Confirmar transação
```

O sistema não deve deixar uma operação de estoque parcialmente concluída.

Modificações concorrentes de estoque para o mesmo produto devem ser serializadas no nível da transação do banco (`ADR-001`) para garantir que `INV-006` não possa ser violado por condições de corrida.

---

# 25. Desativação do produto e estoque

Desativar um produto não remove nem altera seu estoque.

Exemplo:

```text
Chocolate
Estoque: 15

Desativar produto

Chocolate
Ativo: false
Estoque: 15
```

O histórico de estoque permanece intacto.

Um produto inativo **não pode receber nenhuma Entrada ou Ajuste de Estoque** (`INV-008`). Se um operador precisar ajustar ou adicionar estoque para um produto inativo, o produto deve ser reativado primeiro. A reativação não altera o estoque.

M1 exige que produtos inativos não possam ser selecionados para novas operações que exijam produtos ativos.

---

# 26. Regras de negócio usadas por M1

M1 deve implementar as seguintes regras do Contrato de Negócio:

### INV-001 — Estoque baseado em movimentações

As mudanças de estoque são representadas por movimentações de estoque.

### INV-002 — Preservação do histórico de estoque

As correções de estoque preservam o histórico original das movimentações.

### INV-006 — Sem estoque físico negativo

O sistema não deve criar uma movimentação de estoque que faça com que o saldo físico disponível de um produto fique negativo. Esse invariante é absoluto e se aplica estritamente a operações concorrentes (`ADR-001`).

### INV-003 — Estoque insuficiente pode ser selecionado

Um produto com estoque insuficiente pode ser selecionado para operações futuras de cesta/venda, desde que a falta seja claramente indicada. M1 fornece o estado e as informações de estoque necessárias para que marcos posteriores implementem esse comportamento.

### INV-008 — Produtos inativos não podem receber operações de estoque

Um produto inativo não pode receber nenhuma Entrada ou Ajuste de Estoque.

### PROD-001 — Unidades base controladas e mutabilidade

A `base_unit` de um produto deve ser uma de: `UN`, `KG`, `G`, `L`, `ML`. Ela só pode ser editada enquanto o produto não possui movimentações de estoque; quando uma movimentação existe, `base_unit` se torna imutável.

### PROD-002 — Não unicidade do nome do produto

Nomes de produtos não são obrigatórios como únicos em M1.

### SEARCH-001 — Semântica da busca de produtos

A busca de produtos é sem distinção de maiúsculas e minúsculas e corresponde a substrings dentro do nome do produto.

---

# 27. Resumo de casos de uso

M1 deve suportar estes casos de uso principais:

```text
UC-M1-01 Criar Produto
UC-M1-02 Editar Produto
UC-M1-03 Ativar Produto
UC-M1-04 Desativar Produto
UC-M1-05 Listar Produtos
UC-M1-06 Buscar Produtos
UC-M1-07 Adicionar Estoque
UC-M1-08 Ajustar Estoque
UC-M1-09 Visualizar Saldo de Estoque
UC-M1-10 Visualizar Histórico de Estoque
UC-M1-11 Verificar Disponibilidade de Estoque
```

Fluxos detalhados do usuário ficam em `use-cases.md`.

---

# 28. Tratamento de erros

O sistema deve fornecer retorno claro para operações inválidas.

No mínimo:

### Produto

* nome do produto ausente;
* unidade base inválida (não está entre `UN`, `KG`, `G`, `L`, `ML`);
* tentativa de modificar `base_unit` após a existência de movimentações de estoque;
* tentativa de usar um produto inativo quando um produto ativo é exigido.

### Estoque

* quantidade de Entrada inválida (zero, negativa ou não inteira para `UN`);
* quantidade de Ajuste inválida (zero ou não inteira para `UN`);
* ajuste de estoque que resultaria em saldo negativo (< 0);
* Entrada ou Ajuste de Estoque em produto inativo;
* identificador de produto desconhecido;
* tipo de movimentação inválido.

Mensagens de erro devem explicar o que impediu a operação.

A implementação não deve expor detalhes técnicos desnecessários ao usuário.

---

# 29. Integridade de dados

A implementação deve preservar os seguintes invariantes:

### Invariante do produto

Cada movimentação de estoque referencia um produto existente.

### Invariante de quantidade

As quantidades de estoque devem usar uma representação consistente de unidade, compatível com a `base_unit` do produto.

### Invariante de estoque negativo

O saldo físico de estoque resultante nunca deve ser negativo, incluindo em operações concorrentes.

### Invariante histórica

Movimentações existentes de estoque não devem ser reescritas ou excluídas silenciosamente como parte de um ajuste ou correção.

### Invariante de ativação

A desativação do produto não remove informações históricas.

---

# 30. Requisitos de teste

M1 deve incluir testes automatizados para o comportamento de negócio estabelecido.

No mínimo, os testes devem cobrir:

## Produto

* criar produto;
* editar produto;
* ativar produto;
* desativar produto;
* listar produtos;
* buscar produtos.

## Estoque

* adicionar estoque;
* calcular saldo;
* criar ajuste positivo;
* criar ajuste negativo;
* preservar histórico de movimentações;
* rejeitar saldo resultante negativo;
* identificar estoque insuficiente;
* manter estoque após desativação do produto.

## Integridade de dados

* movimentação referencia um produto válido;
* operação inválida de estoque não cria movimentação;
* ajuste negativo rejeitado não altera o saldo.

Os testes devem focar no comportamento de negócio em vez de detalhes de implementação.

---

# 31. Limite de aceitação

M1 está concluído quando o seguinte cenário funcionar:

```text
1. Criar Chocolate
2. Definir base unit = UN
3. Verificar que o produto está ativo
4. Adicionar 20 unidades de Chocolate
5. Verificar saldo = 20
6. Adicionar ajuste -3
7. Verificar saldo = 17
8. Verificar que as duas movimentações permanecem no histórico
9. Tentar ajuste -18
10. Operação rejeitada
11. Verificar que o saldo permanece 17
12. Verificar que nenhuma movimentação inválida foi criada
13. Verificar disponibilidade para 20 unidades
14. Sistema informa estoque insuficiente
15. Desativar Chocolate
16. Verificar que o histórico de estoque continua disponível
17. Verificar que Chocolate inativo não pode ser selecionado para novas operações
```

---

# 32. Restrições de implementação

A implementação deve seguir as regras de nível de projeto em `AGENTS.md`.

Em particular:

* não introduzir arquitetura especulativa;
* não implementar marcos futuros;
* não criar abstrações genéricas sem necessidade atual;
* não introduzir arquitetura de repositório/serviço/evento apenas porque pode ser útil depois;
* não implementar Purchase ou InventoryLot;
* não implementar dedução de estoque de venda;
* não implementar estoque negativo;
* não inventar regras de negócio adicionais.

A implementação mais simples que satisfaça esta especificação é preferida.

---

# 33. Decisões de Arquitetura

M1 não prescreve:

* linguagem de programação/estrutura de framework;
* esquema exato do banco de dados;
* ORM;
* arquitetura de API;
* estrutura de componentes do frontend;
* padrão de repositório;
* camada de serviço;
* injeção de dependências;
* cache;
* sistemas de eventos.

Essas são decisões de implementação.

O agente deve usar as convenções técnicas existentes no projeto, quando houver.

Se uma decisão arquitetural significativa se tornar necessária, ela deve ser apresentada explicitamente e documentada como ADR quando apropriado.

---

# 34. Sequência de Implementação

A ordem de implementação recomendada é:

```text
1. Modelo do Produto
       ↓
2. Persistência do Produto
       ↓
3. Operações de Produto
       ↓
4. Ativação/desativação do Produto
       ↓
5. Modelo de Movimentação de Estoque
       ↓
6. Saldo de Estoque
       ↓
7. Entrada de Estoque
       ↓
8. Ajuste de Estoque
       ↓
9. Proteção contra Estoque Negativo
       ↓
10. Histórico de Estoque
       ↓
11. Verificação de Disponibilidade
       ↓
12. Testes Automatizados
       ↓
13. Validação Manual
```

O agente pode ajustar essa sequência se a arquitetura existente do projeto tornar outra ordem mais simples, mas não deve ampliar o escopo de negócio.

---

# 35. Critérios de Conclusão

M1 só pode ser considerado concluído quando:

* todas as funcionalidades dentro do escopo estiverem implementadas;
* todas as regras de negócio estabelecidas para M1 estiverem cobertas;
* os testes automatizados passarem;
* estoque negativo for impedido;
* movimentações históricas de estoque forem preservadas;
* a ativação/desativação de produtos funcionar;
* a disponibilidade do estoque puder ser identificada;
* nenhuma funcionalidade de M2 ou posterior tiver sido introduzida;
* a validação manual tiver sido concluída;
* o usuário tiver aprovado explicitamente o marco.

---

# 36. Próximos Documentos

Antes do início da implementação, M1 deve ter os seguintes documentos de apoio:

```text
docs/milestones/m1-products-inventory/
│
├── specification.md
├── use-cases.md
├── acceptance-criteria.md
└── validation.md
```

Este documento define **o que M1 deve fazer**.

Os outros documentos definem:

* `use-cases.md` → como o usuário realiza as operações;
* `acceptance-criteria.md` → condições objetivas que determinam se cada comportamento está correto;
* `validation.md` → verificação manual realizada após a implementação.

---

# 37. Rastreabilidade

M1 segue a cadeia de documentação do projeto:

```text
business-contract.md
        ↓
M1 specification.md
        ↓
use-cases.md
        ↓
acceptance-criteria.md
        ↓
implementation
        ↓
automated tests
        ↓
validation.md
```

A implementação não deve introduzir comportamento de negócio que não possa ser rastreado até um requisito estabelecido ou uma decisão técnica explicitamente aprovada.

---

# 38. Princípio Orientador de M1

M1 deve fornecer uma base confiável e simples para o restante do sistema.

Ele deve responder a três perguntas básicas:

```text
Quais produtos temos?
        ↓
Quanto estoque físico temos?
        ↓
O que aconteceu com esse estoque?
```

Nada além do necessário para responder a essas perguntas pertence a M1.
