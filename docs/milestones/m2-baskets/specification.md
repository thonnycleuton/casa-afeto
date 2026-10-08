# M2 — Especificação de Cestas e Templates de Cesta

**Versão do documento:** 0.1  
**Status:** COMPLETED  
**Implementation Gate:** READY FOR IMPLEMENTATION  
**Implementation:** Concluída  
**Validation/Review:** VALIDATED  
**Aprovação humana:** Concluída  
**Marco:** M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)  
**Fase:** 1 — Operações Centrais (Core Operations)

---

## 1. Objetivo

M2 permite cadastrar templates reutilizáveis e manter cestas concretas como composições persistidas de produtos. O marco prepara composições para uso futuro, sem implementar o domínio de vendas nem alterar produtos ou estoque do M1.

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
* consultar disponibilidade de estoque apenas para exibir aviso.

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

### 4.1 Template de Cesta

Um template é uma composição reutilizável, identificada e nomeada, com estado ativo/inativo. Um template novo nasce ativo por padrão; não existe estado DRAFT em M2.

Dados de negócio:

* identificador do template;
* nome;
* estado ativo/inativo;
* composição de produtos e quantidades.

Cada item da composição contém `product_id` e `quantity`. Um template pode ser salvo e editado sem itens. Um template vazio permanece ativo, mas não pode ser usado para criar uma cesta até possuir ao menos um item. A forma persistida exata e os metadados técnicos pertencem à implementação e não ampliam o modelo de negócio.

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

Não fazem parte da cesta M2: cliente, venda, destinatário, endereço ou data de entrega, pagamento, preço, custo, estado comercial, reserva ou dedução de estoque.

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

Custo de produto, custo de cesta, custo médio, custo por lote, preço sugerido, preço final, margem, markup e cálculo de preço estão fora do M2. M1 não possui fonte formal de custo. A ideia antiga de preço em torno de duas vezes o custo não é regra de negócio vigente. Fonte de custo e regras de precificação serão especificadas em marco futuro.

## 10. Consultas e operações

As operações previstas são:

| Entidade | Operações M2 |
|---|---|
| Template | Criar, listar/consultar, visualizar, editar, ativar/desativar |
| Cesta | Criar com/sem template, listar/consultar, visualizar, editar composição, adicionar/remover/substituir produto e alterar quantidade |

Não se presume operação de exclusão, arquivamento ou duplicação.

## 11. Relação com vendas futuras

M2 não cria entidade Sale/Venda nem relacionamento estrutural entre cesta e venda. Não adiciona `sale_id`, cliente, pagamento, entrega ou estado de venda.

O M4 definirá como uma venda utiliza uma cesta e se a composição é copiada/congelada naquele contexto. M2 não antecipa essa decisão.

## 12. Fora do escopo

Além dos itens explicitamente excluídos acima, estão fora do M2:

* clientes e vendas;
* pagamentos, destinatários e entregas;
* compras e fornecedores;
* lotes, validade, FEFO e reposição;
* reserva e dedução de estoque;
* comunicação, notificações e dashboards;
* custo e precificação.

## 13. Regras relacionadas

Consultar `docs/domain/business-contract.md`, regras `BASKET-001` a `BASKET-012`, e `docs/milestones/m1-products-inventory/specification.md` para Produto, unidade base, atividade e disponibilidade.

## 14. Estado das decisões

As quatro decisões anteriormente pendentes foram fechadas pelo Product Owner e estão incorporadas nesta especificação. Não há Open Questions de negócio registradas para M2.
