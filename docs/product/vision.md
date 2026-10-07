# Casa Afeto — Visão do Produto

**Versão do documento:** 0.1
**Status:** Rascunho
**Última atualização:** 2026-10-02

---

## 1. Visão Geral do Produto

Casa Afeto é um negócio focado na criação e venda de cestas de café da manhã e cestas de presente afetivas.

A operação se dá por meio de pedidos personalizados, em que um cliente escolhe uma cesta, solicita alterações quando necessário, concorda com uma data de entrega e destinatário, efetua o pagamento e a equipe da Casa Afeto prepara e entrega o pedido.

O propósito deste sistema é oferecer à Casa Afeto uma forma simples, confiável e centralizada de gerenciar sua operação de vendas.

O sistema deve conectar as principais atividades de negócio envolvidas em um pedido:

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
    ↓
Estoque
```

O sistema pretende reduzir o trabalho manual, melhorar a visibilidade do negócio, preservar informações históricas e fornecer uma base para futuros aprimoramentos operacionais.

---

## 2. Visão do Produto

Construir um sistema prático de gestão de vendas que permita à Casa Afeto gerenciar seus produtos, estoque, cestas, clientes, vendas e pagamentos em um único lugar, mantendo o sistema simples o suficiente para refletir a forma real como o negócio opera.

O sistema deve apoiar o negócio sem forçar o negócio a adaptar seus processos a complexidade desnecessária de software.

O princípio orientador é:

> **O software deve tornar a operação da Casa Afeto mais fácil de gerenciar, não tornar a operação mais complicada.**

---

## 3. Problema

A operação da Casa Afeto envolve diversas informações naturalmente conectadas, mas que podem se tornar difíceis de gerenciar quando tratadas manualmente.

Uma única venda pode envolver:

* um cliente;
* uma ou mais cestas;
* composições diferentes de cesta;
* produtos com quantidades diferentes;
* um destinatário diferente do cliente;
* um endereço de entrega;
* uma data de entrega;
* pagamentos realizados em momentos diferentes;
* consumo de estoque;
* alterações no pedido após sua criação.

Sem um sistema centralizado, manter a consistência entre essas informações torna-se cada vez mais difícil.

O sistema, portanto, precisa fornecer uma fonte confiável de informação operacional, preservando a flexibilidade exigida pelo negócio.

---

## 4. Usuários-Alvo

Os usuários principais são as pessoas responsáveis por operar a Casa Afeto.

O sistema inicial foi pensado principalmente para uso interno do negócio, em vez de permitir que os clientes façam pedidos diretamente.

O sistema deve priorizar:

* simplicidade;
* rapidez de operação;
* clareza;
* baixo custo administrativo;
* informações históricas confiáveis;
* correção fácil de erros operacionais.

---

## 5. Fluxo Central do Negócio

O sistema deve suportar o fluxo real de um pedido típico da Casa Afeto.

```text
Cliente entra em contato com a Casa Afeto
        ↓
Cliente escolhe uma cesta
        ↓
Composição da cesta pode ser personalizada
        ↓
Informações de entrega são definidas
        ↓
Pagamento é recebido
        ↓
Venda é confirmada
        ↓
Estoque é consumido
        ↓
Cesta é preparada
        ↓
Cesta é entregue
```

O sistema não precisa reproduzir todas as comunicações ou atividades operacionais executadas pelo negócio.

Sua responsabilidade é manter as informações necessárias para gerenciar e controlar a operação do negócio.

---

## 6. Princípios do Produto

### 6.1 Negócio em primeiro lugar

As regras de negócio devem orientar o design do software.

O sistema deve representar como a Casa Afeto realmente opera em vez de introduzir processos genéricos apenas porque são comuns em outros sistemas.

---

### 6.2 Simplicidade sobre abstração

O sistema deve usar o design mais simples que resolva corretamente o problema de negócio atual.

Deve evitar abstrações desnecessárias:

* abstrações;
* frameworks;
* camadas arquiteturais;
* infraestrutura genérica;
* integrações;
* automações;
* conceitos de domínio;
* mecanismos de configuração.

A complexidade deve ser introduzida somente quando houver uma razão concreta de negócio ou técnica.

---

### 6.3 Informações históricas importam

Eventos importantes do negócio devem preservar seu histórico.

Por exemplo:

* alterar o custo de um produto não deve reescrever informações históricas de aquisição;
* alterar um template de cesta não deve alterar cestas já criadas;
* corrigir o estoque deve preservar a movimentação original e criar uma nova correção;
* cancelar uma venda não deve apagar a venda do sistema.

O sistema deve favorecer a rastreabilidade em vez de atualizações destrutivas quando a informação histórica for relevante.

---

### 6.4 Flexibilidade onde o negócio precisa

Casa Afeto vende cestas personalizadas.

Portanto, o sistema deve permitir que uma cesta baseada em um template padrão seja modificada para um cliente específico.

Uma cesta pode:

* usar um template;
* ser criada sem template;
* conter múltiplas quantidades do mesmo produto;
* ter produtos adicionados ou removidos;
* ter produtos substituídos.

A composição concreta usada por uma venda futura deve representar o que foi vendido ao cliente. No M2, uma cesta persistida ainda não é uma venda; a relação e a cópia da composição no contexto da venda serão definidas no M4.

---

### 6.5 Controle humano sobre decisões finais

O negócio deve manter o controle sobre decisões comerciais importantes. Custos e precificação dependem de regras e fontes de dados que serão definidos em marcos futuros; a visão de longo prazo não os torna requisitos do M2.

---

### 6.6 Evolução progressiva

O produto deve evoluir de forma incremental.

Cada marco deve resolver um problema claramente definido antes que a próxima área seja implementada.

O projeto deve seguir:

```text
Definir
  ↓
Especificar
  ↓
Construir
  ↓
Testar
  ↓
Validar
  ↓
Aprender
  ↓
Construir a próxima coisa
```

Ideias futuras não devem se tornar automaticamente requisitos atuais.

---

## 7. Áreas Centrais do Produto

O produto inicial é organizado em cinco áreas operacionais centrais.

### Produtos

Produtos representam itens que a Casa Afeto usa em suas cestas.

Exemplos incluem:

* chocolates;
* barras de cereal;
* sucos;
* bolos;
* cafés;
* canecas;
* cartões;
* materiais de embalagem.

Produtos têm uma unidade base de estoque e podem ser ativados ou desativados.

---

### Estoque

Estoque representa a disponibilidade física de produtos usados pela Casa Afeto.

O sistema deve fornecer visibilidade sobre:

* quantidades atuais;
* adições;
* deduções;
* correções;
* histórico de estoque.

O estoque deve, em última instância, ser baseado em movimentações e não apenas em um valor atual editado manualmente.

O sistema deve evoluir para conceitos de estoque mais detalhados, como lotes de aquisição, custos e datas de vencimento, conforme o negócio exigir.

---

### Cestas

Cestas são o principal produto comercial vendido pela Casa Afeto.

Uma cesta pode ser criada a partir de um template padrão ou criada independentemente.

Um template fornece uma composição padrão, mas a cesta concreta vendida a um cliente pode diferir desse template.

O sistema deve preservar a composição real de cada cesta.

---

### Clientes

Clientes representam as pessoas que compram da Casa Afeto.

O registro do cliente deve fornecer as informações necessárias para identificar e gerenciar clientes e suas vendas.

Funcionalidades mais avançadas de relacionamento com clientes ficam intencionalmente fora do escopo inicial do produto.

---

### Vendas

Uma venda representa uma transação comercial com um cliente.

Uma venda pode conter uma ou mais cestas.

Cada cesta pode ter seu próprio:

* destinatário;
* endereço de entrega;
* data de entrega;
* composição.

Uma venda avança por estados operacionais conforme se move da criação até a entrega.

---

### Pagamentos

Pagamentos representam valores recebidos para uma venda.

O sistema inicial deve suportar o processo atual de pagamento do negócio, incluindo:

* PIX;
* pagamentos com cartão;
* comprovante de pagamento;
* pagamentos parciais;
* saldo de pagamento.

O status do pagamento está relacionado ao status operacional da venda, mas é distinto dele.

---

## 8. Evolução de Custos e Precificação

Custos e precificação são capacidades futuras. M1 não fornece uma fonte formal de custo e o M2 não calcula custo de produto ou cesta, preço sugerido ou final, margem ou markup. A antiga ideia de aproximadamente duas vezes o custo é apenas uma ideia futura, não uma regra de negócio vigente. As regras e fontes de dados aplicáveis serão definidas em marco futuro.

---

## 9. Relação entre Estoque e Vendas

O estoque está diretamente conectado ao ciclo de vida das vendas.

O comportamento pretendido é:

```text
Venda criada
    ↓
Venda permanece em rascunho
    ↓
Pagamento alcança o limite de confirmação
    ↓
Venda se torna confirmada
    ↓
Estoque é deduzido
```

O sistema deve preservar a relação entre uma venda e as alterações de estoque que ela provoca.

Se uma venda confirmada for modificada mais tarde, o sistema deve ajustar o estoque conforme a diferença entre as composições anterior e nova, em vez de reescrever o histórico original de estoque.

Isso permite que o negócio entenda o que aconteceu ao longo do tempo.

---

## 10. Custo do Produto e Histórico de Aquisição

O custo de um produto não é necessariamente fixo.

O mesmo produto pode ser comprado a preços diferentes.

Por exemplo:

```text
Cereal Bar

Compra A → R$2,50 / unidade
Compra B → R$1,80 / unidade
```

O sistema deve, portanto, evitar tratar o custo do produto como uma propriedade permanente do próprio produto.

A evolução futura do estoque pode associar o estoque ao seu contexto de aquisição, incluindo:

* custo de aquisição;
* quantidade;
* data de vencimento;
* quantidade restante.

A implementação exata e as regras de negócio para essa funcionalidade serão definidas quando essa funcionalidade entrar em um marco aprovado.

---

## 11. Personalização

Personalização é uma característica importante do negócio da Casa Afeto.

O sistema deve suportar a realidade de que um cliente pode solicitar alterações a uma cesta padrão.

Por exemplo:

```text
Template
    ↓
Cesta padrão
    ↓
Cliente solicita alterações
    ↓
Cesta concreta
    ↓
Venda real
```

A composição concreta usada por uma venda deve representar o que foi realmente vendido, independentemente de mudanças posteriores no template original. A cesta mantida no M2 é uma entidade separada e não possui vínculo estrutural com uma venda; o M4 definirá como ela será usada em uma venda.

---

## 12. Evolução Futura do Produto

O produto inicial foca na operação central de vendas.

Versões futuras podem evoluir para suportar capacidades adicionais, como:

### Relacionamento com clientes e datas afetivas

Casa Afeto pode eventualmente manter datas importantes associadas a clientes e destinatários, como:

* aniversários;
* bodas;
* outras ocasiões relevantes.

Isso pode permitir que o negócio identifique datas próximas e entre em contato proativamente com clientes.

Essa funcionalidade é intencionalmente fora do escopo inicial do MVP.

---

### Vencimento e otimização de estoque

Futuras funcionalidades de estoque podem incluir:

* lotes de produto;
* datas de vencimento;
* alertas de vencimento;
* uso preferencial de produtos próximos do vencimento;
* seleção de estoque mais sofisticada.

O negócio atualmente considera uma estratégia de primeiro vencimento como conceitualmente desejável, mas isso é uma política de negócio futura e não deve ser tratada como uma regra arquitetural imutável.

---

### Produção interna

Alguns produtos da Casa Afeto podem eventualmente ser produzidos internamente, como bolos.

Futuras funcionalidades poderiam, portanto, suportar:

* receitas;
* ingredientes;
* quantidades de produção;
* custos de produção;
* vencimento.

Essa funcionalidade não faz parte do produto inicial.

---

### Reposição

O sistema pode eventualmente identificar situações em que produtos requisitados por cestas já vendidas precisam ser repostos.

Isso pode fornecer visibilidade sobre necessidades futuras de estoque.

Essa funcionalidade não faz parte do produto inicial.

---

### Comunicação de negócios

Versões futuras podem integrar canais de comunicação, como WhatsApp, para reduzir o trabalho manual em torno da comunicação com clientes.

Essas integrações só devem ser introduzidas quando houver um requisito de negócio claramente definido.

---

## 13. Escopo do MVP

A primeira fase do produto foca nas seguintes capacidades:

```text
Produtos
    ↓
Estoque
    ↓
Templates de Cesta
    ↓
Cestas
    ↓
Clientes
    ↓
Vendas
    ↓
Pagamentos
    ↓
Dedução de estoque
```

A primeira fase é dividida em:

```text
M1 — Produtos e Estoque (Products & Inventory)
M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)
M3 — Clientes (Customers)
M4 — Vendas (Sales)
M5 — Pagamentos (Payments)
```

O objetivo não é implementar todos os possíveis processos da Casa Afeto.

O objetivo é estabelecer uma base operacional confiável que possa ser validada e evoluída.

---

## 14. Explicitamente Fora do Escopo Inicial

O seguinte não faz parte do produto inicial, a menos que um requisito futuro o coloque explicitamente em escopo:

* pedido por autoatendimento do cliente;
* integração com gateway de pagamento online;
* integração com WhatsApp;
* campanhas de marketing automatizadas;
* lembretes de datas afetivas;
* CRM avançado;
* gestão de fornecedores;
* compras automatizadas;
* alertas de vencimento;
* reposição automatizada;
* gestão de produção;
* gestão de receitas;
* gestão de ingredientes;
* gestão de logística/envio;
* promoções;
* gestão de descontos;
* integração de faturamento;
* gestão multiempresa;
* relatórios avançados e business intelligence.

Sua exclusão não significa que nunca possam existir.

Significa que eles não devem influenciar a arquitetura ou a implementação do produto atual, a menos que um requisito concreto os torne relevantes.

---

## 15. Critérios de Sucesso

O produto inicial deve ser considerado bem-sucedido quando a Casa Afeto puder gerenciar o fluxo operacional central sem depender de registros manuais desconectados para as informações cobertas pelo sistema.

No mínimo, o sistema deve permitir que o negócio:

1. Mantenha seus produtos.
2. Saiba as quantidades atuais de estoque.
3. Entenda as movimentações de estoque.
4. Defina templates de cesta padrão.
5. Crie cestas personalizadas.
6. Mantenha informações de clientes.
7. Crie vendas contendo uma ou mais cestas.
8. Registre informações de pagamento.
9. Determine quando uma venda atinge o limite de confirmação.
10. Deduza o estoque quando a venda é confirmada.
11. Preservar informações históricas quando correções ou mudanças ocorrerem.
12. Entenda o estado atual de um pedido sem reconstruí-lo manualmente a partir de diferentes fontes.

---

## 16. Atributos de Qualidade do Produto

O sistema deve priorizar as seguintes qualidades.

### Correção

As regras de negócio devem ser respeitadas de forma consistente.

### Rastreabilidade

Mudanças importantes em estoque, vendas, pagamentos e outras informações de negócio devem permanecer compreensíveis posteriormente.

### Simplicidade

O sistema deve permanecer fácil de entender e operar.

### Manutenibilidade

A base de código deve ser estruturada para que mudanças futuras possam ser feitas sem acoplamento desnecessário.

### Evolutividade

O sistema deve ser capaz de crescer conforme requisitos reais de negócio surgirem, sem implementar funcionalidade especulativa com antecedência.

### Usabilidade

Tarefas operacionais comuns devem exigir o menor número possível de etapas desnecessárias.

---

## 17. Princípio Orientador para Desenvolvimento

Cada funcionalidade deve responder a uma necessidade concreta de negócio.

Antes de implementar uma nova capacidade, o projeto deve ser capaz de responder:

> **Qual problema na operação da Casa Afeto isso resolve?**

Se a resposta for ambígua, a funcionalidade não deve ser adicionada automaticamente ao escopo atual.

O projeto deve preferir:

```text
Requisito real
    ↓
Regra de negócio clara
    ↓
Implementação pequena
    ↓
Testes automatizados
    ↓
Validação humana
    ↓
Feedback do mundo real
```

em vez de:

```text
Necessidade futura possível
    ↓
Abstração genérica
    ↓
Arquitetura complexa
    ↓
Funcionalidade não utilizada
```

---

## 18. Relação com a Outra Documentação

Este documento define a visão do produto e a direção de alto nível.

Ele não define requisitos detalhados de implementação.

A hierarquia da documentação é:

```text
Visão do Produto
      ↓
Contrato de Negócio
      ↓
Modelo de Domínio / Regras de Negócio
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

Cada documento deve ter uma responsabilidade clara e evitar duplicar informações já definidas em outro lugar.

A Visão do Produto deve permanecer relativamente estável conforme o sistema evolui.

---

## 19. Política de Mudança

A visão do produto pode evoluir conforme a Casa Afeto aprende com o uso do sistema.

Mudanças devem ser feitas de forma deliberada.

Uma nova ideia deve primeiro ser classificada como uma de:

* requisito atual;
* marco futuro;
* item de backlog futuro;
* complexidade rejeitada ou desnecessária.

Uma ideia futura não deve se tornar automaticamente um requisito de implementação.

Quando uma mudança significativa afeta a direção do produto, este documento deve ser atualizado para que continue sendo uma representação precisa do propósito e dos limites do produto.

---

## 20. Direção Atual do Produto

O objetivo imediato é construir a menor versão útil do sistema de gestão da Casa Afeto e validá-la por meio do uso real do negócio.

O projeto começará com:

**M1 — Produtos e Estoque (Products & Inventory)**

e evoluirá progressivamente por:

```text
M1 Produtos e Estoque (Products & Inventory)
        ↓
M2 Cestas e Templates de Cesta (Baskets & Basket Templates)
        ↓
M3 Clientes (Customers)
        ↓
M4 Vendas (Sales)
        ↓
M5 Pagamentos (Payments)
```

Cada marco deve ser especificado, implementado, testado e validado antes que o projeto avance.

O sistema deve crescer a partir de **necessidades reais da Casa Afeto**, e não a partir de suposições sobre o que uma plataforma completa de gestão de negócios poderia eventualmente exigir.
