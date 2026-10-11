# M2 — Casos de Uso de Cestas e Templates de Cesta

**Versão do documento:** 0.3
**Status geral:** Concluído (COMPLETED)
**Histórico da conclusão original de M2:** Concluída e aprovada (COMPLETED / VALIDATED / Aprovação humana concluída em 2026-10-06)
**Status da correção pontual:** Concluída e aprovada (COMPLETED)
**Validação da correção pontual:** Validada (testes automatizados e aceitação humana concluídos)
**Fechamento da reabertura:** Concluído (implementação, testes automatizados e aprovação humana concluídos)
**Marco:** M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)

Os casos de uso abaixo não definem exclusão, arquivamento ou duplicação. As decisões de negócio aplicáveis estão formalizadas na especificação do marco.

Correções pontuais aprovadas em M2 antes de M4: incluir definição e persistência de preço de venda da cesta-modelo, registro de custo unitário de aquisição nas entradas de estoque para controle interno, cálculo de custo de referência da cesta a partir de `quantidade × reference_price`, e sugestão de preço igual a 2 × custo de referência, com total autonomia do operador e garantia de não sobrescrita de preços salvos.

---

## UC-M2-01 — Criar template

**Objetivo:** Registrar um template de composição reutilizável (cesta-modelo), com preço de venda opcional.

**Pré-condições:** Os produtos a incluir estão ativos e cadastrados em M1.

**Fluxo principal:**
1. O usuário inicia a criação de um template.
2. Informa o nome.
3. Opcionalmente informa o preço de venda manual (com precisão de duas casas decimais).
4. Opcionalmente seleciona produtos ativos e suas quantidades.
5. Salva o template.

**Alternativas:**
* Se um produto selecionado estiver inativo, ele não pode ser incluído; o usuário seleciona outro produto ativo.
* Se o template for salvo sem itens, permanece ativo, mas não pode originar uma cesta até que tenha ao menos um item.
* Se o usuário não informar preço de venda, o template é salvo com preço ausente (`null`), podendo ser precificado posteriormente.
* Se o usuário informar preço zero (`0.00`), o valor é salvo como preço definido (brinde/cortesia), distinto de ausência de preço.
* Se o usuário informar valor negativo ou com precisão superior a duas casas decimais, o sistema rejeita a operação com erro de validação.

**Regras aplicáveis:** Template novo nasce ativo por padrão, sem estado DRAFT. Quantidades usam unidade base de M1. Repetir um produto já presente incrementa sua quantidade em vez de criar outra linha. Custo e estoque não são alterados automaticamente; preço de venda da cesta-modelo é manual com precisão de duas casas decimais. Ausência de preço impede posterior inclusão em venda (M4).

**Resultado esperado:** O template, sua composição e seu preço opcional ficam persistidos e consultáveis.

## UC-M2-02 — Consultar e visualizar templates

**Objetivo:** Localizar e inspecionar templates existentes, ativos ou inativos, visualizando composição e preço.

**Pré-condições:** Há templates persistidos para consulta.

**Fluxo principal:**
1. O usuário solicita a lista de templates.
2. O sistema apresenta os templates, seus estados e seus preços de venda (quando definidos).
3. O usuário seleciona um template.
4. O sistema apresenta seu nome, estado, preço de venda (ou indicação explícita de ausência de preço) e composição, identificando produtos atualmente inativos.

**Alternativas:** Se não houver resultado, o sistema apresenta uma lista vazia.

**Regras aplicáveis:** Template inativo permanece consultável. Produto inativo em composição existente não é removido. Preço ausente é visualmente diferenciado de preço zero.

**Resultado esperado:** O template selecionado, seu preço e sua composição são apresentados sem alteração.

## UC-M2-03 — Editar composição ou dados de template

**Objetivo:** Atualizar explicitamente um template existente, seu nome, preço de venda ou composição.

**Pré-condições:** O template está persistido.

**Fluxo principal:**
1. O usuário abre o template para edição.
2. Altera seu nome, seu preço de venda ou sua composição.
3. Salva as alterações.

**Alternativas:**
* O usuário pode definir um preço para um template que estava sem preço, alterar um preço existente ou definir preço zero.
* Tentativas de salvar preço negativo ou com mais de duas casas decimais são rejeitadas.
* Produtos ativos podem ser adicionados.
* Produtos inativos já referenciados podem ser mantidos, ter sua quantidade alterada ou ser removidos.
* Para substituir um produto inativo, o usuário remove/substitui explicitamente a referência por um produto ativo.
* Se o produto substituto já estiver na composição, as quantidades são agregadas e o produto permanece em uma única linha.

**Regras aplicáveis:** A edição do template não altera cestas já criadas a partir dele nem altera preços já copiados para vendas em M4 (snapshot histórico). Cada produto aparece no máximo uma vez; nova inclusão do mesmo produto incrementa a quantidade existente.

**Resultado esperado:** As mudanças ficam persistidas no template, sem alterar cestas ou vendas existentes.

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

**Regras aplicáveis:** `template_id` fica ausente; custo e dados de venda não são solicitados. Preço de venda da cesta-modelo, quando aplicável, é manual e persistido sem cálculo automático.

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

## UC-M2-12 — Definir preço de venda da cesta-modelo

**Objetivo:** Registrar ou alterar o preço de venda persistido da cesta-modelo para uso em vendas futuras.

**Pré-condições:** A cesta-modelo existe no M2 (com ou sem preço definido).

**Fluxo principal:**
1. O usuário abre a cesta-modelo para visualização ou edição.
2. Informa manualmente um valor de preço de venda positivo com até duas casas decimais (ex.: `180.00`) ou aceita a sugestão automática calculada (ver UC-M2-14).
3. Salva a alteração.
4. O sistema valida a precisão e o valor e persiste o preço informado.
5. Em nova consulta após recarga de dados, o valor persistido é exibido fielmente.

**Alternativas:**
* **Preço zero:** o usuário informa `0.00` para registrar cortesia ou brinde promocional; o sistema aceita e persiste o valor como preço definido, diferenciando-o de preço ausente.
* **Preço negativo:** o usuário tenta informar valor menor que zero; o sistema bloqueia o salvamento e exibe erro de validação.
* **Mais de duas casas decimais:** o usuário tenta informar valor com mais de duas casas decimais (ex.: `180.555`); o sistema rejeita a operação exigindo exatamente até duas casas decimais, sem arredondar ou truncar silenciosamente.
* **Manter sem preço:** o usuário opta por não informar o preço; o sistema salva o registro com preço ausente (`null`), sem atribuir preços fictícios ou estimados.
* **Cestas existentes/legadas:** registros criados antes da implementação do preço continuam com preço ausente após a migration, sem preenchimento automático.

**Regras aplicáveis:**
* O preço da cesta-modelo é persistido com precisão de duas casas decimais;
* O operador possui total autonomia para digitar um preço próprio ou aceitar a sugestão automática calculada pelo sistema;
* Preços de venda já salvos **não são sobrescritos automaticamente** diante de mudanças posteriores nos custos de aquisição;
* Ausência de preço (`null`) é diferente de preço zero (`0.00`);
* Cestas-modelo sem preço não podem ser adicionadas a uma venda no M4;
* Ao adicionar a cesta a uma venda em M4, o preço vigente é copiado como snapshot histórico e não é alterado caso o preço da cesta-modelo mude posteriormente no M2.

**Resultado esperado:** O preço de venda fica persistido com duas casas decimais na cesta-modelo, pronto para servir de snapshot de preço em M4.

## UC-M2-13 — Registrar custo de aquisição na entrada de estoque

**Objetivo:** Registrar o custo unitário de compra ao dar entrada de produtos no estoque.

**Pré-condições:** Produto cadastrado e ativo em M1.

**Fluxo principal:**
1. O usuário acessa a funcionalidade de movimentação de estoque.
2. Seleciona o tipo de movimentação `ENTRY` (entrada).
3. Informa a quantidade movimentada e opcionalmente o custo unitário de aquisição (`unit_cost`) com precisão de até duas casas decimais.
4. Confirma a movimentação.
5. O sistema registra a movimentação de estoque com o custo informado.

**Alternativas:**
* **Custo não informado:** o usuário deixa o campo de custo vazio; o sistema grava a entrada com custo `null`. Entradas com custo nulo são ignoradas no cálculo do custo médio ponderado (não são tratadas como zero).
* **Custo negativo:** o usuário tenta informar custo menor que zero; o sistema rejeita a operação com erro de validação.

**Regras aplicáveis:**
* Custo unitário aplica-se exclusivamente a movimentações de entrada (`ENTRY`);
* Valores negativos são rejeitados;
* Custos ausentes não são tratados como zero.

**Resultado esperado:** A movimentação de entrada é gravada no histórico de estoque com seu respectivo custo unitário de aquisição.

## UC-M2-14 — Obter sugestão de preço (2 × custo de referência) e aceitar ou personalizar

**Objetivo:** Auxiliar o operador apresentando o custo de referência da composição e uma sugestão de preço de venda calculada como 2 × custo de referência, preservando a autonomia de precificação.

**Pré-condições:** A composição possui um ou mais itens e todos os itens possuem `reference_price` definido.

**Fluxo principal:**
1. Ao abrir ou editar uma cesta ou template, o sistema calcula o custo de referência da cesta (somatório de `quantidade × reference_price` de cada item).
2. O sistema calcula a sugestão de preço igual a **2 × custo de referência**.
3. A interface apresenta o custo de referência, a sugestão de preço e um botão para "Usar sugestão".
4. O operador clica em "Usar sugestão" (o valor sugerido é preenchido no campo de preço) ou digita um preço próprio.
5. O operador salva a cesta-modelo.
6. O sistema persiste o preço escolhido.

**Alternativas:**
* O operador já havia salvo um preço anteriormente: o sistema exibe a sugestão calculada, mas **não altera nem sobrescreve** o preço já salvo no formulário ou no banco.
* O operador edita a composição (alterando produtos ou quantidades): o custo de referência e o preço sugerido são recalculados dinamicamente, mantendo o preço salvo inalterado até ação explícita do operador.

**Regras aplicáveis:**
* A sugestão é meramente um auxílio operacional (2 × custo de referência);
* O operador tem plena autonomia para aceitar a sugestão ou definir outro valor;
* Preços já salvos nunca são sobrescritos automaticamente por mudanças no preço de referência.

**Resultado esperado:** Custo de referência e preço sugerido são exibidos dinamicamente, e o preço escolhido pelo operador é persistido.

## UC-M2-15 — Indisponibilidade de sugestão de preço por `reference_price` ausente

**Objetivo:** Informar claramente ao operador quando o cálculo de custo de referência e de preço sugerido não for possível ou confiável.

**Pré-condições:** A composição está vazia ou pelo menos um dos produtos componentes não possui `reference_price` definido.

**Fluxo principal:**
1. O usuário consulta ou edita a cesta/template.
2. O sistema identifica que ao menos um produto da composição não possui `reference_price` definido (ou que a composição não tem itens).
3. O sistema sinaliza que o custo de referência é indisponível.
4. A interface exibe aviso informativo indicando que não há preço de referência definido para todos os itens.
5. A sugestão de preço não é apresentada como confiável e o botão de usar sugestão fica desabilitado/indisponível.
6. O operador pode definir manualmente o preço de venda desejado e salvar a cesta-modelo.

**Regras aplicáveis:**
* `reference_price` ausente não é tratado como zero;
* Sugestão incompleta nunca é apresentada como valor confiável;
* A ausência de sugestão não impede a composição da cesta nem a definição manual de preço de venda.

**Resultado esperado:** O operador é devidamente informado da indisponibilidade de preço de referência confiável sem ter seu fluxo de precificação manual bloqueado.
