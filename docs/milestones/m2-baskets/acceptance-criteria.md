# M2 — Critérios de Aceitação

**Versão do documento:** 0.1  
**Status:** COMPLETED  
**Implementation Gate:** READY FOR IMPLEMENTATION  
**Implementation:** Concluída  
**Validation/Review:** VALIDATED  
**Aprovação humana:** Concluída  
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

### AC-M2-018 — Sem custo ou preço

**Dado** qualquer criação, consulta ou edição de template/cesta no M2,  
**então** não são calculados nem persistidos como comportamento de domínio custo, custo de cesta, preço sugerido, preço final, margem ou markup.

### AC-M2-019 — Sem dados ou estados de venda

**Dado** uma cesta do M2,  
**então** ela não possui vínculo estrutural com Sale/Venda, cliente, pagamento, destinatário, entrega ou estados comerciais como confirmada, vendida, entregue, cancelada ou paga.

## Open Questions

None. As decisões anteriormente pendentes estão cobertas pelos critérios acima.
