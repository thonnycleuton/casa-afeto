# M2 — Plano de Validação

**Versão do documento:** 0.1  
**Status:** COMPLETED  
**Implementation Gate:** READY FOR IMPLEMENTATION  
**Implementation:** Concluída  
**Validation/Review:** VALIDATED  
**Aprovação humana:** Concluída  
**Marco:** M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)

Este plano foi aplicado após a implementação e antes da aceitação humana. A Validation/Review resultou em `VALIDATED` e a aprovação humana foi concluída. Os casos validaram comportamento visível e persistido, além de confirmar que M1 e os limites do M2 permanecem intactos.

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

* Criar e consultar template, estado e composição após recarregar a aplicação.
* Criar e consultar template sem itens; confirmar que seu estado inicial é ativo e que o template não pode originar cesta enquanto vazio.
* Criar cesta com e sem template; verificar persistência de nome, origem opcional e composição.
* Alterar uma entidade e confirmar que a outra não é modificada.
* Salvar e consultar uma cesta vazia.
* Confirmar que os dados de domínio não incluem `sale_id`, `customer_id`, destinatário, entrega, pagamento, custo, preço, estado comercial, reserva ou dedução de estoque.
* Confirmar que referências de produto mantêm `product_id` após renomeação e desativação.

## 6. Validação de API

* Exercitar cada operação aprovada de criação, listagem/consulta, visualização, edição e ativação/desativação de template.
* Exercitar cada operação aprovada de criação com/sem template, listagem/consulta, visualização e edição de cesta/composição.
* Verificar rejeição apropriada de inclusão de produto inativo e de uso de template inativo ou com produto inativo.
* Verificar respostas para estoque insuficiente: aviso observável, operação permitida e nenhum efeito no estoque.
* Verificar validação de unidade e quantidade com os casos aprovados no domínio.
* Verificar incremento de quantidade ao incluir produto já existente e agregação de quantidades em substituição por produto já presente.
* Confirmar que não foram criadas operações de venda, preço/custo, exclusão, arquivamento ou duplicação sem decisão de escopo.

## 7. Validação de frontend

* Verificar listagem, visualização e edição de templates e cestas.
* Verificar seleção somente de produtos ativos para novas inclusões.
* Verificar identificação acessível e clara de produto inativo em composição existente, sem bloquear a edição de outros itens.
* Verificar que template inativo não pode ser escolhido para nova cesta e que template com produto inativo apresenta motivo e caminho de correção explícita.
* Verificar aviso de estoque insuficiente sem bloquear salvamento.
* Verificar criação e salvamento de cesta vazia.
* Confirmar ausência de campos e ações de venda, cliente, entrega, pagamento, custo/preço, reserva e dedução de estoque.
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
* ausência de custo, preço e dados de venda.

## 9. Cenários negativos

* Incluir produto inativo em nova composição.
* Usar template inativo para criar cesta.
* Usar template com produto inativo para criar cesta.
* Modificar unidade base de produto que possua movimentações de estoque, respeitando a rejeição de M1.
* Enviar unidade não suportada por M1 ou quantidade incompatível com unidade.
* Confirmar que indisponibilidade/estoque insuficiente não produz bloqueio de composição nem movimentação.
* Confirmar que não há comportamentos bloqueados por questões de negócio abertas no M2.

## 10. Revisão final e aceitação

1. Executar critérios de aceitação aplicáveis e registrar resultados.
2. Confirmar ausência de diferenças inesperadas em saldos e histórico do estoque.
3. Confirmar que nenhum fluxo de vendas foi antecipado.
4. Realizar validação humana das operações e mensagens visíveis.
5. Registrar e resolver defeitos antes de declarar M2 validado.
