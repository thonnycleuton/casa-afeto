# M2 — Especificação de Cestas e Templates de Cesta

**Versão do documento:** 0.3
**Status geral:** Concluído (COMPLETED)
**Histórico da conclusão original de M2:** Concluída e aprovada (COMPLETED / VALIDATED / Aprovação humana concluída em 2026-10-06)
**Status da correção pontual:** Concluída e aprovada (COMPLETED)
**Validação da correção pontual:** Validada (testes automatizados e aceitação humana concluídos)
**Fechamento da reabertura:** Concluído (implementação, testes automatizados e aprovação humana concluídos)
**Marco:** M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)
**Fase:** 1 — Operações Centrais (Core Operations)

---

## 1. Objetivo

M2 permite cadastrar templates reutilizáveis e manter cestas concretas como composições persistidas de produtos. O marco prepara composições para uso futuro, sem implementar o domínio de vendas nem alterar regras de produtos ou integridade física de estoque do M1.

Como correções pontuais aprovadas em M2 antes de M4:
* Permite registrar o custo unitário de aquisição nas entradas de estoque (`ENTRY`).
* Calcula o custo médio ponderado do produto considerando as entradas com custo conhecido, sem tratar custos desconhecidos como zero.
* Calcula o custo estimado da cesta somando o custo médio ponderado dos produtos multiplicado pelas respectivas quantidades.
* Fornece sugestão de preço de venda igual a **2 × custo estimado da cesta**.
* Assegura total autonomia ao operador, permitindo aceitar a sugestão ou informar outro preço manualmente.
* Garante que alterações nos custos não sobrescrevem automaticamente preços de venda já definidos.
* Disponibiliza a persistência do preço de venda na cesta-modelo usada como origem comercial em vendas.
* Quando não houver dados suficientes de custo para algum item ou a composição estiver vazia, a sugestão de preço permanece indisponível.

Esta especificação registra o comportamento aprovado para M2. As decisões formalizadas pelo Product Owner prevalecem sobre descrições antigas em outros documentos.

## 2. Escopo

M2 inclui:

* criar, listar, consultar, visualizar, editar, ativar e desativar templates;
* compor templates com produtos e quantidades;
* criar, listar, consultar, visualizar e editar cestas concretas;
* criar cesta com ou sem template;
* copiar a composição do template no momento da criação;
* adicionar, remover e substituir produtos, e alterar quantidades;
* salvar uma cesta sem itens;
* identificar produtos inativos presentes em composições;
* consultar disponibilidade de estoque apenas para exibir aviso;
* definir e persistir manualmente o preço de venda da cesta-modelo;
* registrar custo unitário de aquisição opcional em entradas de estoque (`ENTRY`);
* calcular o custo médio ponderado de produtos com entradas de custo conhecido;
* calcular o custo estimado da composição da cesta;
* calcular e apresentar sugestão de preço de venda igual a duas vezes o custo estimado;
* aceitar a sugestão de preço ou definir outro preço com preservação de valores salvos;
* apresentar a sugestão como indisponível quando houver dados insuficientes de custo.

Exclusão, arquivamento e duplicação de templates ou cestas não são operações definidas para M2.

## 3. Dependências de M1

M2 reutiliza Produto e as informações de unidade, estado ativo/inativo e disponibilidade fornecidas por M1. M2 não altera regras ou dados de M1.

* As composições identificam produtos por `product_id`, não pelo nome.
* Produtos ativos podem ser incluídos em novas composições.
* A quantidade é expressa na unidade base atual do produto. `UN` admite quantidade inteira; `KG`, `G`, `L` e `ML` admitem quantidade decimal, conforme os valores de unidade definidos em M1.
* Referenciar produto em cesta ou template não constitui movimentação de estoque e não impede uma mudança de unidade base que M1 permita.
* M2 não converte unidades nem mantém histórico de unidades.
* Disponibilidade de estoque é consultada conforme M1 e é apenas informativa. Pode mudar após a consulta.

## 4. Entidades e dados

### 4.1 Template de Cesta (Cesta-Modelo)

Um template é uma composição reutilizável, identificada e nomeada, com estado ativo/inativo e preço de venda opcional. Um template novo nasce ativo por padrão; não existe estado DRAFT em M2.

Campos mínimos:

| Campo | Significado | Restrições |
|---|---|---|
| `id` | Identificador do template | Chave primária |
| `name` | Nome do template | Texto obrigatório |
| `active` | Estado ativo/inativo | Booleano, padrão `true` |
| `price` | Preço de venda da cesta-modelo | Definição manual, persistido, precisão de duas casas decimais, anulável (opcional no cadastro), aceita zero (`0.00`), rejeita valores negativos e rejeita precisão superior a duas casas decimais |
| `created_at` | Data/hora de criação | Preenchido automaticamente |
| `updated_at` | Data/hora da última atualização | Preenchido automaticamente |

Cada item da composição contém:

| Campo | Significado | Restrições |
|---|---|---|
| `template_id` | Identificador do template ao qual o item pertence | Chave estrangeira, cascata na exclusão |
| `product_id` | Identidade do produto em M1 | Chave estrangeira, restrição de integridade |
| `quantity` | Quantidade na unidade base atual do produto | Maior que zero, respeitando regras de unidade de M1 |

Regras de diferenciação do preço de venda:

* **Preço ausente (`null` ou não informado):** a cesta-modelo pode ser cadastrada, consultada e editada no M2, mas não pode ser adicionada a uma venda até que o preço seja definido manualmente.
* **Preço zero (`0.00`):** valor explicitamente atribuído para brindes, cortesias e itens promocionais. É um preço válido e definido, categoricamente diferente de preço ausente.
* **Preço positivo (`> 0.00`):** valor monetário normal com precisão de duas casas decimais.
* **Rejeição de negativos:** valores monetários menores que zero são estritamente inválidos e devem ser rejeitados pela validação.
* **Validação de precisão decimal:** o campo exige precisão de exatamente duas casas decimais. Entradas com mais de duas casas decimais devem ser rejeitadas pela validação, sem aplicação arbitrária de arredondamento ou truncamento automático.

Compatibilidade com dados existentes e futura migration Alembic:

* A tabela física atual de cestas-modelo (`basket_templates`) não possui coluna de preço.
* A futura etapa técnica de implementação precisará criar uma migration Alembic para adicionar um campo monetário anulável (nullable) na tabela de templates de cesta, preservando integralmente os registros existentes.
* Registros existentes não receberão preços fictícios, estimados ou calculados automaticamente.
* Registros existentes sem preço continuarão sem preço após a migration, exigindo definição manual de preço caso venham a ser selecionados para vendas em M4.
* O preço zero jamais será atribuído automaticamente ou utilizado como fallback para registros sem preço.
* A migration não é criada nem executada nesta tarefa de alinhamento documental.
* Não se impõe tipo SQL rígido nesta especificação documental além da exigência de precisão monetária de duas casas decimais, cabendo à etapa técnica a escolha conforme os padrões arquiteturais do backend (como `Numeric(asdecimal=True)`).

Um template pode ser salvo e editado sem itens. Um template vazio permanece ativo, mas não pode ser usado para criar uma cesta até possuir ao menos um item. A forma persistida exata e os metadados técnicos pertencem à implementação e não ampliam o modelo de negócio.

### 4.2 Cesta concreta

Uma cesta concreta é uma entidade persistida que representa uma composição específica. Seu ciclo de vida no M2 é criar, editar, salvar e continuar editando.

Campos mínimos:

| Campo | Significado |
|---|---|
| `id` | Identificador da cesta |
| `name` | Nome da cesta |
| `template_id` | Opcional; identifica somente o template que originou a cesta |
| `created_at` | Data/hora de criação |
| `updated_at` | Data/hora da última atualização |

Cada item da composição contém:

| Campo | Significado |
|---|---|
| `basket_id` | Cesta à qual o item pertence |
| `product_id` | Identidade do produto |
| `quantity` | Quantidade na unidade base atual do produto |

Não fazem parte da cesta M2: cliente, venda, destinatário, endereço ou data de entrega, pagamento, custo, estado comercial, reserva ou dedução de estoque.

O preço de venda é atributo da cesta-modelo (template), servindo de origem comercial para integração com M4. A cesta concreta do M2 não cria vínculo estrutural com Sale/Venda.

### 4.3 Composição e quantidades

Templates e cestas contêm produtos e quantidades. A quantidade deve respeitar a representação da unidade base de M1. A composição não cria movimentação de estoque.

Uma composição pode incluir mais de uma unidade/quantidade do mesmo produto. Cada `product_id` pode aparecer no máximo uma vez em uma composição. Ao incluir produto que já esteja presente, a quantidade solicitada é somada à quantidade existente, sem criar uma segunda linha. Ao substituir um item por um produto já presente na composição, as quantidades são somadas e a composição resultante mantém uma única linha para esse produto.

Cada quantidade de item deve ser maior que zero; zero não representa item na composição. Aplicam-se as regras de unidade de M1 para valores inteiros ou decimais.

## 5. Regras de Template

1. Um template novo nasce ativo por padrão; M2 não possui estado DRAFT.
2. Um template pode ser criado, consultado, editado, ativado e desativado.
3. Um template vazio pode ser salvo e editado posteriormente, mas não pode originar uma cesta nova enquanto não possuir itens.
4. Um template inativo continua persistido, consultável, editável e pode ser reativado.
5. Um template inativo não pode ser usado para criar uma cesta nova.
6. Um template com produto inativo não pode ser usado para criar uma cesta nova.
7. Desativar um produto já presente no template não remove nem altera sua referência ou quantidade.
8. A composição de template existente que contém produto inativo permanece editável; o usuário pode manter o item, alterar sua quantidade ou removê-lo.
9. A correção de um produto inativo no template é explícita. Não há remoção ou substituição automática.
10. A inclusão de produto em template exige que o produto esteja ativo; se já existir na composição, sua quantidade é incrementada.
11. Um produto aparece no máximo uma vez em cada composição; substituição por produto já presente agrega as quantidades em uma única linha.

## 6. Regras de Cesta

1. Uma cesta pode ser criada a partir de um template ativo cuja composição contenha somente produtos ativos.
2. Ao criar uma cesta com template, os itens e quantidades são copiados naquele momento. O `template_id` registra a origem, não uma composição viva.
3. Alterações posteriores no template não afetam a cesta criada; alterações na cesta não afetam o template.
4. Uma cesta pode ser criada sem template.
5. Uma cesta sem itens é válida e pode ser criada e salva. Também pode ser esvaziada e salva novamente.
6. Uma cesta existente continua editável; não há estados comerciais no M2.
7. Produtos inativos que já estejam na cesta permanecem nela e não são removidos ou substituídos automaticamente. O usuário pode mantê-los, alterar sua quantidade ou removê-los e pode editar outros itens.
8. Produto inativo não pode ser incluído como novo item. Uma substituição só ocorre por ação explícita do usuário e selecionando outro produto ativo.
9. A interface deve identificar claramente os produtos inativos que já estejam em uma composição.
10. A inclusão de produto que já esteja na cesta incrementa a quantidade existente; cada produto aparece uma única vez.

## 7. Identidade do produto e unidade base

Renomear um produto não cria nova identidade. Templates e cestas continuam referenciando o mesmo `product_id`, sem duplicação de referências, alteração de quantidades ou histórico de nomes no M2. A interface pode apresentar o nome atual.

A referência em uma composição não é movimentação de estoque. Uma mudança de unidade base permitida pelas regras de M1 continua permitida. Quantidades da composição são interpretadas na unidade base atual; M2 não converte quantidades nem mantém histórico de unidades.

## 8. Estoque

Um produto sem estoque suficiente pode ser incluído em uma composição. Quando a disponibilidade consultada for insuficiente para a quantidade da composição, a interface apresenta um aviso, sem bloquear a seleção ou o salvamento.

A disponibilidade exibida é informativa e pode mudar. M2 não:

* reserva estoque;
* deduz estoque;
* cria, edita ou exclui movimentações;
* altera quantidade disponível;
* confirma vendas.

Não é introduzida nova regra de concorrência nem novo ADR. O ADR-001 permanece aplicável às operações futuras que efetivamente alterem estoque.

## 9. Custo e preço

Decisões de negócio aprovadas para a correção de M2:

1. **Custo unitário de aquisição na entrada de estoque:** nas movimentações de estoque do tipo entrada (`ENTRY`), pode ser registrado o custo unitário de aquisição do produto (`unit_cost`) com precisão de duas casas decimais. O campo é opcional, anulável (`nullable`) e rejeita valores negativos.
2. **Custo médio ponderado do produto:** o custo médio unitário é calculado considerando as quantidades e custos das entradas de estoque com custo conhecido. Entradas sem custo registrado são ignoradas no cálculo da média e não são tratadas como zero. Produtos sem entradas com custo conhecido permanecem sem custo médio confiável.
3. **Custo estimado da cesta:** obtido pela soma do custo médio ponderado de cada produto multiplicado pela sua quantidade na composição. Se algum item da composição não possuir custo de aquisição conhecido, o custo estimado da cesta é considerado indisponível / não confiável (`has_reliable_cost = false`).
4. **Preço sugerido:** calculado automaticamente como **2 × custo estimado da cesta** quando todos os itens possuem custo de aquisição conhecido e a composição não está vazia. Se houver dados insuficientes de custo ou a composição estiver vazia, o preço sugerido permanece indisponível e nunca é apresentado como confiável.
5. **Autonomia do operador e aceitação da sugestão:** a sugestão é exibida como auxílio operacional. O operador tem total autonomia para aceitar a sugestão com um clique ou informar manualmente outro preço de venda.
6. **Não sobrescrita de preços salvos:** alterações posteriores nos custos de aquisição ou nas entradas de estoque **não sobrescrevem** automaticamente preços de venda já definidos e persistidos.
7. **Recálculo sob demanda:** ao editar a composição da cesta ou solicitar nova sugestão, o sistema recalcula dinamicamente o custo estimado e a sugestão atualizada, sem substituir automaticamente o preço de venda já fixado.
8. **Definição manual e persistência de preço na cesta-modelo:** o preço de venda da cesta-modelo é persistido no banco de dados com precisão de exatamente duas casas decimais. Valores com mais de duas casas decimais ou valores negativos são estritamente rejeitados na validação (sem arredondamento ou truncamento automático).
9. **Preço zero:** o preço zero (`0.00`) é permitido para representar brindes, cortesias e itens promocionais, sendo categoricamente distinto de ausência de preço (`null`).
10. **Snapshot histórico em vendas (M4):** ao adicionar uma cesta-modelo a uma venda (em M4), o preço vigente é copiado como snapshot histórico imutável. Alterações futuras no preço da cesta-modelo não alteram vendas preexistentes.
11. **Preservação de registros preexistentes:** registros de movimentações e composições criados antes da implementação não recebem custos ou preços retroativos fictícios.

## 10. Consultas e operações

As operações previstas são:

| Entidade | Operações M2 |
|---|---|
| Template | Criar (com preço opcional), listar/consultar, visualizar, editar (inclusive preço), ativar/desativar |
| Cesta | Criar com/sem template, listar/consultar, visualizar, editar composição, adicionar/remover/substituir produto e alterar quantidade |

Não se presume operação de exclusão, arquivamento ou duplicação.

## 11. Relação com vendas futuras

M2 não cria entidade Sale/Venda nem relacionamento estrutural entre cesta e venda. Não adiciona `sale_id`, cliente, pagamento, entrega ou estado de venda.

O M4 definirá como uma venda utiliza uma cesta e se a composição é copiada/congelada naquele contexto.

Para suportar o comportamento aprovado de M4:
* M2 disponibiliza preço de venda persistido na cesta-modelo.
* Se a cesta-modelo estiver sem preço definido, M4 bloqueará a sua adição à venda.
* Ao adicionar à venda, M4 copia o preço como snapshot histórico imutável, desacoplando-o de eventuais alterações futuras no template do M2.

## 12. Fora do escopo

Além dos itens explicitamente excluídos acima, estão fora do M2:

* clientes e vendas;
* pagamentos, destinatários e entregas;
* compras e fornecedores;
* lotes, validade, FEFO e reposição;
* reserva e dedução de estoque;
* comunicação, notificações e dashboards;
* regras de margem ou markup além da regra aprovada de sugestão (2 × custo estimado).

## 13. Regras relacionadas

Consultar `docs/domain/business-contract.md`, regras `BASKET-001` a `BASKET-019` e Seção 19, e `docs/milestones/m1-products-inventory/specification.md` para Produto, unidade base, atividade e disponibilidade.

## 14. Estado das decisões e governança

As decisões de negócio sobre templates, composições, persistência de preços de venda, registro de custos de aquisição em entradas de estoque e cálculo de preço sugerido (2 × custo) estão formalizadas e aprovadas pelo Product Owner.

Governança do marco:
* Conclusão original de M2: mantida no histórico (aprovada em 2026-10-06).
* Reabertura pontual: Custos de aquisição nas entradas de estoque e sugestão de preço das cestas.
* Estado da implementação: Concluída (migration técnica aplicada, modelos SQLAlchemy, schemas Pydantic, serviços FastAPI, componentes Vue e testes de regressão aprovados).
* Validação e Aceitação Humana: Aprovadas formalmente pelo Product Owner. Reabertura encerrada e marco M2 concluído (COMPLETED).
