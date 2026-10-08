# M2 — Casos de Uso de Cestas e Templates de Cesta

**Versão do documento:** 0.1  
**Status:** COMPLETED  
**Implementation Gate:** READY FOR IMPLEMENTATION  
**Implementation:** Concluída  
**Validation/Review:** VALIDATED  
**Aprovação humana:** Concluída  
**Marco:** M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)

Os casos de uso abaixo não definem exclusão, arquivamento ou duplicação. As decisões de negócio aplicáveis estão formalizadas na especificação do marco.

---

## UC-M2-01 — Criar template

**Objetivo:** Registrar um template de composição reutilizável.

**Pré-condições:** Os produtos a incluir estão ativos e cadastrados em M1.

**Fluxo principal:**
1. O usuário inicia a criação de um template.
2. Informa o nome.
3. Opcionalmente seleciona produtos ativos e suas quantidades.
4. Salva o template.

**Alternativas:**
* Se um produto selecionado estiver inativo, ele não pode ser incluído; o usuário seleciona outro produto ativo.
* Se o template for salvo sem itens, permanece ativo, mas não pode originar uma cesta até que tenha ao menos um item.

**Regras aplicáveis:** Template novo nasce ativo por padrão, sem estado DRAFT. Quantidades usam unidade base de M1. Repetir um produto já presente incrementa sua quantidade em vez de criar outra linha. Custo, preço e estoque não são alterados.

**Resultado esperado:** O template e sua composição ficam persistidos e consultáveis.

## UC-M2-02 — Consultar e visualizar templates

**Objetivo:** Localizar e inspecionar templates existentes, ativos ou inativos.

**Pré-condições:** Há templates persistidos para consulta.

**Fluxo principal:**
1. O usuário solicita a lista de templates.
2. O sistema apresenta os templates e seus estados.
3. O usuário seleciona um template.
4. O sistema apresenta seu nome, estado e composição, identificando produtos atualmente inativos.

**Alternativas:** Se não houver resultado, o sistema apresenta uma lista vazia.

**Regras aplicáveis:** Template inativo permanece consultável. Produto inativo em composição existente não é removido.

**Resultado esperado:** O template selecionado e sua composição são apresentados sem alteração.

## UC-M2-03 — Editar composição ou dados de template

**Objetivo:** Atualizar explicitamente um template existente.

**Pré-condições:** O template está persistido.

**Fluxo principal:**
1. O usuário abre o template para edição.
2. Altera seu nome ou composição.
3. Salva as alterações.

**Alternativas:**
* Produtos ativos podem ser adicionados.
* Produtos inativos já referenciados podem ser mantidos, ter sua quantidade alterada ou ser removidos.
* Para substituir um produto inativo, o usuário remove/substitui explicitamente a referência por um produto ativo.
* Se o produto substituto já estiver na composição, as quantidades são agregadas e o produto permanece em uma única linha.

**Regras aplicáveis:** A edição do template não altera cestas já criadas a partir dele. Cada produto aparece no máximo uma vez; nova inclusão do mesmo produto incrementa a quantidade existente.

**Resultado esperado:** As mudanças ficam persistidas no template, sem alterar cestas existentes.

## UC-M2-04 — Ativar ou desativar template

**Objetivo:** Controlar se um template pode originar novas cestas.

**Pré-condições:** O template está persistido.

**Fluxo principal:**
1. O usuário consulta o template.
2. Escolhe ativar ou desativar.
3. Confirma a alteração.
4. O sistema persiste o novo estado.

**Alternativas:** Se a operação não puder ser concluída, o erro é informado e o estado anterior permanece.

**Regras aplicáveis:** Template inativo continua consultável e editável, mas não pode originar cesta nova.

**Resultado esperado:** O estado é atualizado sem excluir o template ou alterar cestas existentes.

## UC-M2-05 — Criar cesta a partir de template

**Objetivo:** Criar uma composição concreta baseada em um template utilizável.

**Pré-condições:** O template está ativo, contém ao menos um item e todos os produtos em sua composição estão ativos.

**Fluxo principal:**
1. O usuário seleciona um template utilizável.
2. Informa o nome da nova cesta.
3. O sistema copia a composição e as quantidades atuais do template.
4. O sistema registra opcionalmente o `template_id` como origem.
5. O usuário salva a cesta.

**Alternativas:**
* Template inativo não pode ser selecionado para criação.
* Template que contenha produto inativo não pode originar cesta; o sistema identifica a condição e o usuário corrige explicitamente o template antes de tentar novamente.
* Template ativo vazio não pode originar cesta; o usuário precisa adicionar ao menos um item.
* Produto sem estoque suficiente não impede a criação; é apresentado aviso informativo.

**Regras aplicáveis:** A composição é uma cópia, não uma referência viva. Não há vínculo com venda nem movimentação de estoque.

**Resultado esperado:** Cesta persistida com composição independente e origem opcional registrada.

## UC-M2-06 — Criar cesta sem template

**Objetivo:** Criar uma composição concreta sem template de origem.

**Pré-condições:** O usuário tem acesso à operação de criação de cesta.

**Fluxo principal:**
1. O usuário inicia uma cesta sem template.
2. Informa o nome.
3. Opcionalmente adiciona produtos ativos e quantidades.
4. Salva a cesta.

**Alternativas:**
* O usuário pode salvar sem itens.
* Produto inativo não pode ser incluído.
* Produto sem estoque suficiente pode ser incluído com aviso.

**Regras aplicáveis:** `template_id` fica ausente; custo/preço e dados de venda não são solicitados.

**Resultado esperado:** Cesta persistida, inclusive quando vazia.

## UC-M2-07 — Consultar e visualizar cestas

**Objetivo:** Localizar e inspecionar cestas existentes.

**Pré-condições:** Há cestas persistidas para consulta.

**Fluxo principal:**
1. O usuário solicita a lista de cestas.
2. O sistema apresenta as cestas disponíveis.
3. O usuário seleciona uma cesta.
4. O sistema apresenta nome, origem quando existente e composição.
5. O sistema identifica claramente produtos inativos e pode apresentar disponibilidade informativa.

**Alternativas:** Se não houver resultado, o sistema apresenta uma lista vazia.

**Regras aplicáveis:** Consulta de disponibilidade não reserva nem altera estoque.

**Resultado esperado:** Os dados persistidos são apresentados sem alteração.

## UC-M2-08 — Editar uma cesta

**Objetivo:** Alterar explicitamente nome ou composição de uma cesta existente.

**Pré-condições:** A cesta está persistida.

**Fluxo principal:**
1. O usuário abre a cesta para edição.
2. Mantém, adiciona, remove, substitui itens ou altera quantidades.
3. Salva a cesta.

**Alternativas:**
* Itens que referenciam produtos inativos permanecem identificáveis e podem ser mantidos ou removidos.
* O usuário pode editar outros itens mesmo quando a cesta contém um produto inativo.
* O usuário pode alterar a quantidade de um item existente cujo produto foi desativado; não pode incluir o produto inativo novamente.
* Remover todos os itens é permitido e a cesta vazia pode ser salva.
* A inclusão de novos itens requer produto ativo.
* Incluir novamente produto ativo que já existe incrementa a quantidade existente, mantendo uma única linha.

**Regras aplicáveis:** Não há estado comercial; a cesta permanece editável. Não ocorre movimentação de estoque.

**Resultado esperado:** A cesta é salva com as alterações explícitas, inclusive sem itens.

## UC-M2-09 — Substituir produto em composição

**Objetivo:** Trocar explicitamente um produto por outro em um template ou cesta.

**Pré-condições:** A composição contém o item que o usuário deseja substituir; o produto substituto está ativo.

**Fluxo principal:**
1. O usuário escolhe o item a substituir.
2. Seleciona explicitamente outro produto ativo.
3. Define a quantidade aplicável e salva a composição.

**Alternativas:** Se o produto substituto estiver inativo, ele não pode ser selecionado.

**Regras aplicáveis:** Nunca há substituição automática por desativação. Produto sem estoque suficiente pode ser escolhido com aviso.

**Resultado esperado:** A referência anterior é substituída somente após ação explícita do usuário.

## UC-M2-10 — Usar produto sem estoque suficiente

**Objetivo:** Compor uma cesta ou template com produto cuja disponibilidade não atende à quantidade desejada.

**Pré-condições:** Produto ativo selecionado; M1 disponibiliza informação de disponibilidade.

**Fluxo principal:**
1. O usuário seleciona produto ativo e quantidade.
2. O sistema consulta disponibilidade informativa.
3. Se insuficiente, mostra aviso.
4. O usuário pode manter a composição e salvá-la.

**Alternativas:** A disponibilidade pode mudar depois da consulta e não bloqueia o salvamento.

**Regras aplicáveis:** Não reservar, deduzir ou movimentar estoque; não criar regra de concorrência.

**Resultado esperado:** A composição é salva e o estoque permanece inalterado.

## UC-M2-11 — Composição após mudança de produto

**Objetivo:** Preservar a identidade da referência quando atributos do produto mudam em M1.

**Pré-condições:** Um template ou cesta referencia produto por `product_id`.

**Fluxo principal:**
1. O nome do produto é alterado em M1; a composição continua referenciando o mesmo ID e a interface pode exibir o nome atual.
2. Se o produto for desativado, as referências existentes permanecem; não há inclusão nova e a interface o identifica como inativo.
3. Se a unidade base puder ser alterada segundo M1, a referência em composição não impede a mudança.

**Alternativas:** Não há conversão de unidades nem histórico de nomes/unidades no M2.

**Regras aplicáveis:** Regras de estado e mutabilidade da unidade base são as do M1.

**Resultado esperado:** Identidade e quantidades persistidas não são alteradas automaticamente.
