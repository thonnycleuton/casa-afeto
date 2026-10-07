# Casa Afeto — Fase 1

**Versão do documento:** 0.1
**Status:** Ativo
**Fase:** 1 — Operações Centrais (Core Operations)

---

## 1. Finalidade

A Fase 1 estabelece a fundação operacional do Sistema de Gestão de Vendas da Casa Afeto.

O objetivo é implementar o conjunto mínimo de capacidades necessário para gerenciar:

* produtos;
* estoque;
* templates de cesta;
* cestas;
* clientes;
* vendas;
* pagamentos.

A fase deve resultar em um fluxo operacional coerente desde o cadastro de produtos até a confirmação da venda e a dedução de estoque.

A Fase 1 segue o princípio central de desenvolvimento do projeto:

> Construa pouco, valide, aprenda e depois construa a próxima coisa.

Cada marco deve ser implementado, testado e validado manualmente antes que o próximo marco comece.

---

## 2. Sequência de Desenvolvimento da Fase 1

A Fase 1 é dividida em cinco marcos:

```text
M1 — Produtos e Estoque (Products & Inventory)
        ↓
M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)
        ↓
M3 — Clientes (Customers)
        ↓
M4 — Vendas (Sales)
        ↓
M5 — Pagamentos (Payments)
```

A ordem é intencional.

Cada marco deve estabelecer a base mínima necessária para o próximo, sem implementar funcionalidade que pertença a marcos posteriores.

---

# 3. Marco M1 — Produtos e Estoque (Products & Inventory)

## Objetivo

Estabelecer a base básica de produto e estoque.

## Escopo

M1 inclui:

* criação de produto;
* edição de produto;
* ativação/desativação de produto;
* listagem de produtos;
* busca de produtos;
* unidade base de estoque;
* entrada manual de estoque;
* ajustes de estoque;
* saldo de estoque;
* histórico de movimentações de estoque;
* informações básicas de disponibilidade de estoque.

## Capacidades esperadas

O usuário deve ser capaz de:

1. Criar um produto.
2. Definir sua unidade base de estoque.
3. Editar suas informações básicas.
4. Ativar ou desativar o produto.
5. Adicionar estoque manualmente.
6. Ajustar o estoque.
7. Visualizar o saldo atual.
8. Visualizar o histórico de movimentações de estoque.
9. Identificar se um produto possui estoque disponível no momento.

## Comportamento importante de negócio

O estoque deve ser representado por meio de movimentações em vez de depender exclusivamente de um valor mutável de estoque.

O sistema deve preservar o histórico de alterações do estoque.

Uma correção de estoque não deve apagar nem reescrever movimentações anteriores.

Um produto com estoque insuficiente ainda pode ser selecionado para uma cesta futura, desde que a falta de estoque seja claramente visível ao usuário.

## Explicitamente fora de escopo

M1 não implementa:

* compras;
* fornecedores;
* itens de compra;
* lotes de estoque;
* datas de vencimento;
* FEFO/seleção por lote;
* reposição automática;
* gestão de perdas;
* produção;
* receitas;
* estoque reservado;
* dedução de estoque relacionada a vendas.

Essas capacidades podem ser introduzidas em fases ou marcos posteriores.

## Exemplo de validação de M1

Um fluxo básico de validação deve demonstrar:

```text
Criar Chocolate
    ↓
Adicionar 20 unidades
    ↓
Saldo = 20
    ↓
Ajustar -3
    ↓
Saldo = 17
    ↓
Revisar histórico de movimentações
    ↓
Desativar produto
    ↓
Verificar que produto inativo não pode ser selecionado para novas operações
```

## Dependência

Nenhuma.

M1 é a base da Fase 1.

---

# 4. Marco M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)

## Objetivo

Permitir que a Casa Afeto mantenha templates reutilizáveis e cestas concretas persistidas como composições de produtos. A cesta concreta do M2 não é uma venda nem possui cliente, dados de entrega ou estado comercial.

## Escopo

M2 inclui:

* criação de template de cesta;
* listagem, consulta e visualização de templates;
* edição de template de cesta;
* ativação/desativação de template;
* composição do template;
* quantidades de produtos em templates;
* criação de cesta persistida com nome, com ou sem template;
* listagem, consulta e visualização de cestas;
* criação de cesta a partir de template;
* criação de cesta sem template;
* personalização de cesta;
* adicionar produtos;
* remover produtos;
* substituir produtos;
* alterar quantidades;
* múltiplas quantidades do mesmo produto;
* persistência da composição da cesta;
* salvar e continuar editando cesta, inclusive vazia.

## Capacidades esperadas

O usuário deve ser capaz de:

1. Criar um template de cesta.
2. Consultar, visualizar e editar templates.
3. Ativar ou desativar templates.
4. Adicionar produtos ativos e quantidades a um template.
5. Criar uma cesta a partir de um template ativo cuja composição contenha somente produtos ativos.
6. Criar uma cesta sem template.
7. Consultar, visualizar e editar cestas.
8. Adicionar, remover ou substituir produtos e alterar quantidades.
9. Salvar uma cesta vazia.

## Comportamento importante de negócio

Uma cesta concreta deve ser independente de futuras alterações em seu template.

Por exemplo:

```text
Template A
    Chocolate × 2
    Suco × 1

        ↓ criar cesta

Cesta X
    Chocolate × 2
    Suco × 1

        ↓ alterar template depois

Template A
    Chocolate × 1
    Suco × 2
```

A cesta X deve continuar contendo:

```text
Chocolate × 2
Suco × 1
```

A mudança no template não deve alterar a cesta existente.

Uma cesta também pode ser personalizada após sua criação.

Ao criar uma cesta a partir de um template, sua composição é copiada naquele momento. Alterações posteriores em qualquer uma das composições não alteram a outra.

Uma cesta sem itens é válida e pode ser salva. A composição usa produtos identificados por `product_id` e quantidades na unidade base atual do produto, conforme as regras de unidade de M1. Referenciar um produto não é uma movimentação e não impede uma alteração de unidade base que M1 permita.

Produtos inativos já referenciados permanecem na composição e não impedem a edição de outros itens; devem ser identificados claramente. Produtos inativos não podem ser incluídos novamente nem substituídos automaticamente. Template inativo não pode originar uma nova cesta. Template que contenha produto inativo também não pode originar nova cesta até correção explícita.

Produto sem estoque suficiente pode ser incluído com aviso. A disponibilidade é informativa e pode mudar; M2 não reserva, deduz ou movimenta estoque.

## Explicitamente fora de escopo

M2 não implementa vendas, clientes, pagamentos, compras, fornecedores, lotes, validade, FEFO, reposição, reserva ou dedução de estoque, comunicação, notificações, dashboards, custo, preço, margem ou markup. Não existe relacionamento estrutural com Sale/Venda. Duplicação, exclusão e arquivamento de cestas ou templates não fazem parte das operações aprovadas.

## Dependência

M2 depende de M1, pois cestas e templates dependem de produtos e estoque.

## Status atual

```text
Status: Planejado
Implementation Gate: aguardando nova revisão humana da documentação
```

M1 está concluído. A documentação preparatória não autoriza a implementação de M2; o início depende de um novo M2 Implementation Gate.

---

# 5. Marco M3 — Clientes (Customers)

## Objetivo

Estabelecer o registro básico de cliente necessário para associar vendas a clientes.

## Escopo

M3 inclui:

* criação de clientes;
* edição de informações do cliente;
* ativação/desativação de clientes;
* listagem de clientes;
* busca de clientes;

## Capacidades esperadas

O usuário deve ser capaz de:

1. Criar um cliente.
2. Editar dados do cliente.
3. Buscar clientes.
4. Identificar um cliente ativo.
5. Desativar um cliente.

## Modelo de Negócio

Um cliente representa a pessoa que realiza a compra.

O destinatário de uma cesta não precisa ser representado como uma entidade separada de Cliente/Pessoa durante a Fase 1.

As informações do destinatário serão associadas ao contexto da cesta/entrega quando as vendas forem implementadas.

## Explicitamente fora de escopo

M3 não inclui:

* CRM;
* segmentação de clientes;
* campanhas para clientes;
* datas afetivas;
* gestão de aniversários;
* gestão de aniversários de casamento;
* lembretes automatizados;
* entidades de destinatário;
* integrações de comunicação;
* integração com WhatsApp.

Essas são capacidades futuras.

## Dependência

M2.

## Status atual

```text
Status: Planejado
```

---

# 6. Marco M4 — Vendas (Sales)

## Objetivo

Criar e gerenciar a transação comercial conectando clientes e cestas.

## Escopo

M4 inclui:

* criação de vendas;
* seleção de cliente;
* inclusão de uma ou mais cestas por venda;
* seleção de cestas;
* visualização da composição das cestas;
* edição da composição das cestas;
* informações do destinatário;
* endereço de entrega;
* data de entrega;
* observações da venda;
* total da venda;
* vendas em rascunho;
* edição de vendas.

## Capacidades Esperadas

O usuário deve ser capaz de:

1. Criar uma venda.
2. Selecionar um cliente.
3. Adicionar uma ou mais cestas.
4. Revisar a composição de cada cesta.
5. Modificar a composição da cesta quando necessário.
6. Definir as informações do destinatário.
7. Definir o endereço de entrega.
8. Definir a data de entrega.
9. Adicionar observações.
10. Revisar o total da venda.
11. Salvar a venda como rascunho.
12. Editar a venda antes da confirmação.

## Estrutura da Venda

Conceitualmente:

```text
Cliente
    │
    └── Venda
          │
          ├── Cesta
          │     └── Itens da Cesta
          │
          ├── Cesta
          │     └── Itens da Cesta
          │
          └── ...
```

Uma venda deve conter pelo menos uma cesta.

Uma venda pode conter várias cestas.

Cada cesta tem suas próprias informações de entrega/destinatário.

Várias cestas podem compartilhar o mesmo endereço.

## Ciclo de vida esperado

O ciclo operacional inicial esperado segue:

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

Também é esperada uma situação de cancelamento:

```text
DRAFT / CONFIRMED / PREPARING / READY
                  ↓
               CANCELLED
```

As regras exatas de transição serão definidas na especificação do marco.

## Comportamento Importante de Negócio

M4 introduz a venda, mas ainda não confirma a venda do ponto de vista do pagamento.

O estoque não deve ser deduzido apenas porque existe uma venda em rascunho.

O processamento de pagamentos e as regras de confirmação pertencem a M5.

## Explicitamente Fora de Escopo

M4 não implementa:

* registro de pagamentos;
* confirmação de pagamento;
* comprovantes de pagamento;
* regra de confirmação de 50%;
* regra de pagamento integral antes da entrega;
* dedução de estoque causada pela confirmação;
* gateways de pagamento;
* conciliação automática de pagamentos.

## Dependência

M1, M2 e M3.

## Status atual

```text
Status: Planejado
```

---

# 7. Marco M5 — Pagamentos (Payments)

## Objetivo

Conectar informações de pagamento ao ciclo de vida de vendas e estabelecer as regras para confirmação da venda e dedução de estoque.

## Escopo

M5 inclui:

* registrar pagamentos;
* pagamentos via PIX;
* pagamentos com cartão;
* valor do pagamento;
* comprovante de pagamento;
* status do pagamento;
* total pago;
* valor restante;
* confirmação da venda;
* dedução de estoque na confirmação;
* alterações na venda após a confirmação;
* ajustes da diferença de estoque;
* exigência de pagamento para entrega.

## Regras de Pagamento

O sistema deve oferecer suporte às seguintes regras de negócio:

### Limite de Confirmação

Uma venda é confirmada quando pelo menos 50% de seu valor total tiver sido pago.

Exemplo:

```text
Total = R$ 200
Pago  = R$ 100
       ↓
A venda pode ser confirmada
```

### Exigência para Entrega

O saldo restante deve ser integralmente pago antes da entrega.

```text
Confirmada
    ↓
Saldo restante
    ↓
Pagamento concluído
    ↓
Entrega permitida
```

O status do pagamento e o status da venda são conceitos separados.

Uma venda pode ser confirmada mesmo que ainda tenha saldo pendente.

## Comportamento do Estoque

Quando uma venda é confirmada, o sistema deduz o estoque necessário.

Exemplo:

```text
Antes da confirmação

Chocolate: 20
Suco:       8

Venda:
Chocolate × 2
Suco × 1

Após a confirmação

Chocolate: 18
Suco:      7
```

## Alterações após confirmação

Uma venda confirmada pode ser modificada.

O estoque deve ser ajustado de acordo com a diferença entre a composição anterior e a nova.

Exemplo:

```text
Original:
2 × Chocolate
1 × Suco

Novo:
2 × Biscoito
1 × Suco

Ajuste de estoque:
+2 Chocolate
-2 Biscoito
```

A movimentação original de estoque permanece no histórico.

O sistema não deve reescrever a movimentação original para dar a impressão de que a venda original nunca aconteceu.

## Cancelamento

Uma venda confirmada pode ser cancelada posteriormente.

O cancelamento deve preservar a venda e suas informações históricas.

O sistema não deve presumir que todos os itens retornam fisicamente ao estoque.

A situação física do estoque deve determinar se são necessárias correções.

## Explicitamente Fora de Escopo

M5 não implementa:

* integração com gateways de pagamento;
* conciliação bancária automática;
* verificação automática de PIX;
* processamento de cartão de crédito;
* reembolsos por meio de provedores externos;
* relatórios financeiros avançados.

## Dependência

M1, M2, M3 e M4.

## Status atual

```text
Status: Planejado
```

---

---

# 8. Fluxo Integrado da Fase 1

Ao final da Fase 1, o seguinte fluxo operacional deve ser possível:

```text
Produto
   ↓
Estoque
   ↓
Template de Cesta
   ↓
Cesta
   ↓
Cliente
   ↓
Venda
   ↓
Pagamento
   ↓
Confirmação da Venda
   ↓
Dedução de Estoque
```

O sistema deve oferecer suporte ao seguinte cenário real:

```text
1. Cadastrar produtos
2. Adicionar produtos ao estoque
3. Criar ou selecionar um template de cesta
4. Criar uma cesta
5. Personalizar a cesta, se necessário
6. Cadastrar/selecionar o cliente
7. Criar uma venda
8. Adicionar uma ou mais cestas
9. Definir as informações do destinatário e da entrega
10. Registrar o pagamento
11. Atingir o limite de pagamento de 50%
12. Confirmar a venda
13. Deduzir o estoque
14. Registrar o pagamento restante
15. Permitir a entrega somente após o pagamento integral
```

---

# 9. Definição de Pronto da Fase 1

A Fase 1 só é considerada concluída quando todas as condições a seguir forem verdadeiras:

## Produtos e Estoque

* Produtos podem ser criados e gerenciados.
* A ativação/desativação de produtos funciona.
* É possível adicionar estoque manualmente.
* Ajustes de estoque são suportados.
* É possível visualizar os saldos atuais.
* As movimentações de estoque são preservadas no histórico.

## Cestas

* Templates de cesta podem ser criados e gerenciados.
* Cestas podem ser criadas a partir de templates.
* Cestas podem ser criadas sem templates.
* As composições das cestas podem ser personalizadas.
* Várias unidades do mesmo produto são suportadas.
* Cestas existentes são independentes de alterações futuras em templates.

## Clientes

* Clientes podem ser criados e gerenciados.
* Clientes podem ser pesquisados.
* Clientes podem ser ativados/desativados.

## Vendas

* Vendas podem ser criadas.
* Uma venda pode conter uma ou mais cestas.
* A associação de clientes funciona.
* As informações de entrega das cestas funcionam.
* Vendas em rascunho podem ser salvas e editadas.
* Os totais das vendas são calculados.

## Pagamentos

* Pagamentos via PIX e cartão podem ser registrados.
* Os valores dos pagamentos são acompanhados.
* Um comprovante de pagamento pode ser associado.
* O total pago e o saldo restante ficam visíveis.
* A confirmação da venda segue a regra de pagamento de 50%.
* O estoque é deduzido quando a venda é confirmada.
* Alterações em vendas confirmadas ajustam o estoque pela diferença.
* O pagamento integral é exigido antes da entrega.
* Vendas canceladas preservam seu histórico.

## Qualidade

* Testes automatizados cobrem o comportamento de negócio implementado.
* Os testes automatizados existentes continuam passando.
* A validação manual foi realizada para cada marco.
* Não há problemas críticos conhecidos de integridade de dados.
* Nenhum marco introduziu regras de negócio não documentadas.
* Nenhuma funcionalidade futura desnecessária foi implementada.

---

# 10. Regra de Conclusão do Marco

Um marco não é considerado concluído apenas porque seu código foi implementado.

A sequência de conclusão é:

```text
Especificação
    ↓
Implementação
    ↓
Testes Automatizados
    ↓
Verificação pelo Agente
    ↓
Validação Humana
    ↓
Aprovação
    ↓
Próximo Marco
```

O próximo marco não deve começar até que o marco atual tenha sido validado explicitamente.

---

# 11. Controle de Escopo

Durante a Fase 1, novos requisitos devem ser classificados antes da implementação.

### A — Necessário para o Marco Atual

O requisito é necessário para que o marco atual funcione corretamente.

Ele pode ser adicionado à especificação atual.

### B — Necessário para um Marco Posterior

O requisito é válido, mas pertence a outro marco.

Ele deve ser documentado para esse marco sem ampliar a implementação atual.

### C — Ideia para o Backlog Futuro

A ideia pode ser útil, mas não é necessária neste momento.

Ela deve ser registrada como uma oportunidade futura.

### D — Complexidade Desnecessária

A proposta não resolve um problema de negócio estabelecido atualmente ou introduz arquitetura especulativa.

Ela não deve ser implementada.

O agente não deve ampliar silenciosamente o escopo de um marco.

---

# 12. Tratamento de Novas Regras de Negócio

Se a implementação revelar um comportamento que não foi definido pela documentação de negócio, o agente deve parar e identificar a ambiguidade.

O agente não deve inventar silenciosamente uma regra de negócio.

O processo é:

```text
Ambiguidade detectada
        ↓
Identificar a decisão de negócio exata
        ↓
Perguntar ao usuário
        ↓
Documentar a decisão
        ↓
Atualizar a especificação, se necessário
        ↓
Continuar a implementação
```

Detalhes técnicos de implementação podem ser escolhidos pelo agente quando não alterarem o comportamento de negócio e a solução razoável mais simples estiver clara.

O comportamento de negócio exige confirmação explícita.

---

# 13. Princípio de Arquitetura da Fase 1

A Fase 1 deve permanecer intencionalmente simples.

A implementação deve priorizar:

* conceitos de domínio claros;
* modelos de dados diretos;
* lógica simples de serviço/aplicação;
* regras de negócio explícitas;
* código legível;
* testes automatizados;
* projeto de banco de dados sustentável;
* abstração mínima;
* evolução incremental.

A implementação não deve introduzir arquitetura especulativa para requisitos futuros.

A existência de ideias futuras como lotes, vencimentos, produção, datas afetivas, comunicação ou precificação avançada não justifica implementá-las durante a Fase 1.

O sistema atual deve ser projetado de modo a permitir evolução futura sem implementá-la prematuramente.

---

# 14. Documentação da Fase 1

Cada marco deve ter sua própria pasta de documentação:

```text
docs/milestones/
│
├── phase-1.md
│
├── m1-products-inventory/
│   ├── specification.md
│   ├── use-cases.md
│   ├── acceptance-criteria.md
│   └── validation.md
│
├── m2-baskets/
│   ├── specification.md
│   ├── use-cases.md
│   ├── acceptance-criteria.md
│   └── validation.md
│
├── m3-customers/
│   ├── specification.md
│   ├── use-cases.md
│   ├── acceptance-criteria.md
│   └── validation.md
│
├── m4-sales/
│   ├── specification.md
│   ├── use-cases.md
│   ├── acceptance-criteria.md
│   └── validation.md
│
└── m5-payments/
    ├── specification.md
    ├── use-cases.md
    ├── acceptance-criteria.md
    └── validation.md
```

A documentação específica do marco deve ser criada quando ele estiver prestes a começar.

Não crie especificações detalhadas para todos os marcos antecipadamente.

---

# 15. Status Atual da Fase

| Marco                           | Status                       | Observações                                                                 |
| ------------------------------- | ---------------------------- | -------------------------------------------------------------------------- |
| M1 — Produtos e Estoque          | Concluído                    | Implementação, refinamento visual, validação e aceitação humana concluídos |
| M2 — Cestas e Templates de Cesta | Planejado                    | Depende de M1; aguarda o M2 Implementation Gate                             |
| M3 — Clientes                    | Planejado                    | Depende de M2                                                              |
| M4 — Vendas                      | Planejado                    | Depende de M1, M2 e M3                                                     |
| M5 — Pagamentos                  | Planejado                    | Depende de M1–M4                                                           |

### Dependências dos Marcos

```text
M1 — Produtos e Estoque (Products & Inventory)
├── pré-requisito para M2 (cestas referenciam produtos e estoque)
└── pré-requisito para M4 (vendas referenciam estoque para dedução)

M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)
└── pré-requisito para M4 (vendas contêm cestas)

M3 — Clientes (Customers)
└── pré-requisito para M4 (vendas pertencem a clientes)

M4 — Vendas (Sales)
└── pré-requisito para M5 (pagamentos confirmam vendas e acionam dedução de estoque)
```

O M1 — Produtos e Estoque — foi concluído após a aceitação humana pelo Product Owner.

O estado final de M1 é:

```text
Implementação:       Concluída
Refinamento visual:  Concluído
Validação:           Concluída
Aceitação humana:    Concluída
Status geral:        Concluído (COMPLETED)
```

O próximo passo é o M2 Implementation Gate. A implementação de M2 não começou e depende da conclusão desse gate.

Decisões fundamentais de negócio para M1 foram resolvidas:

* **Política de estoque negativo: RESOLVIDA**
  * **Política:** o estoque físico nunca deve ficar negativo (`INV-006`).
  * Operações que produziriam saldo negativo são rejeitadas.
  * O invariante é absoluto e também se aplica a operações concorrentes de estoque (`ADR-001`).

Nenhum marco posterior deve começar antes que o escopo seja explicitamente autorizado e o marco atual tenha passado pelo Gate de Conclusão do Marco.

---

# 16. Relação com a Outra Documentação

A Fase 1 segue a hierarquia de documentação do projeto:

```text
Visão do Produto
      ↓
Roadmap do Produto
      ↓
Contrato de Negócio
      ↓
Fase 1
      ↓
Especificação do Marco
      ↓
Casos de Uso
      ↓
Critérios de Aceitação
      ↓
Implementação
      ↓
Validação
```

Os documentos têm finalidades diferentes e não devem duplicar informações desnecessariamente.

`phase-1.md` define a estrutura e os limites da fase.

Ele não substitui:

* o Contrato de Negócio;
* as especificações dos marcos;
* os critérios de aceitação;
* as decisões de arquitetura;
* a documentação da implementação.

---

# 17. Princípio Orientador

A Fase 1 deve produzir um sistema operacional útil sem tentar resolver todo o futuro da Casa Afeto.

O objetivo não é prever todos os requisitos futuros.

O objetivo é estabelecer uma base sólida e simples que possa evoluir com base em necessidades reais do negócio.

> **Construa o que foi decidido. Valide. Aprenda com o uso. Então construa a próxima coisa.**
