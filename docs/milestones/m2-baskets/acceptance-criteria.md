# M2 — Critérios de Aceitação

**Versão do documento:** 0.3
**Status geral:** Concluído (COMPLETED)
**Histórico da conclusão original de M2:** Concluída e aprovada (COMPLETED / VALIDATED / Aprovação humana concluída em 2026-10-06)
**Status da correção pontual:** Concluída e aprovada (COMPLETED)
**Validação da correção pontual:** Validada (testes automatizados e aceitação humana concluídos)
**Fechamento da reabertura:** Concluído (implementação, testes automatizados e aprovação humana concluídos)
**Marco:** M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)

Os critérios abaixo descrevem resultados observáveis para as decisões de negócio aprovadas.

---

## Templates

### AC-M2-001 — Criar e consultar template

**Dado** que o usuário crie um template com nome,
**quando** salvá-lo com ou sem itens,
**então** o template fica persistido, nasce ativo por padrão e pode ser listado e visualizado.

### AC-M2-001a — Template vazio ativo não origina cesta

**Dado** um template vazio recém-criado,
**quando** o usuário tentar criar uma cesta a partir dele,
**então** a operação é impedida até que o template tenha ao menos um item;
**e** o template continua ativo, persistido e editável.

### AC-M2-002 — Editar template

**Dado** um template persistido,
**quando** o usuário editar seu nome ou composição e salvar,
**então** a alteração aparece ao consultar o template e não altera cestas já criadas a partir dele.

### AC-M2-003 — Ativar e desativar template

**Dado** um template persistido,
**quando** o usuário alterar seu estado,
**então** o estado é persistido, o template continua consultável e um template inativo não pode originar nova cesta.

### AC-M2-004 — Template com produto inativo

**Dado** um template existente que referencia produto posteriormente desativado,
**quando** o template for consultado,
**então** a referência permanece e o produto é identificado como inativo;
**e**, enquanto essa composição contiver produto inativo, o template não pode originar nova cesta.

### AC-M2-004a — Ativar template após produto inativo ser resolvido

**Dado** um template que foi corrigido explicitamente para não conter produtos inativos,
**quando** estiver ativo e possuir ao menos um item,
**então** ele pode originar uma nova cesta.

## Cestas

### AC-M2-005 — Criar cesta com template

**Dado** um template ativo, com ao menos um item, cuja composição contém somente produtos ativos,
**quando** o usuário criar e salvar uma cesta a partir dele,
**então** a cesta e seus itens são persistidos com a composição existente no instante da criação, e o template de origem pode ser identificado sem manter composição sincronizada.

### AC-M2-006 — Criar cesta sem template

**Dado** que o usuário escolha criar uma cesta sem template,
**quando** informar o nome e salvar, com ou sem itens,
**então** a cesta é persistida sem origem de template.

### AC-M2-007 — Cesta vazia

**Dado** uma cesta nova ou existente,
**quando** ela for salva sem itens, inclusive após remoção de todos os itens,
**então** o salvamento é aceito e a cesta permanece consultável e editável.

### AC-M2-008 — Independência entre template e cesta

**Dado** uma cesta criada a partir de template,
**quando** o usuário alterar e salvar o template,
**então** os itens e quantidades da cesta não mudam;
**e**, quando alterar a cesta, o template não muda.

### AC-M2-009 — Editar composição

**Dado** uma cesta persistida,
**quando** o usuário adicionar, remover ou substituir explicitamente itens, alterar quantidades e salvar,
**então** a composição atualizada fica persistida e pode ser visualizada. A cesta permanece editável.

### AC-M2-010 — Produto inativo em composição existente

**Dado** uma cesta ou template que já referencia produto posteriormente desativado,
**quando** a composição for visualizada ou editada,
**então** a referência é preservada, o estado inativo é claramente identificável, outros itens continuam editáveis e o item inativo pode ser mantido, ter sua quantidade alterada ou ser removido;
**e** nenhuma substituição automática ocorre.

### AC-M2-011 — Impedir nova inclusão de produto inativo

**Dado** um produto inativo,
**quando** o usuário tentar incluí-lo como novo item em template ou cesta,
**então** a inclusão não é permitida; o usuário pode escolher explicitamente outro produto ativo.

### AC-M2-011a — Agregar inclusão repetida do mesmo produto

**Dado** uma composição que já contém um produto,
**quando** o usuário incluir novamente esse mesmo produto com uma quantidade válida,
**então** a quantidade solicitada é somada à quantidade existente e o produto permanece em uma única linha.

### AC-M2-011b — Agregar produto existente durante substituição

**Dado** uma composição com item a substituir e que já contenha o produto ativo escolhido como substituto,
**quando** o usuário confirmar a substituição,
**então** as quantidades do item substituído e do produto existente são somadas, preservando uma única linha para o produto substituto.

### AC-M2-012 — Impedir criação a partir de template inativo

**Dado** um template inativo,
**quando** o usuário tentar usá-lo para criar uma cesta nova,
**então** a operação é impedida e o template permanece consultável, editável e reativável.

### AC-M2-013 — Renomeação de produto

**Dado** uma composição que referencia um produto,
**quando** o nome desse produto mudar em M1,
**então** a referência continua usando o mesmo `product_id`, a quantidade não muda e a interface pode apresentar o nome atual.

### AC-M2-014 — Unidade base

**Dado** produto referenciado em cesta ou template sem movimentação de estoque,
**quando** uma mudança de unidade base for permitida pelas regras de M1,
**então** a mera referência em M2 não impede a mudança; M2 não converte a quantidade nem registra histórico de unidades.

### AC-M2-015 — Quantidades e unidades

**Dado** composição com item de produto,
**quando** sua quantidade for validada,
**então** a quantidade é maior que zero, `UN` aceita quantidades inteiras e `KG`, `G`, `L` e `ML` aceitam quantidades decimais, conforme unidades controladas por M1.

### AC-M2-015a — Unicidade de produto por composição

**Dado** qualquer template ou cesta,
**então** cada `product_id` aparece no máximo uma vez na composição persistida.

## Estoque, custo e preço

### AC-M2-016 — Estoque insuficiente é aviso

**Dado** um produto ativo cuja disponibilidade consultada é menor que a quantidade desejada,
**quando** o usuário o incluir em uma composição,
**então** o sistema apresenta aviso informativo, não bloqueia a composição e permite salvá-la.

### AC-M2-017 — Nenhuma movimentação de estoque

**Dado** que o usuário crie ou edite template/cesta, inclusive com disponibilidade insuficiente,
**quando** salvar a operação,
**então** M2 não reserva nem deduz estoque, não altera quantidade disponível e não cria movimentação de estoque.

### AC-M2-018 — Preservação de escopo: sem regras comerciais além do aprovado

**Dado** qualquer criação, consulta ou edição de template/cesta no M2,
**então** não são calculadas regras de margem ou markup comercial além da regra aprovada de sugestão (2 × custo de referência da cesta);
**e** não são executadas reservas ou deduções de estoque nem criados fluxos de vendas.

### AC-M2-019 — Sem dados ou estados de venda

**Dado** uma cesta do M2,
**então** ela não possui vínculo estrutural com Sale/Venda, cliente, pagamento, destinatário, entrega ou estados comerciais como confirmada, vendida, entregue, cancelada ou paga.

### AC-M2-020 — Preço de venda manual persistido na cesta-modelo

**Dado** uma cesta-modelo a ser criada com preço de venda positivo e precisão de duas casas decimais (ex.: `150.00`),
**quando** o usuário salvar e posteriormente consultar a cesta-modelo,
**então** o preço informado é persistido com precisão de duas casas decimais e exibido na consulta de detalhes do template.

### AC-M2-021 — Criação e manutenção de cesta-modelo sem preço

**Dado** uma cesta-modelo a ser criada ou editada sem preço informado (preço ausente / `null`),
**quando** o usuário salvá-la,
**então** a cesta-modelo é persistida com preço ausente, permanece ativa, consultável e editável no M2 e não recebe nenhum valor fictício, estimado ou padrão.

### AC-M2-022 — Edição e persistência do preço da cesta-modelo

**Dado** uma cesta-modelo já persistida, com ou sem preço definido,
**quando** o usuário editar seu preço para um novo valor válido com duas casas decimais e salvar,
**então** o novo preço é persistido no registro da cesta-modelo e refletido em consultas subsequentes.

### AC-M2-023 — Aceitação de preço zero como valor definido

**Dado** que o usuário defina explicitamente o preço de uma cesta-modelo como zero (`0.00`) para fins de cortesia ou brinde,
**quando** salvar a cesta-modelo,
**então** o sistema persiste o valor zero como preço definido;
**e** essa condição é tratada como preço válido definido, sendo categoricamente diferente de preço ausente.

### AC-M2-024 — Rejeição de preço negativo

**Dado** uma tentativa de cadastrar ou editar o preço de uma cesta-modelo com valor negativo (ex.: `-10.00`),
**quando** a validação for acionada,
**então** o sistema rejeita a operação com erro de validação de valor mínimo não atendido e não persiste o valor.

### AC-M2-025 — Rejeição de preço com mais de duas casas decimais

**Dado** uma tentativa de cadastrar ou editar o preço de uma cesta-modelo com precisão superior a duas casas decimais (ex.: `50.125`),
**quando** a validação for acionada,
**então** o sistema rejeita a operação exigindo precisão de exatamente até duas casas decimais;
**e** não aplica nenhum arredondamento ou truncamento automático silencioso.

### AC-M2-026 — Bloqueio de inclusão em venda quando preço estiver ausente

**Dado** uma cesta-modelo cadastrada com preço ausente (`null`),
**quando** uma rotina de venda (M4) tentar adicioná-la como item de venda,
**então** a inclusão na venda é bloqueada até que um preço válido (zero ou positivo) seja manualmente definido na cesta-modelo de origem.

### AC-M2-027 — Preservação do preço histórico na venda após alteração da cesta-modelo

**Dado** uma cesta-modelo cujo preço vigente foi copiado para uma venda preexistente em M4,
**quando** o preço da cesta-modelo for posteriormente alterado ou removido no M2,
**então** o preço registrado na venda anterior permanece inalterado (snapshot histórico imutável).

### AC-M2-028 — Preservação de registros preexistentes sem preços fictícios

**Dado** o conjunto de cestas-modelo preexistentes criadas antes da introdução do campo de preço,
**quando** a migration de compatibilidade for executada,
**então** todos os registros antigos continuam com preço ausente (`null`);
**e** o sistema não atribui valores padrão, fictícios ou estimados a nenhum registro preexistente.

### AC-M2-029 — Cálculo de preço sugerido como 2 × custo de referência da cesta

**Dado** uma cesta ou template com composição não vazia onde todos os produtos possuem `reference_price` definido,
**quando** a composição for consultada ou editada,
**então** o sistema calcula e apresenta o custo de referência da cesta (somatório de `quantidade × reference_price` de cada item) e a sugestão de preço igual a **2 × custo de referência da cesta**.

### AC-M2-030 — Registro de custo de aquisição na entrada de estoque

**Dado** uma movimentação de estoque do tipo entrada (`ENTRY`),
**quando** o operador registrar a movimentação informando opcionalmente o custo unitário de aquisição (`unit_cost`) com precisão de duas casas decimais e valor não negativo,
**então** o custo unitário é persistido junto à movimentação de entrada;
**e** movimentações com valor negativo são rejeitadas pela validação.

### AC-M2-031 — Custo médio ponderado do produto com entradas de custo conhecido

**Dado** um produto com múltiplas entradas de estoque,
**quando** o custo médio unitário for calculado,
**então** o sistema pondera as quantidades e custos apenas das entradas que possuem custo de aquisição registrado;
**e** entradas sem custo informado são ignoradas no cálculo, não sendo tratadas como custo zero.

### AC-M2-032 — Custo de referência da composição da cesta

**Dado** uma composição de cesta ou template com um ou mais itens,
**quando** o custo de referência for calculado,
**então** ele corresponde à soma exata de `quantidade × reference_price` de cada item na composição.

### AC-M2-033 — Autonomia do operador na precificação

**Dado** uma sugestão de preço calculada pelo sistema (2 × custo de referência),
**quando** o operador visualizar a sugestão na interface de criação ou edição da cesta-modelo,
**então** o operador pode aceitar a sugestão com um clique ou informar manualmente qualquer outro preço válido;
**e** o sistema persiste o preço escolhido pelo operador.

### AC-M2-034 — Não sobrescrita automática de preço já definido

**Dado** uma cesta-modelo que já possui um preço de venda definido e salvo,
**quando** o preço de referência dos produtos componentes for alterado,
**então** o preço de venda previamente salvo permanece inalterado e não é sobrescrito automaticamente pelo sistema.

### AC-M2-035 — Recálculo de sugestão sem alterar preço salvo

**Dado** uma cesta ou template com preço de venda já salvo,
**quando** o usuário editar a composição ou solicitar uma nova sugestão de preço,
**então** o custo de referência e a sugestão são recalculados com base nos dados atuais,
**mas** o preço de venda já salvo permanece inalterado até que o usuário decida explicitamente aceitar a nova sugestão ou salvar um novo valor.

### AC-M2-036 — Indisponibilidade de sugestão por `reference_price` ausente

**Dado** uma composição onde pelo menos um produto não possui `reference_price` definido, ou uma composição vazia sem itens,
**quando** a composição for consultada ou editada,
**então** o sistema indica que o custo de referência e o preço sugerido estão indisponíveis;
**e** a interface apresenta aviso claro de dados insuficientes, sem exibir sugestão como valor confiável e permitindo ao operador definir o preço manualmente.

### AC-M2-037 — Indisponibilidade de sugestão quando `reference_price` ausente

**Dado** uma composição onde pelo menos um produto não possui `reference_price` definido,
**quando** a composição for consultada ou editada,
**então** o custo de referência e o preço sugerido estão indisponíveis;
**e** o operador pode definir o preço manualmente.

## Open Questions

None. As decisões formalizadas pelo Product Owner estão cobertas pelos critérios acima.
