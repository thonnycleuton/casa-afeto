# Casa Afeto — Roadmap do Produto

**Versão do documento:** 0.3
**Status:** Ativo
**Última atualização:** 2026-10-05

---

## 1. Finalidade

Este documento define a evolução planejada do sistema de gestão da Casa Afeto e reflete o estado atual dessa evolução.

Sua finalidade é estabelecer:

* a sequência inicial de entrega;
* as capacidades planejadas para cada fase;
* o estado atual de cada marco;
* dependências entre marcos;
* gates de governança que controlam quando um marco pode começar e quando está completo;
* áreas futuras de evolução;
* limites entre escopo atual e escopo futuro.

O roadmap responde a duas perguntas:

> "Para onde o projeto está indo?"

> "Onde o projeto está agora?"

Este roadmap é deliberadamente de alto nível.

Comportamentos detalhados pertencem às especificações de marcos e regras de negócio.

O roadmap não é um compromisso de implementar todas as capacidades futuras listadas aqui.

Capacidades futuras devem ser validadas contra necessidades reais do negócio antes de entrarem em desenvolvimento ativo.

---

# 2. Estratégia de Evolução do Produto

O sistema será desenvolvido de forma incremental.

O projeto segue o princípio:

> **Construa pouco, valide, aprenda e depois construa a próxima coisa.**

O produto inicial focará no núcleo operacional:

```text
Produtos
    ↓
Estoque
    ↓
Cestas
    ↓
Clientes
    ↓
Vendas
    ↓
Pagamentos
```

Somente após esse fluxo central ficar operacional é que capacidades adicionais devem ser consideradas.

O roadmap, portanto, distingue entre:

1. **Fase 1 — Operações Centrais (Core Operations)**
2. **Fase 2 — Evolução do Estoque e dos Clientes (Inventory & Customer Evolution)**
3. **Fase 3 — Automação Operacional (Operational Automation)**
4. **Oportunidades Futuras**

As fronteiras das fases são intencionalmente flexíveis.

Prioridades reais podem mudar com base no feedback do negócio.

---

# 3. Fundamentos Transversais

Determinadas capacidades não são marcos de negócio — são fundações técnicas e de design que apoiam todos os marcos.

```text
Fundamentos Transversais
├── Fundação Técnica       (infraestrutura, stack, padrões de arquitetura)
└── Sistema de Design      (linguagem visual, biblioteca de componentes, princípios de UX)

Marcos de Negócio
├── M1 — Produtos e Estoque (Products & Inventory)
├── M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)
├── M3 — Clientes (Customers)
├── M4 — Vendas (Sales)
└── M5 — Pagamentos (Payments)
```

O **Sistema de Design** não é um marco. É uma fundação usada pelos marcos conforme necessário.

Sua evolução é guiada pelos requisitos visuais de cada marco, e não por uma trilha de entrega separada.

A **Fundação Técnica** estabelece infraestrutura, stack e restrições arquiteturais. Ela está documentada em:

```text
docs/architecture/technical-foundation.md
```

---

# 4. Fase 1 — Operações Centrais (Core Operations)

## Objetivo

Criar a primeira versão confiável do sistema operacional da Casa Afeto.

O sistema deve permitir que a Casa Afeto gerencie a relação básica entre:

* produtos;
* estoque;
* cestas;
* clientes;
* vendas;
* pagamentos.

Ao final da Fase 1, o sistema deve suportar o fluxo principal de negócio:

```text
Produto
    ↓
Estoque
    ↓
Cesta
    ↓
Cliente
    ↓
Venda
    ↓
Pagamento
    ↓
Dedução de estoque
```

---

# 5. Marcos da Fase 1

A Fase 1 é dividida em cinco marcos.

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

Cada marco deve ser:

* especificado;
* implementado;
* testado;
* validado manualmente;
* revisado contra os requisitos de negócio

antes que o projeto avance para o próximo marco.

---

# 6. M1 — Produtos e Estoque (Products & Inventory)

## Objetivo

Estabelecer a base para gerenciar os produtos usados pela Casa Afeto e seu estoque atual.

## Capacidades planejadas

### Produtos

* criar produtos;
* editar informações do produto;
* ativar produtos;
* desativar produtos;
* buscar/listar produtos;
* definir a unidade base de estoque do produto.

### Estoque

* adicionar estoque;
* remover estoque por ajustes suportados;
* visualizar saldo atual;
* visualizar histórico de movimentações de estoque;
* realizar correções de estoque preservando o histórico de movimentações.

## Conceitos-chave de negócio

M1 estabelece o estoque como um conceito baseado em movimentações.

O sistema não deve depender apenas de alterar manualmente um único número de estoque sem preservar como esse número foi produzido.

## Decisões-chave de negócio resolvidas

* **Política de estoque negativo: RESOLVIDA**
  * **Política:** O estoque físico deve nunca ficar negativo (`INV-006`).
  * Operações que produziriam um saldo negativo são rejeitadas.
  * Este invariante é absoluto e também se aplica a operações concorrentes de estoque (`ADR-001`).

## Explicitamente fora de M1

O seguinte não faz parte deste marco:

* compras;
* fornecedores;
* notas fiscais de compra;
* itens de compra;
* lotes de estoque;
* datas de vencimento;
* seleção FEFO;
* alertas de vencimento;
* reposição automatizada;
* produção;
* receitas;
* estoque reservado;
* dedução de estoque relacionada a vendas.

Esses conceitos podem ser introduzidos em marcos posteriores.

## Status atual

```text
Implementação:       Concluída
Refinamento visual:  Concluído
Validação:           Concluída
Aceitação humana:    Pendente
Status geral:        Em andamento
```

M1 passou pela validação técnica formal e aguarda a aceitação humana do proprietário do produto.

---

# 7. M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)

## Objetivo

Permitir que a Casa Afeto defina cestas padrão e crie cestas personalizadas para vendas individuais.

## Capacidades planejadas

### Templates de cesta

* criar templates;
* editar templates;
* ativar/desativar templates;
* definir composição do template;
* definir quantidades de produtos.

### Cestas

* criar uma cesta a partir de um template;
* criar uma cesta sem template;
* personalizar a cesta;
* adicionar produtos;
* remover produtos;
* substituir produtos;
* definir múltiplas quantidades do mesmo produto;
* preservar a composição da cesta concreta;
* calcular custo da cesta;
* calcular preço sugerido;
* definir preço final manualmente.

## Fluxo de trabalho esperado

O usuário deve ser capaz de:

1. Criar um template de cesta.
2. Adicionar produtos e quantidades ao template.
3. Criar uma cesta concreta a partir do template.
4. Criar uma cesta sem template.
5. Modificar a cesta concreta.
6. Adicionar ou remover produtos.
7. Substituir produtos.
8. Usar múltiplas unidades do mesmo produto.
9. Ver o custo da cesta.
10. Ver um preço sugerido de venda.
11. Definir o preço final manualmente.

## Comportamento importante de negócio

Uma cesta concreta deve ser independente de futuras alterações no seu template.

Por exemplo:

```text
Template A
    Chocolate × 2
    Suco × 1

        ↓ criar cesta

Cesta X
    Chocolate × 2
    Suco × 1

        ↓ alteração posterior do template

Template A
    Chocolate × 1
    Suco × 2
```

A cesta X deve continuar contendo:

```text
Chocolate × 2
Suco × 1
```

A alteração do template não deve modificar a cesta existente.

Uma cesta também pode ser personalizada após sua criação.

Um produto com estoque insuficiente ainda pode ser adicionado à cesta, mas o usuário deve receber um aviso claro sobre a falta de estoque.

## Comportamento de precificação

O sistema deve calcular:

```text
Custo da Cesta
    ↓
Preço Sugerido
    ↓
Preço Final
```

A prática atual de negócio de aproximadamente 2× custo é tratada como sugestão de precificação, não como regra imposta.

O preço final de venda permanece sob controle do usuário.

## Explicitamente fora de escopo

M2 não implementa:

* vendas;
* clientes;
* pagamentos;
* dedução de estoque;
* gestão de compras;
* seleção de lote;
* gestão de vencimento;
* gerenciamento de destinatário como entidade separada;
* descontos ou promoções.

## Dependência

M2 depende de M1, pois cestas e templates dependem de produtos e estoque.

## Status atual

```text
Status: Planejado
```

M2 não entrará em implementação até que M1 passe pelo Gate de Conclusão do Marco.

---

# 8. M3 — Clientes (Customers)

## Objetivo

Estabelecer o registro básico de cliente necessário para associar vendas a clientes.

## Capacidades planejadas

* criar clientes;
* editar informações do cliente;
* buscar clientes;
* ativar/desativar clientes;
* associar vendas a clientes.

## Filosofia de escopo

M3 deve permanecer intencionalmente simples.

Não se destina a se tornar um CRM completo.

## Explicitamente fora de M3

* segmentação de clientes;
* campanhas de marketing;
* lembretes automatizados;
* programas de fidelidade;
* pontuação de clientes;
* análises avançadas de clientes;
* datas afetivas;
* comunicação automatizada por WhatsApp.

Essas podem ser avaliadas mais tarde.

## Status atual

```text
Status: Planejado
```

---

# 9. M4 — Vendas (Sales)

## Objetivo

Criar e gerenciar a transação comercial conectando clientes e cestas.

## Capacidades planejadas

Uma venda deve permitir ao usuário:

* selecionar um cliente;
* adicionar uma ou mais cestas;
* visualizar composições da cesta;
* modificar composição da cesta;
* definir informações do destinatário;
* definir endereço de entrega;
* definir data de entrega;
* adicionar observações relevantes;
* calcular totais da venda;
* salvar a venda como rascunho;
* modificar uma venda em rascunho.

## Ciclo de vida da venda

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

## Importante fronteira de escopo

M4 cria a estrutura de vendas, mas não introduz o fluxo completo de confirmação de pagamento.

O comportamento de pagamento pertence a M5.

## Status atual

```text
Status: Planejado
```

---

# 10. M5 — Pagamentos (Payments)

## Objetivo

Conectar informações de pagamento ao ciclo de vida de vendas e estabelecer as regras para confirmação da venda e dedução de estoque.

## Capacidades planejadas

* registrar pagamentos;
* suportar PIX;
* suportar pagamentos com cartão;
* registrar comprovante de pagamento;
* acompanhar o total pago;
* calcular saldo restante;
* determinar se o limite de confirmação foi alcançado.

## Regra de confirmação

A regra atual de negócio é:

> Uma venda é confirmada quando pelo menos 50% do seu valor total foi pago.

Uma vez confirmada, a venda gera a dedução correspondente de estoque.

```text
Pagamento >= 50%
       ↓
Venda confirmada
       ↓
Estoque deduzido
```

## Pagamento restante

O saldo restante deve ser pago antes da entrega.

A regra atual de negócio é:

> 100% da venda deve ser pago antes da entrega.

## Alterações após confirmação

Uma venda confirmada pode ser modificada.

Quando a composição da cesta muda, o estoque deve ser ajustado de acordo com a diferença entre as composições anterior e nova.

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

A movimentação original de estoque permanece parte do registro histórico.

## Status atual

```text
Status: Planejado
```

---

# 11. Visão Geral do Status dos Marcos

Retrato atual dos estados dos marcos da Fase 1.

```text
M1 — Produtos e Estoque
     Implementação       Concluída
     Refinamento visual  Concluído
     Validação           Concluída
     Aceitação humana    Pendente
     Status geral        Em andamento

M2 — Cestas e Templates de Cesta  Planejado
M3 — Clientes                     Planejado
M4 — Vendas                       Planejado
M5 — Pagamentos                   Planejado
```

Esta seção deve ser atualizada sempre que um marco mudar de estado.

---

# 12. Dependências dos Marcos

As dependências conhecidas são:

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

---

# 13. Definição de Pronto da Fase 1

A Fase 1 deve ser considerada concluída quando a Casa Afeto puder executar o seguinte fluxo pelo sistema:

```text
Cadastrar Produto
      ↓
Gerenciar Estoque
      ↓
Criar Template de Cesta
      ↓
Criar Cesta Personalizada
      ↓
Cadastrar Cliente
      ↓
Criar Venda
      ↓
Registrar Pagamento
      ↓
Atingir Limite de Confirmação
      ↓
Confirmar Venda
      ↓
Deduzir Estoque
      ↓
Concluir Fluxo de Entrega
```

Os critérios de aceitação exatos pertencem aos documentos de cada marco.

---

# 14. Fase 2 — Evolução do Estoque e dos Clientes

A Fase 2 representa capacidades que se tornam valiosas quando o fluxo operacional central estiver funcionando.

Essas capacidades só devem ser promovidas para desenvolvimento ativo depois que a experiência da Fase 1 fornecer evidências suficientes de que são necessárias.

## 14.1 Gestão de Compras

Capacidades potenciais:

* registrar compras;
* registrar itens de compra;
* registrar quantidades adquiridas;
* registrar preços de compra;
* converter unidades comerciais de compra em unidades de estoque;
* associar compras ao estoque.

Exemplo:

```text
1 caixa
×
24 unidades por caixa
=
24 unidades de estoque
```

O sistema deve preservar o preço real de aquisição, em vez de substituir custos históricos anteriores.

## 14.2 Lotes de Estoque

Capacidade potencial:

Representar como lotes separados os estoques adquiridos em momentos e preços diferentes.

Exemplo:

```text
Chocolate

Lote A
Custo: R$ 2,50
Quantidade: 20

Lote B
Custo: R$ 1,80
Quantidade: 15
Vencimento: mais próximo
```

Isso permite que o sistema diferencie contextos distintos de aquisição.

A estratégia exata de seleção de lote deve ser definida como uma regra de negócio quando essa funcionalidade entrar em desenvolvimento ativo.

## 14.3 Gestão de Vencimentos

Capacidades potenciais:

* datas de vencimento;
* alertas de vencimento;
* produtos próximos do vencimento;
* uso preferencial de produtos com vencimento mais próximo;
* visibilidade do estoque vencido.

Uma estratégia que prioriza o vencimento mais próximo é atualmente uma possível política de negócio.

Ela deve permanecer uma regra de negócio substituível, em vez de se tornar uma suposição arquitetural.

## 14.4 Reposição de Estoque

Capacidades potenciais:

* identificar produtos necessários para cestas futuras;
* identificar estoque insuficiente;
* destacar produtos que precisam ser repostos;
* distinguir necessidades normais de estoque das necessidades urgentes criadas por vendas confirmadas.

O sistema deve primeiro oferecer visibilidade antes de tentar automatizar as compras.

## 14.5 Datas Afetivas

Funcionalidades potenciais relacionadas a clientes podem incluir:

```text
Cliente
   ↓
Pessoa / Destinatário
   ↓
Ocasião
   ↓
Data
```

Exemplos:

* aniversário;
* aniversário de casamento;
* outras ocasiões relevantes.

Capacidades futuras potenciais:

* registrar datas importantes;
* listar datas próximas;
* notificar o negócio;
* apoiar o contato proativo com clientes.

Essa funcionalidade está explicitamente fora da Fase 1.

---

# 15. Fase 3 — Automação Operacional

Depois que a operação central e a evolução de estoque/clientes estiverem estáveis, o sistema poderá evoluir para reduzir o trabalho repetitivo.

Áreas potenciais incluem:

## Comunicação

Possíveis integrações com:

* WhatsApp;
* fluxos de comunicação com clientes;
* comunicação de status do pedido;
* lembretes de pagamento.

Essas integrações só devem ser implementadas quando seus processos de negócio estiverem claramente definidos.

## Notificações Automatizadas

Notificações potenciais podem incluir:

* entrega próxima;
* pagamento pendente;
* vencimento próximo;
* data afetiva próxima;
* necessidade de reposição.

Cada notificação deve ter um propósito de negócio explícito antes da implementação.

## Painéis Operacionais

Painéis potenciais podem apresentar:

* entregas próximas;
* vendas por período;
* pagamentos pendentes;
* situação do estoque;
* produtos que exigem atenção;
* datas afetivas próximas.

Relatórios devem ser introduzidos conforme as necessidades reais do negócio, em vez de criar antecipadamente um subsistema amplo de relatórios.

---

# 16. Oportunidades Futuras

As capacidades a seguir poderão se tornar relevantes conforme a Casa Afeto crescer.

Elas estão registradas aqui como possibilidades, não como compromissos.

## 16.1 Produção Interna

Alguns produtos podem ser produzidos internamente.

Capacidades potenciais:

* receitas;
* ingredientes;
* lotes de produção;
* quantidades produzidas;
* custos de produção;
* datas de vencimento.

Exemplo:

```text
Receita
   ↓
Ingredientes
   ↓
Produção
   ↓
Produto Acabado
   ↓
Estoque
```

Isso só deve ser introduzido quando o negócio definir um processo real de produção.

## 16.2 Precificação Avançada

Funcionalidades futuras de precificação podem incluir:

* regras de precificação;
* análise de margem;
* preços históricos;
* precificação sazonal;
* promoções;
* descontos.

O sistema atual não deve implementar esses conceitos de forma especulativa.

## 16.3 Gestão Avançada de Clientes

Possíveis capacidades futuras:

* histórico de clientes;
* padrões de compra;
* preferências de clientes;
* segmentação;
* análise de compras recorrentes;
* ofertas personalizadas.

Elas só devem ser introduzidas se oferecerem valor operacional ou comercial mensurável.

## 16.4 Análises de Negócio

Relatórios futuros potenciais podem incluir:

* receita;
* custo;
* margens;
* vendas por cesta;
* consumo de produtos;
* giro de estoque;
* comportamento de pagamento;
* recorrência de clientes.

As análises devem evoluir a partir de dados reais e de perguntas do negócio.

---

# 17. Classificação do Backlog

Ideias identificadas durante o desenvolvimento devem ser classificadas, em vez de implementadas automaticamente.

Cada nova ideia deve pertencer a uma das categorias a seguir:

### A — Requisito do Marco Atual

A funcionalidade é necessária para concluir o marco que está sendo implementado.

Ela pode entrar na especificação atual.

### B — Requisito de Marco Futuro

A funcionalidade é importante, mas não pertence ao marco atual.

Ela deve ser documentada e adiada.

### C — Ideia para o Backlog Futuro

A ideia pode ser útil, mas exige validação adicional.

Ela deve ser registrada sem afetar a arquitetura atual.

### D — Complexidade Desnecessária

A ideia não resolve atualmente um problema de negócio significativo ou introduz complexidade desproporcional.

Ela não deve ser implementada.

---

# 18. Política de Mudanças do Roadmap

O roadmap não é imutável.

O aprendizado do negócio pode justificar alterações na sequência.

No entanto, as mudanças devem ser deliberadas.

Uma proposta de mudança deve identificar:

1. O que mudou?
2. Que problema de negócio isso resolve?
3. Por que isso é necessário agora?
4. Qual marco isso afeta?
5. Qual escopo existente seria substituído ou atrasado?
6. Isso introduz novos conceitos de domínio?
7. Isso exige uma decisão de arquitetura?

O projeto deve evitar ampliar um marco apenas porque um agente identificou uma capacidade futura potencialmente útil.

---

# 19. Relação entre Roadmap e Especificações

O roadmap define **o que está planejado e aproximadamente quando**.

Ele não define o comportamento detalhado.

A relação é:

```text
Visão
   ↓
Roadmap
   ↓
Marco
   ↓
Especificação
   ↓
Casos de Uso
   ↓
Critérios de Aceitação
   ↓
Implementação
```

Por exemplo:

```text
Roadmap:
M1 — Produtos e Estoque

        ↓

Especificação de M1:
Criar e gerenciar produtos

        ↓

Caso de Uso:
Criar Produto

        ↓

Critérios de Aceitação:
Dadas informações válidas do produto
Quando o usuário salvar o produto
Então o produto é persistido e fica disponível para seleção
```

As regras detalhadas pertencem à documentação do marco.

---

# 20. Próximo Marco de Governança

O próximo passo de M1 é a aceitação humana:

> **M1 — Produtos e Estoque**

Nenhuma funcionalidade de marcos posteriores deve ser implementada apenas porque poderá ser útil no futuro.

M1 continua em andamento e aguarda a aceitação humana do proprietário do produto. O status é:

```text
Implementação:       Concluída
Refinamento visual:  Concluído
Validação:           Concluída
Aceitação humana:    Pendente
Status geral:        Em andamento
```

As decisões fundamentais de negócio da especificação M1 foram resolvidas:

* **Política de estoque negativo: RESOLVIDA**
  * **Política:** o estoque físico nunca deve ficar negativo (`INV-006`).
  * Operações que produziriam um saldo negativo são rejeitadas.
  * Este invariante é absoluto e também se aplica a operações concorrentes de estoque (`ADR-001`).

M2 e os marcos posteriores permanecem planejados. Nenhum marco posterior está autorizado a começar.

---

# 21. Resumo do Roadmap

```text
FASE 1 — OPERAÇÕES CENTRAIS
─────────────────────────────────────

M1  Produtos e Estoque
 ↓
M2  Cestas e Templates de Cesta
 ↓
M3  Clientes
 ↓
M4  Vendas
 ↓
M5  Pagamentos


FASE 2 — EVOLUÇÃO
─────────────────────────────────────

Compras
Lotes de Estoque
Vencimentos
Reposição
Datas Afetivas


FASE 3 — AUTOMAÇÃO
─────────────────────────────────────

Comunicação
Notificações
Painéis Operacionais


OPORTUNIDADES FUTURAS
─────────────────────────────────────

Produção Interna
Precificação Avançada
Gestão Avançada de Clientes
Análises de Negócio
```

O roadmap existe para fornecer direção sem se tornar uma restrição ao aprendizado.

O sistema deve evoluir conforme as necessidades reais da Casa Afeto, com cada capacidade entrando em desenvolvimento somente quando seu valor e comportamento de negócio forem suficientemente compreendidos.
