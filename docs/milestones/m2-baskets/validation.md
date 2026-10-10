# M2 — Plano de Validação

**Versão do documento:** 0.4
**Status geral:** Concluído (COMPLETED)
**Histórico da conclusão original de M2:** Concluída e aprovada (COMPLETED / VALIDATED / Aprovação humana concluída em 2026-10-06)
**Status da correção pontual:** Implementada, validada e formalmente aprovada
**Validação da correção pontual:** Executada e aprovada (55 testes de backend aprovados, sendo 9 testes dedicados de custo e precificação e 17 de templates/cestas; 18 testes de frontend aprovados; validação humana concluída e aprovada pelo Product Owner)
**Fechamento da reabertura:** Concluído (COMPLETED / Aceitação humana formalizada)
**Marco:** M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)

Este documento foi originalmente aplicado após a implementação do núcleo de cestas e resultou em `VALIDATED` com aprovação humana concluída em 2026-10-06. O plano foi posteriormente reaberto de forma pontual para a introdução do preço de venda persistido da cesta-modelo e, em seguida, para o registro de custo de aquisição em entradas de estoque, cálculo do custo médio ponderado e custo estimado da composição, e cálculo de sugestão de preço (2 × custo) com preservação de preços salvos e autonomia do operador. Ambas as correções foram integralmente implementadas no backend e frontend, validadas por suítes de testes automatizados e aceitas pelo Product Owner.

---

## 1. Preparação

1. Usar ambiente de validação e dados de teste identificáveis.
2. Preparar produtos M1 ativos de unidade `UN` e de unidade decimal, com estoque suficiente e insuficiente.
3. Preparar um produto ativo que possa ser desativado durante o cenário e outro que possua movimentação, para validar as regras de unidade de M1 sem alterá-las.
4. Confirmar estado inicial dos dados e saldos de estoque.
5. Não usar dados de clientes, vendas, pagamentos, compras ou lotes; esses domínios não fazem parte do M2.

## 2. Validação de domínio

* Criar e editar template com produtos ativos e quantidades; consultar estado e composição.
* Desativar e reativar template; confirmar que inativo não pode originar cesta e continua consultável/editável.
* Criar template vazio; confirmar que nasce ativo, pode ser salvo/editado e não pode originar cesta até possuir um item.
* Verificar que um template contendo produto posteriormente inativo não pode originar cesta até que o usuário corrija explicitamente a composição.
* Criar cesta com template e confirmar cópia dos itens e quantidades naquele instante.
* Alterar template após a criação e verificar que a cesta não muda; alterar cesta e verificar que template não muda.
* Criar cesta sem template e salvar vazia; remover todos os itens de cesta existente e salvá-la vazia.
* Adicionar, remover, substituir explicitamente e alterar quantidades; consultar a composição salva.
* Desativar produto presente em template/cesta; verificar preservação da referência, indicação clara de inatividade, possibilidade de manter/alterar quantidade/remover item e edição de outros itens.
* Tentar inclusão nova de produto inativo e verificar que é impedida; verificar que eventual substituição é explícita e exige produto ativo.
* Incluir novamente produto já existente em uma composição e confirmar incremento da quantidade sem criação de outra linha; substituir item por produto já existente e confirmar agregação das quantidades.
* Renomear produto em M1 e verificar que a composição continua ligada ao mesmo `product_id`, sem alterar quantidade.
* Alterar unidade base somente quando permitido pelas regras M1 e confirmar que a referência M2 não impede a operação. Confirmar que não há conversão nem histórico de unidade M2.

## 3. Validação de quantidade e unidades

* Verificar unidade controlada e coerência com a unidade base vigente do produto.
* Verificar quantidades inteiras para `UN` e decimais para `KG`, `G`, `L` e `ML`.
* Cobrir quantidade inválida conforme as validações aprovadas para composição.
* Confirmar que cada produto ocorre no máximo uma vez em cada composição, inclusive após inclusão repetida e substituição por produto existente.

## 4. Validação de estoque e integração com M1

* Com produto ativo sem estoque suficiente, adicionar à composição e confirmar aviso claro e salvamento permitido.
* Confirmar que a informação de disponibilidade é apresentada como consulta informativa, não como garantia futura.
* Comparar saldo e histórico de movimentações antes e depois de criar e editar templates/cestas; ambos devem permanecer inalterados.
* Confirmar ausência de reserva, dedução e movimentação de estoque.
* Confirmar que operações futuras que alterem estoque permanecem sob as regras e garantias existentes em M1/ADR-001; M2 não introduz novo mecanismo de concorrência.

## 5. Validação de persistência

* Criar e consultar template, estado, preço e composição após recarregar a aplicação.
* Criar e consultar template sem itens; confirmar que seu estado inicial é ativo e que o template não pode originar cesta enquanto vazio.
* Criar cesta com e sem template; verificar persistência de nome, origem opcional e composição.
* Alterar uma entidade e confirmar que a outra não é modificada.
* Salvar e consultar uma cesta vazia.
* Confirmar que os dados de domínio da cesta concreta não incluem `sale_id`, `customer_id`, destinatário, entrega, pagamento, custo, estado comercial, reserva ou dedução de estoque.
* Confirmar que a cesta-modelo suporta preço de venda persistido opcional com precisão de duas casas decimais, sem cálculo de custo nem vínculos com vendas.
* Confirmar que referências de produto mantêm `product_id` após renomeação e desativação.

## 6. Validação de API

* Exercitar cada operação aprovada de criação, listagem/consulta, visualização, edição e ativação/desativação de template, incluindo o campo de preço de venda opcional.
* Exercitar cada operação aprovada de criação com/sem template, listagem/consulta, visualização e edição de cesta/composição.
* Verificar rejeição apropriada de inclusão de produto inativo e de uso de template inativo ou com produto inativo.
* Verificar respostas para estoque insuficiente: aviso observável, operação permitida e nenhum efeito no estoque.
* Verificar validação de unidade e quantidade com os casos aprovados no domínio.
* Verificar incremento de quantidade ao incluir produto já existente e agregação de quantidades em substituição por produto já presente.
* Confirmar que não foram criadas operações de venda, cálculo automático de custo/preço, exclusão, arquivamento ou duplicação sem decisão de escopo.

## 7. Validação de frontend

* Verificar listagem, visualização e edição de templates e cestas.
* Verificar interface para definição e edição manual do preço de venda na cesta-modelo, com precisão de duas casas decimais.
* Confirmar ausência de campos de cálculo automático de custo ou margem sugerida.
* Verificar seleção somente de produtos ativos para novas inclusões.
* Verificar identificação acessível e clara de produto inativo em composição existente, sem bloquear a edição de outros itens.
* Verificar que template inativo não pode ser escolhido para nova cesta e que template com produto inativo apresenta motivo e caminho de correção explícita.
* Verificar aviso de estoque insuficiente sem bloquear salvamento.
* Verificar criação e salvamento de cesta vazia.
* Confirmar ausência de campos e ações de venda, cliente, entrega, pagamento, reserva e dedução de estoque.
* Aplicar padrões de interface e acessibilidade definidos em `docs/design/design-system.md`.

## 8. Testes automatizados

Executar os testes de domínio, persistência, API e frontend que cubram os critérios de aceitação M2. Incluir regressão de integração com as operações de consulta de Produto e disponibilidade de M1.

Cobertura mínima dos critérios:

* criação com template e sem template;
* cesta vazia;
* cópia e independência entre composições;
* alteração de composição e quantidades;
* estados de produto/template inativos;
* template vazio ativo que não pode originar cesta;
* alteração de quantidade de item inativo existente;
* agregação de produto repetido e unicidade do produto na composição;
* aviso de estoque insuficiente e ausência de mutação de estoque;
* unidade e quantidade;
* suporte ao preço manual persistido na cesta-modelo;
* ausência de custo e ausência de dados de venda no M2.

## 9. Cenários negativos

* Incluir produto inativo em nova composição.
* Usar template inativo para criar cesta.
* Usar template com produto inativo para criar cesta.
* Modificar unidade base de produto que possua movimentações de estoque, respeitando a rejeição de M1.
* Enviar unidade não suportada por M1 ou quantidade incompatível com unidade.
* Confirmar que indisponibilidade/estoque insuficiente não produz bloqueio de composição nem movimentação.
* Confirmar que não há comportamentos bloqueados por questões de negócio abertas no M2.

## 10. Validação da correção pontual de preço de venda da cesta-modelo

Os casos de teste a seguir cobrem a correção pontual de preço de venda e foram **executados e validados** em 2026-10-09:

1. **Criar e persistir cesta-modelo com preço positivo:** cadastrar um novo template com nome, itens e preço positivo com duas casas decimais (ex.: `150.00`), salvando com sucesso.
   * *Status:* **APROVADO** (coberto por `test_template_price_positive_is_persisted_with_two_decimals` e teste de frontend `creates a template with price and displays formatted value`).
2. **Editar preço e consultar novo valor:** alterar o preço de um template existente para outro valor válido com duas casas decimais (ex.: `180.00`), salvar e verificar se a nova consulta reflete o valor atualizado.
   * *Status:* **APROVADO** (coberto por `test_template_price_update_and_persistence` e teste de frontend `edits template price and saves updated payload`).
3. **Definir preço zero como valor explícito:** cadastrar ou editar template com preço `0.00` (cortesia/brinde); verificar que o valor zero é persistido e que o sistema o trata como preço definido, não como preço ausente.
   * *Status:* **APROVADO** (coberto por `test_template_price_zero_is_valid_and_distinct_from_null` e teste de frontend `displays zero price as cortesia badge distinctly from missing price`).
4. **Rejeitar preço negativo:** tentar cadastrar ou editar template com valor negativo (ex.: `-10.00` e `-5.00`); confirmar que a validação rejeita a requisição (HTTP 422) e impede o salvamento.
   * *Status:* **APROVADO** (coberto por `test_template_price_negative_is_rejected`).
5. **Rejeitar preço com mais de duas casas decimais:** tentar cadastrar ou editar template com precisão decimal superior à permitida (ex.: `50.125` e `99.999`); confirmar rejeição pela validação (HTTP 422) sem arredondamento ou truncamento automático.
   * *Status:* **APROVADO** (coberto por `test_template_price_with_more_than_two_decimals_is_rejected`).
6. **Manter cesta-modelo sem preço sem atribuir valor fictício:** criar ou manter template com campo de preço vazio (`null`); verificar persistência como valor ausente, sem preenchimento automático por valor padrão ou fictício.
   * *Status:* **APROVADO** (coberto por `test_template_created_without_price_has_null_price`).
7. **Bloqueio de inclusão em venda quando o preço estiver ausente:** tentar adicionar template com preço ausente a uma venda; confirmar que a inclusão é bloqueada até que o preço seja definido.
   * *Status:* **PLANEJADO PARA M4** (*validação de integração do ciclo comercial de M4 quando as vendas forem implementadas; bloqueio garantido contratualmente no business contract*).
8. **Compatibilidade e ausência de preços fictícios em registros legados:** confirmar que registros preexistentes na tabela de templates permanecem com preço ausente (`null`) após a migration, sem atribuição de preços automáticos.
   * *Status:* **APROVADO** (migration `60b1196c1918_add_price_to_basket_templates` cria coluna `nullable=True` sem default numérico).
9. **Persistência e leitura após recarga:** cadastrar templates com preços válidos (positivo, zero e ausente); recarregar a base/aplicação e confirmar que todos os valores e estados de nulidade permanecem íntegros.
   * *Status:* **APROVADO** (coberto por testes de integração de API/banco e montagem do componente no frontend).
10. **Preservação de preço histórico em venda (snapshot):** alterar o preço de uma cesta-modelo no M2 cujo valor havia sido previamente copiado para uma venda em M4; verificar que o preço registrado no item da venda não sofre qualquer alteração.
    * *Status:* **PLANEJADO PARA M4** (*validação de integração do ciclo comercial de M4 quando o modelo de vendas for implementado*).

## 11. Checklist de implementação técnica da correção pontual

- [x] **Migration Alembic:** criação de migration `60b1196c1918_add_price_to_basket_templates.py` que adiciona coluna `price NUMERIC(10, 2)` anulável na tabela `basket_templates` com check constraint `price >= 0`, preservando integralmente os registros existentes sem valores fictícios.
- [x] **Modelo de persistência:** atualização do modelo SQLAlchemy `BasketTemplate` com campo `price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2, asdecimal=True), nullable=True)` e constraint `ck_basket_templates_price_non_negative`.
- [x] **Schemas e validações:** atualização dos schemas Pydantic (`BasketTemplateCreate`, `BasketTemplateUpdate`, `BasketTemplateRead`) com validação estrita de precisão (duas casas decimais, rejeição de negativos e > 2 casas sem truncamento, aceitação de zero e nulo, e normalização de inteiros e 1 casa decimal).
- [x] **Endpoints e serviços:** adequação dos endpoints em `backend/app/api/v1/baskets.py` e métodos de serviço em `backend/app/baskets/service.py` (`create_template`, `update_template`, `template_read`) para gravação e leitura íntegra do preço.
- [x] **Interface frontend:** inclusão do campo de preço de venda no formulário de criação e de edição, indicação visual em badges de status ("Sem preço cadastrado", "R$ 0,00 (Gratuita / Cortesia)", valor monetário formatado) e coluna de preço na listagem de templates em `TemplatesView.vue`.
- [x] **Testes automatizados de backend:** suíte de 17 testes em `test_m2_baskets.py` cobrindo cenários positivos, negativos, normalização, nulo, zero e isolamento de instâncias (46 testes totais na suíte backend, 100% aprovados).
- [x] **Testes automatizados de frontend:** suíte de 5 testes em `M2Views.spec.ts` cobrindo criação com preço, edição de preço, exibição de preço zero como cortesia e badges (17 testes totais na suíte frontend, 100% aprovados).
- [x] **Validação de compatibilidade:** confirmação de persistência nula e integridade de instâncias preexistentes e novas sem atribuição indevida de valores padrão.
- [x] **Atualização do relatório de validação:** execução dos testes e registro formal dos resultados no encerramento da reabertura técnica.
- [ ] **Testes de integração de snapshot com M4:** reservados para a implementação do marco M4 (Vendas).

## 12. Validação da correção pontual de custos de aquisição e sugestão de preço

Os casos de teste a seguir cobrem a correção pontual de custos e precificação e foram **executados e validados** em 2026-10-10:

1. **Registro opcional de custo na entrada de estoque (`ENTRY`):** registrar movimentação de entrada com custo positivo (ex.: `R$ 10,00`), com custo zero e sem custo (`null`); verificar gravação íntegra do campo `unit_cost`.
   * *Status:* **APROVADO** (coberto por `test_cost_and_pricing.py::test_entry_movement_records_unit_cost` e `test_entry_movement_without_cost_records_null`).
2. **Rejeição de custo negativo em entrada:** tentar registrar entrada com custo menor que zero; verificar bloqueio pela validação e constraint do banco.
   * *Status:* **APROVADO** (coberto por `test_cost_and_pricing.py::test_negative_unit_cost_is_rejected`).
3. **Custo médio ponderado do produto:** calcular custo ponderando entradas com custos conhecidos e quantidades; confirmar que entradas sem custo informado são ignoradas e não tratadas como zero.
   * *Status:* **APROVADO** (coberto por `test_cost_and_pricing.py::test_weighted_average_cost_ignores_unknown_costs`).
4. **Custo estimado da cesta:** calcular somatório dos custos médios ponderados multiplicado pelas quantidades dos itens; verificar exatidão matemática do valor.
   * *Status:* **APROVADO** (coberto por `test_cost_and_pricing.py::test_basket_estimated_cost_calculation`).
5. **Sugestão de preço (2 × custo estimado):** verificar que o sistema calcula a sugestão como duas vezes o custo estimado da composição.
   * *Status:* **APROVADO** (coberto por `test_cost_and_pricing.py::test_suggested_price_is_two_times_estimated_cost`).
6. **Indisponibilidade de sugestão quando houver dados insuficientes:** cesta com produto sem histórico de custo conhecido ou cesta vazia; verificar que `has_reliable_cost` é retornado como `false` e sugestão não é confiável.
   * *Status:* **APROVADO** (coberto por `test_cost_and_pricing.py::test_suggested_price_unavailable_when_product_has_no_cost` e `test_suggested_price_unavailable_for_empty_basket`).
7. **Não sobrescrita de preço já salvo:** cadastrar cesta-modelo com preço de venda; adicionar novas entradas de estoque que alterem os custos médios; verificar que o preço de venda salvo não sofre alteração automática.
   * *Status:* **APROVADO** (coberto por `test_cost_and_pricing.py::test_cost_change_does_not_overwrite_existing_selling_price`).
8. **Recálculo dinâmico sob demanda:** alterar composição da cesta e verificar atualização do custo estimado e do preço sugerido sem substituir o preço de venda previamente salvo.
   * *Status:* **APROVADO** (coberto por `test_cost_and_pricing.py::test_recalculating_suggestion_does_not_overwrite_saved_price`).
9. **Interface frontend para custos e sugestão:** tela de produtos exibe campo de custo na entrada; tela de edição de templates e cestas apresenta custo estimado, badge de confiabilidade, sugestão de preço e botão para aplicar sugestão no campo de preço.
   * *Status:* **APROVADO** (coberto por testes Vitest em `M2Views.spec.ts` e verificação manual em navegador).

## 13. Checklist de implementação técnica de custos e sugestão de preço

- [x] **Migration Alembic:** criação de migration `65e00c126251_add_unit_cost_to_inventory_movements.py` que adiciona coluna `unit_cost NUMERIC(10, 2)` anulável na tabela `inventory_movements` com check constraint `ck_inventory_movements_unit_cost_non_negative`.
- [x] **Modelos e schemas:** atualização de `InventoryMovement` e schemas Pydantic de movimentação (`MovementCreate`, `MovementRead`) e produtos/cestas (`BasketTemplateRead`, `BasketRead`).
- [x] **Serviço de estoque e custos:** implementação do cálculo de custo médio ponderado (`product_average_costs`) em `backend/app/inventory/service.py`, ignorando entradas sem custo e não tratando-as como zero.
- [x] **Serviço de cestas e precificação:** cálculo de `estimated_cost`, `suggested_price` (2 × custo) e flag `has_reliable_cost` em `backend/app/baskets/service.py`.
- [x] **Componentes frontend:** inclusão do campo de custo de aquisição em movimentação de estoque, apresentação do custo estimado e preço sugerido em `CompositionEditor.vue`, `TemplatesView.vue` e `BasketsView.vue`, com botão de aceitar sugestão e garantia de tamanho do componente < 250 linhas.
- [x] **Testes automatizados completos:** 55 testes backend (pytest) e 18 testes frontend (Vitest) 100% aprovados sem quebras de regressão.

## 14. Revisão final e aceitação

1. [x] Executar critérios de aceitação aplicáveis e registrar resultados: todos os critérios AC-M2-001 a AC-M2-036 atendidos.
2. [x] Confirmar ausência de diferenças inesperadas em saldos e histórico do estoque: garantido por constraints e testes.
3. [x] Confirmar que nenhum fluxo de vendas foi antecipado indevidamente no M2: estrutura de vendas preservada exclusivamente para M4.
4. [x] Realizar validação humana das operações e mensagens visíveis após a implementação da correção: validada e aprovada pelo Product Owner.
5. [x] Declarar a reabertura de M2 formalmente encerrada e o marco M2 integralmente concluído (COMPLETED).
