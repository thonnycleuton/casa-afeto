# Casa Afeto — Roadmap do Produto

**Versão do documento:** 0.7
**Status:** Ativo
**Última atualização:** 2026-10-30

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
3. **Fase 3 — Infraestrutura & Acesso (Infrastructure & Access)**
4. **Fase 4 — Automação Operacional (Operational Automation)**
5. **Oportunidades Futuras**

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
Autorização financeira da confirmação
    ↓
Venda confirmada
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
Aceitação humana:    Concluída
Status geral:        Concluído
```

M1 foi aprovado na validação técnica e aceito pelo Product Owner. O marco está **COMPLETED**.

---

# 7. M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)

## Objetivo

Permitir que a Casa Afeto mantenha templates reutilizáveis e cestas concretas persistidas como composições de produtos. A cesta concreta do M2 não é uma venda nem possui cliente, dados de entrega ou estado comercial.

## Capacidades do marco

### Templates de cesta

* criar templates;
* definir nome do template;
* listar, consultar e visualizar templates;
* editar templates;
* ativar/desativar templates;
* definir composição do template;
* definir quantidades de produtos.

### Cestas

* criar uma cesta a partir de um template;
* criar uma cesta sem template;
* definir nome da cesta;
* listar, consultar e visualizar cestas;
* personalizar a cesta;
* adicionar produtos;
* remover produtos;
* substituir produtos;
* definir múltiplas quantidades do mesmo produto;
* alterar quantidades;
* salvar e continuar editando uma cesta, inclusive quando vazia.

## Fluxo de trabalho esperado

O usuário deve ser capaz de:

1. Criar um template de cesta.
2. Consultar, visualizar e editar templates.
3. Ativar ou desativar templates.
4. Adicionar produtos ativos e quantidades a um template.
5. Criar uma cesta a partir de um template ativo cuja composição contenha somente produtos ativos.
6. Criar uma cesta sem template, inclusive vazia.
7. Consultar, visualizar e editar cestas.
8. Adicionar, remover ou substituir produtos e alterar quantidades.
9. Salvar uma cesta vazia.

## Comportamento importante de negócio

Ao criar uma cesta a partir de um template, a composição é copiada naquele momento. A cesta permanece independente de alterações posteriores no template, e alterações na cesta não alteram o template. O `template_id`, se armazenado, identifica somente a origem.

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

Uma cesta pode permanecer vazia. Produtos inativos que já estejam em composições permanecem nelas e não impedem a edição de outros itens; a interface deve identificá-los. Produtos inativos não podem ser incluídos novamente nem substituídos automaticamente. Templates inativos permanecem consultáveis e editáveis, mas não podem originar novas cestas. Um template com produto inativo também não pode originar nova cesta até correção explícita.

Produto sem estoque suficiente pode ser incluído, com aviso informativo. A consulta de disponibilidade não bloqueia a composição, reserva estoque, altera saldo nem cria movimentações.

As composições referenciam produtos por `product_id`. Renomear um produto não altera suas referências ou quantidades. Uma referência em cesta ou template não é uma movimentação de estoque e não impede uma alteração de unidade base permitida pelas regras de M1; quantidades são expressas na unidade base atual, sem conversão ou histórico de unidade no M2.

## Fora do escopo

M2 não implementa vendas, clientes, pagamentos, destinatários, entrega, compras, fornecedores, lotes, validade, FEFO, reposição, reserva ou dedução de estoque, comunicação, notificações ou dashboards. Como correções pontuais aprovadas em M2 antes de M4, são implementados: preço de venda persistido na cesta-modelo, registro de custo unitário de aquisição nas entradas de estoque, cálculo do custo médio ponderado do produto (sem tratar custos desconhecidos como zero), cálculo do custo estimado da cesta e sugestão de preço de venda (2 × custo estimado da cesta), garantindo que o operador pode aceitar a sugestão ou informar outro preço e que alterações nos custos não sobrescrevem preços de venda já definidos. Se não houver dados suficientes, a sugestão permanece indisponível.

Duplicação, exclusão e arquivamento de templates ou cestas não fazem parte das operações aprovadas para M2.

## Dependência

M2 depende de M1, pois cestas e templates dependem de produtos, custos de entrada e estoque.

## Status atual

```text
Conclusão original: COMPLETED (VALIDATED / Aprovação humana concluída em 2026-10-06)
Reabertura pontual: Custos de aquisição e sugestão de preço das cestas
Status da correção: Concluída e aprovada (COMPLETED / Aprovação humana concluída)
Status geral de M2: Concluído (COMPLETED)
```

M2 foi originalmente aprovado pelo Product Owner após a Validation/Review em 2026-10-06. A reabertura pontual para registro de custo de aquisição em entradas de estoque, cálculo de custos médios e estimados e sugestão de preço (2 × custo) com preservação da autonomia do operador e dos preços já definidos foi implementada, validada e formalmente aprovada pelo Product Owner.

---

# 8. M3 — Clientes (Customers)

## Objetivo

Gerenciar clientes e suas datas importantes, sem antecipar o fluxo de vendas do M4.

## Capacidades do marco

* criar clientes;
* listar, pesquisar e consultar clientes;
* editar informações do cliente;
* inativar e reativar clientes;
* gerenciar datas importantes recorrentes e não recorrentes vinculadas ao cliente.

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
* comunicação automatizada por WhatsApp.

Essas podem ser avaliadas mais tarde.

## Status atual

```text
Implementation: IMPLEMENTED
Validation/Review: VALIDATED
Aceitação humana: Concluída
Status geral: COMPLETED
```

---

# 9. M4 — Vendas (Sales)

## Objetivo

Definir e futuramente implementar o ciclo operacional da venda, conectando clientes e cestas sem antecipar pagamentos nem movimentações automáticas de estoque.

## Capacidades planejadas

Uma venda deve permitir ao usuário:

* selecionar um cliente;
* adicionar uma ou mais cestas;
* copiar composição e preço vigente ao adicionar cada cesta;
* visualizar composições da cesta;
* modificar composição da cesta conforme o estado da venda;
* definir informações do destinatário;
* definir endereço de entrega;
* definir data de entrega;
* definir horário de entrega;
* calcular totais da venda;
* salvar a venda como rascunho;
* modificar uma venda em rascunho;
* iniciar a preparação por ação explícita;
* marcar cestas individualmente como preparadas;
* reabrir venda `PRONTA` com justificativa;
* registrar entrega por cesta;
* cancelar a venda nas condições aprovadas.

## Ciclo de vida da venda

O ciclo operacional inicial esperado segue:

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

Também é esperada uma situação de cancelamento:

```text
RASCUNHO / CONFIRMADA / EM PREPARAÇÃO / PRONTA
                                   ↓
                              CANCELADA
```

O fluxo normal não permite pular etapas. A transição `CONFIRMADA → EM PREPARAÇÃO` exige ação explícita do usuário. A transição `RASCUNHO → CONFIRMADA` pertence ao contrato de estados, mas sua autorização financeira pertence ao M5.

## Importante fronteira de escopo

M4 cria a estrutura e o ciclo operacional da venda, mas não registra pagamentos nem implementa uma regra financeira paralela de confirmação.

O comportamento financeiro de confirmação pertence a M5. M4 também não presume deduções, devoluções ou ajustes automáticos de estoque por composição, preparação, entrega ou cancelamento.

## Status atual

```text
Status: Concluído (COMPLETED)
Implementação:       Concluída
Refinamento visual:  Concluído
Validação:           Concluída (6/6 testes automatizados + validação manual)
Aceitação humana:    Concluída (2026-10-10)
```

## Objetivo

Registrar pagamentos da venda e autorizar financeiramente a transição `RASCUNHO → CONFIRMADA` conforme as regras aprovadas.

## Capacidades planejadas

* registrar pagamentos;
* suportar PIX;
* suportar pagamentos com cartão;
* registrar comprovante de pagamento;
* acompanhar o total pago;
* calcular saldo restante;
* determinar se o limite de confirmação foi alcançado;
* autorizar financeiramente a transição `RASCUNHO → CONFIRMADA`.

## Regra de confirmação

A regra atual de negócio é:

> Uma venda só pode ser autorizada financeiramente para `CONFIRMADA` quando pelo menos 50% do seu valor total foi pago.

```text
Pagamento >= 50%
       ↓
Autorização financeira da confirmação
```

## Condição operacional adicional

Mesmo quando o limiar financeiro tiver sido atingido, a autorização financeira da transição também exige que todas as cestas tenham destinatário, endereço, data e horário de entrega preenchidos.

## Status atual

```text
Status: Concluído (COMPLETED) — Implementação, validação automatizada (101 testes + 54 verificações API), validação manual parcial e aceitação humana concluídos em 2026-10-15.
```

---

# 11. Visão Geral do Status dos Marcos

Retrato atual dos estados dos marcos da Fase 1.

```text
M1 — Produtos e Estoque
     Implementação       Concluída
     Refinamento visual  Concluído
     Validação           Concluída
     Aceitação humana    Concluída
     Status geral        Concluído (COMPLETED)

M2 — Cestas e Templates de Cesta  Concluído (COMPLETED) — Conclusão original mantida no histórico; correção de custos de aquisição e sugestão de preços concluída e aceita pelo Product Owner
M3 — Clientes e Datas Importantes  Concluído (COMPLETED)
M4 — Vendas                       Concluído (COMPLETED) — Implementação, refinamento visual, validação e aceitação humana concluídos
M5 — Pagamentos                   Concluído (COMPLETED) — Implementação, validação automatizada (101 testes + 54 verificações API), validação manual parcial e aceitação humana concluídos
```

Esta seção deve ser atualizada sempre que um marco mudar de estado.

---

# 12. Dependências dos Marcos

As dependências conhecidas são:

```text
M1 — Produtos e Estoque (Products & Inventory)
├── pré-requisito para M2 (cestas referenciam produtos e estoque)
└── pré-requisito para M4 (vendas reutilizam produtos e informação de disponibilidade sem mover estoque automaticamente)

M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)
└── pré-requisito para M4 (vendas contêm cestas e dependem de preço de venda persistido na cesta-modelo)

M3 — Clientes (Customers)
└── pré-requisito para M4 (vendas pertencem a clientes)

M4 — Vendas (Sales)
└── pré-requisito para M5 (pagamentos autorizam financeiramente a transição `RASCUNHO → CONFIRMADA`)
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
Validar dados obrigatórios de entrega
      ↓
Autorizar financeiramente a confirmação
      ↓
Confirmar Venda
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

**Status: Implementado no M7 (Fase 2).**

O sistema representa como lotes separados os estoques adquiridos em momentos e preços diferentes.

Exemplo:

```text
Chocolate

Lote A
Custo: R$ 2,50
Quantidade: 20

Lote B
Custo: R$ 1,80
Quantidade: 15
```

Isso permite que o sistema diferencie contextos distintos de aquisição.

A estratégia de seleção de lote é FEFO (First Expired, First Out), definida como regra LOT-003 e EXP-005. Lotes com vencimento são consumidos primeiro (por data de vencimento ASC). Lotes sem vencimento são consumidos por último, em ordem FIFO.

## 14.3 Gestão de Vencimentos

**Status: Implementado no M8 (Fase 2).**

Cada lote de estoque pode ter uma data de vencimento opcional. O sistema consome primeiro os lotes com vencimento mais próximo (FEFO — First Expired, First Out). Lotes sem vencimento são consumidos por último, em ordem FIFO.

Capacidades potenciais:

* datas de vencimento;
* alertas de vencimento;
* produtos próximos do vencimento;
* uso preferencial de produtos com vencimento mais próximo;
* visibilidade do estoque vencido.

Uma estratégia que prioriza o vencimento mais próximo é atualmente uma possível política de negócio.

Ela deve permanecer uma regra de negócio substituível, em vez de se tornar uma suposição arquitetural.

## 14.4 Reposição de Estoque

**Status: Implementado no M9 (Fase 2).**

O sistema calcula, para cada produto, o estoque atual (soma dos lotes ativos), a necessidade estimada (templates de cesta ativos) e a necessidade urgente (vendas confirmadas). Cada produto é classificado como OK, BAIXO ou CRÍTICO.

Capacidades implementadas:

* identificar produtos necessários para cestas futuras;
* identificar estoque insuficiente;
* destacar produtos que precisam ser repostos;
* distinguir necessidades normais de estoque das necessidades urgentes criadas por vendas confirmadas;
* filtros por status (BAIXO, CRÍTICO) e por produto.

O sistema oferece visibilidade antes de automatizar as compras. A automação de compras é explicitamente fora do escopo do M9.

## 14.5 Datas Afetivas

**Status: Implementado no M10 (Fase 2).**

O M3 (Clientes) permite registrar datas importantes vinculadas a clientes específicos (aniversários, ocasiões especiais) com recorrência e status. O M10 adiciona uma visão global: listar todas as datas afetivas próximas de todos os clientes.

Capacidades implementadas:

* registrar datas importantes por cliente (M3);
* listar datas próximas via endpoint global `GET /api/v1/important-dates/upcoming?days=7` (M10);
* visualizar datas afetivas no frontend com filtros (hoje, 7 dias, 30 dias) (M10);
* cálculo de próxima ocorrência para datas recorrentes e não-recorrentes, incluindo ano bissexto (M10).

Capacidades futuras (fora do escopo do M10):

* notificar o negócio sobre datas afetivas próximas (Fase 4);
* apoiar o contato proativo com clientes;
* registro de "contato realizado" para datas afetivas.

O sistema segue o princípio "visibilidade antes de automação" — o M10 oferece visibilidade das datas próximas, mas não automatiza notificações.

---

# 15. Fase 3 — Infraestrutura & Acesso

Após a Fase 2, o próximo passo é colocar o sistema em produção e habilitar acesso controlado por usuários autenticados.

Esta fase prepara o sistema para ser usado por pessoas fora do ambiente de desenvolvimento.

## 15.1 M11 — Deploy & Ambiente de Produção ✅

**Status:** Concluído (2026-10-29)
**Ambiente:** Oracle Cloud Always Free — `http://164.152.48.51`

O primeiro marco da Fase 3 foca em tornar o sistema acessível em um ambiente de produção.

Capacidades entregues:

* Dockerfiles de produção (backend e frontend);
* Docker Compose de produção com 5 serviços (PostgreSQL, backend, frontend, Nginx, backup);
* Nginx como reverse proxy (`/api/` → backend, `/` → frontend);
* Variáveis de ambiente seguras (`.env.prod.example`);
* Backup automatizado via `pg_dump` com cron;
* Healthchecks em todos os serviços;
* Guia de deploy completo com lições aprendidas.

Capacidades adiadas (pendente domínio):

* SSL/TLS via Let's Encrypt;
* Redirecionamento HTTP → HTTPS.

Este marco não introduz novas funcionalidades de negócio — prepara a infraestrutura para o sistema operar em produção.

## 15.2 M12 — Autenticação & Área de Usuários

O segundo marco da Fase 3 habilita o acesso controlado ao sistema.

Capacidades planejadas:

* cadastro de usuários com login/senha;
* recuperação de senha por email;
* roles: admin e operador;
* proteção de rotas no frontend e backend;
* página de login e área de perfil.

M12 depende de M11, pois o sistema precisa estar em produção para que o acesso autenticado seja útil para usuários externos.

## 15.3 Sequência de Desenvolvimento

```text
M11 — Deploy & Ambiente de Produção ✅
        ↓
M12 — Autenticação & Área de Usuários ✅
```

A ordem é intencional: o deploy precede a autenticação, pois o sistema precisa estar acessível antes de proteger o acesso.

---

# 16. Fase 4 — Automação Operacional

Depois que a operação central, a evolução de estoque/clientes e a infraestrutura de acesso estiverem estáveis, o sistema poderá evoluir para reduzir o trabalho repetitivo.

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

# 17. Oportunidades Futuras

As capacidades a seguir poderão se tornar relevantes conforme a Casa Afeto crescer.

Elas estão registradas aqui como possibilidades, não como compromissos.

## 17.1 Produção Interna

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

## 17.2 Precificação Avançada

Funcionalidades futuras de precificação podem incluir:

* regras de precificação;
* análise de margem;
* preços históricos;
* precificação sazonal;
* promoções;
* descontos.

O sistema atual não deve implementar esses conceitos de forma especulativa.

## 17.3 Gestão Avançada de Clientes

Possíveis capacidades futuras:

* histórico de clientes;
* padrões de compra;
* preferências de clientes;
* segmentação;
* análise de compras recorrentes;
* ofertas personalizadas.

Elas só devem ser introduzidas se oferecerem valor operacional ou comercial mensurável.

## 17.4 Análises de Negócio

As análises devem evoluir a partir de dados reais e de perguntas do negócio.

## 17.5 Multi-tenancy

O sistema pode evoluir para atender múltiplos clientes (tenants) em uma única instância, com isolamento de dados entre eles.

Capacidades potenciais:

* uma instância atendendo múltiplos clientes isolados;
* isolamento de dados por tenant;
* configuração específica por tenant;
* gestão de tenants.

Essa capacidade só deve ser introduzida quando o negócio definir claramente a necessidade de operar múltiplos clientes na mesma infraestrutura.

O termo **multi-tenancy** refere-se à arquitetura onde uma única instância do sistema atende múltiplos clientes com isolamento lógico de dados entre eles.

---

# 18. Classificação do Backlog

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

# 19. Política de Mudanças do Roadmap

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

# 20. Relação entre Roadmap e Especificações

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

# 21. Encerramento de M1 e Estado Atual dos Marcos

O Product Owner realizou a aceitação humana de **M1 — Produtos e Estoque**. Todas as etapas do marco foram concluídas:

```text
Implementação:       Concluída
Refinamento visual:  Concluído
Validação:           Concluída
Aceitação humana:    Concluída
Status geral:        Concluído (COMPLETED)
```

O **M2 — Cestas e Templates de Cesta** passou originalmente pelo ciclo aprovado e foi aceito pelo Product Owner em 2026-10-06. A reabertura pontual de escopo para implementação e validação da persistência de preços, custos de aquisição em entradas de estoque e sugestão de preço (2 × custo) foi implementada, validada e aceita:

```text
Conclusão original:  COMPLETED (VALIDATED / Aprovação humana concluída em 2026-10-06)
Reabertura pontual:  Custos de aquisição e sugestão de preço das cestas
Status da correção:  Concluída e aprovada (COMPLETED / Aprovação humana concluída)
Status geral de M2:  Concluído (COMPLETED)
```

M3 — Clientes e Datas Importantes está concluído (COMPLETED) após Validation/Review e aceitação humana pelo Product Owner.

As decisões fundamentais de negócio da especificação M1 foram resolvidas:

* **Política de estoque negativo: RESOLVIDA**
  * **Política:** o estoque físico nunca deve ficar negativo (`INV-006`).
  * Operações que produziriam um saldo negativo são rejeitadas.
  * Este invariante é absoluto e também se aplica a operações concorrentes de estoque (`ADR-001`).

M4 — Vendas está concluído (COMPLETED) após implementação, refinamento visual, validação automatizada (6 testes) e aceitação humana pelo Product Owner em 2026-10-10.

M5 — Pagamentos está concluído (COMPLETED) após implementação backend e frontend, validação automatizada (101 testes + 54 verificações API), validação manual parcial (3 cenários via UI) e aceitação humana pelo Product Owner em 2026-10-15.

**A Fase 1 está concluída.** O fluxo operacional central da Casa Afeto está funcional:

```text
Produto → Estoque → Cesta → Cliente → Venda → Pagamento → Confirmação → Entrega
```

**A Fase 2 está concluída.** As capacidades de evolução de estoque e clientes estão funcionais:

```text
Compras → Lotes → Vencimentos → Reposição → Datas Afetivas
```

M6 — Compras está concluído (COMPLETED).
M7 — Lotes de Estoque está concluído (COMPLETED).
M8 — Vencimentos está concluído (COMPLETED).
M9 — Reposição de Estoque está concluído (COMPLETED).
M10 — Datas Afetivas está concluído (COMPLETED).

---

# 22. Resumo do Roadmap

```text
FASE 1 — OPERAÇÕES CENTRAIS (Concluída)
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


FASE 2 — EVOLUÇÃO DO ESTOQUE E DOS CLIENTES (Concluída)
─────────────────────────────────────

M6  Compras
 ↓
M7  Lotes de Estoque
 ↓
M8  Vencimentos
 ↓
M9  Reposição de Estoque
 ↓
M10 Datas Afetivas


FASE 3 — INFRAESTRUTURA & ACESSO
─────────────────────────────────────

M11 Deploy & Ambiente de Produção ✅
 ↓
M12 Autenticação & Área de Usuários ✅


FASE 4 — AUTOMAÇÃO OPERACIONAL
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
Multi-tenancy
```

O roadmap existe para fornecer direção sem se tornar uma restrição ao aprendizado.

O sistema deve evoluir conforme as necessidades reais da Casa Afeto, com cada capacidade entrando em desenvolvimento somente quando seu valor e comportamento de negócio forem suficientemente compreendidos.
