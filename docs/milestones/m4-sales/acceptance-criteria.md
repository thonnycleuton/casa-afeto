# M4 — Critérios de Aceitação

**Versão do documento:** 0.2
**Status:** DRAFT — formalização documental para revisão do Product Owner (implementação não iniciada; condicionada ao fechamento da correção de M2 e decisões pendentes de negócio)
**Marco:** M4 — Vendas (Sales)

Os critérios abaixo descrevem resultados observáveis e testáveis para as decisões aprovadas do M4.

---

## Estrutura da venda e composição das cestas

### AC-M4-001 — Várias cestas por venda

**Dado** que o usuário crie uma venda,
**quando** adicionar mais de uma cesta, inclusive várias baseadas na mesma origem,
**então** a venda aceita várias cestas na mesma operação comercial.

### AC-M4-002 — Dados independentes por cesta

**Dado** uma venda com múltiplas cestas,
**quando** o usuário consultar ou editar os dados operacionais de cada cesta,
**então** cada cesta possui composição, destinatário, endereço, data de entrega e horário de entrega independentes.

### AC-M4-003 — Cópia independente da composição

**Dado** que uma cesta seja adicionada à venda a partir de uma origem existente,
**quando** a adição for concluída,
**então** a composição da origem é copiada naquele momento e passa a ser independente da origem.

### AC-M4-004 — Cópia do preço vigente

**Dado** que uma cesta seja adicionada à venda,
**quando** a operação for concluída,
**então** o preço vigente da origem é copiado para a cesta da venda no instante da adição.

### AC-M4-004a — Bloqueio de inclusão sem preço na origem

**Dado** uma cesta-origem sem preço de venda definido,
**quando** o usuário tentar adicioná-la à venda,
**então** a inclusão é bloqueada até que o preço seja informado na origem.

### AC-M4-004b — Snapshot histórico do preço copiado

**Dado** uma cesta já adicionada à venda com preço copiado,
**quando** o preço da cesta-origem for alterado posteriormente no M2,
**então** o preço já registrado no item da venda permanece inalterado.

### AC-M4-005 — Total da venda

**Dado** uma venda com uma ou mais cestas,
**quando** os preços registrados das cestas forem considerados,
**então** o total da venda corresponde à soma desses preços;
**e**, quando um preço registrado mudar em `RASCUNHO`, o total é recalculado.

### AC-M4-006 — Composição não recalcula preço

**Dado** uma cesta da venda com preço acordado registrado,
**quando** sua composição for alterada,
**então** o preço acordado não é recalculado automaticamente.

## Cliente e `RASCUNHO`

### AC-M4-007 — Nova venda exige cliente ativo

**Dado** um cliente inativo,
**quando** o usuário tentar salvar uma nova venda vinculada a ele,
**então** a operação é bloqueada;
**e** apenas clientes ativos podem originar novas vendas.

### AC-M4-008 — `RASCUNHO` aceita dados de entrega incompletos

**Dado** uma venda em `RASCUNHO`,
**quando** uma ou mais cestas ainda não tiverem destinatário, endereço, data ou horário completos,
**então** a venda ainda pode ser salva nesse estado.

### AC-M4-009 — Dados obrigatórios para confirmação financeira

**Dado** uma venda em `RASCUNHO`,
**quando** o fluxo financeiro de confirmação for acionado em M5,
**então** todas as cestas precisam ter destinatário, endereço, data e horário de entrega preenchidos para que a transição para `CONFIRMADA` possa ser autorizada.

### AC-M4-010 — Vínculo preservado após inativação do cliente

**Dado** uma venda já criada para um cliente ativo,
**quando** esse cliente se tornar inativo posteriormente,
**então** a venda permanece vinculada ao cliente original.

### AC-M4-011 — Inativação posterior não autoriza novas vendas

**Dado** um cliente que ficou inativo após vendas anteriores,
**quando** o usuário tentar criar uma nova venda para ele,
**então** a nova venda continua bloqueada.

## Preço

### AC-M4-012 — Ajuste manual de preço somente em `RASCUNHO`

**Dado** uma venda em `RASCUNHO`,
**quando** o usuário ajustar manualmente o preço de uma cesta,
**então** a alteração é aceita e o total da venda é recalculado.

### AC-M4-013 — Preço bloqueado a partir de `CONFIRMADA`

**Dado** uma venda em `CONFIRMADA` ou estado posterior do fluxo normal,
**quando** o usuário tentar alterar manualmente o preço acordado de uma cesta pelo fluxo normal,
**então** a operação é bloqueada.

### AC-M4-014 — Sem renegociação excepcional no fluxo normal

**Dado** uma venda já `CONFIRMADA`,
**quando** o usuário operar o fluxo normal do M4,
**então** não existe operação normal de renegociação excepcional de preço após a confirmação.

## Fronteira entre M4 e M5

### AC-M4-015 — M4 não registra pagamentos

**Dado** qualquer operação de venda em M4,
**quando** o usuário criar, editar, preparar, reabrir, entregar ou cancelar a venda,
**então** M4 não registra pagamentos, não calcula total pago e não calcula saldo pago.

### AC-M4-016 — M5 autoriza `RASCUNHO → CONFIRMADA`

**Dado** uma venda em `RASCUNHO`,
**quando** houver tentativa de promovê-la para `CONFIRMADA`,
**então** a autorização financeira da transição pertence ao M5;
**e** ela depende do limiar mínimo de 50% pago e da validação dos dados obrigatórios de entrega.

### AC-M4-017 — Sem regra paralela de confirmação financeira no M4

**Dado** o ciclo operacional da venda definido em M4,
**quando** os estados e suas restrições forem observados,
**então** M4 não implementa uma segunda lógica independente de confirmação financeira para a mesma transição `RASCUNHO → CONFIRMADA`.

### AC-M4-018 — Sem efeitos automáticos de estoque no M4

**Dado** qualquer operação normal de M4, inclusive alteração de composição, preparação, entrega, reabertura ou cancelamento,
**quando** ela for concluída,
**então** M4 não presume dedução, devolução, reserva ou ajuste automático de estoque.

## Estados da venda

### AC-M4-019 — Estados oficiais

**Dado** o modelo funcional de vendas do M4,
**então** os únicos estados oficiais do fluxo comercial normal são `RASCUNHO`, `CONFIRMADA`, `EM PREPARAÇÃO`, `PRONTA`, `ENTREGUE` e `CANCELADA`.

### AC-M4-020 — Início explícito da preparação

**Dado** uma venda em `CONFIRMADA`,
**quando** o usuário executar a ação de iniciar preparação,
**então** a venda passa para `EM PREPARAÇÃO`;
**e** essa transição não ocorre automaticamente por simples consulta, passagem de tempo ou edição implícita.

### AC-M4-021 — Venda só fica `PRONTA` quando todas as cestas estiverem preparadas

**Dado** uma venda em `EM PREPARAÇÃO`,
**quando** ainda existir pelo menos uma cesta não preparada,
**então** a venda não pode passar para `PRONTA`.

### AC-M4-022 — Registro operacional de preparação por cesta

**Dado** uma venda em `EM PREPARAÇÃO`,
**quando** o usuário consultar o progresso operacional,
**então** é possível verificar por cesta se sua preparação foi concluída.

### AC-M4-023 — Venda só fica `ENTREGUE` quando todas as cestas forem entregues

**Dado** uma venda com múltiplas cestas,
**quando** a última cesta for marcada como entregue,
**então** a venda passa automaticamente para `ENTREGUE`;
**e** enquanto existir cesta pendente de entrega a venda não fica `ENTREGUE`.

## Alterações de composição e histórico

### AC-M4-024 — Alteração de composição em `CONFIRMADA`

**Dado** uma venda em `CONFIRMADA`,
**quando** o usuário adicionar, remover itens ou alterar quantidades de uma cesta,
**então** a alteração é aceita pelo fluxo normal.

### AC-M4-025 — Alteração de composição em `EM PREPARAÇÃO`

**Dado** uma venda em `EM PREPARAÇÃO`,
**quando** o usuário tentar alterar a composição de uma cesta,
**então** o sistema exige confirmação explícita antes de salvar;
**e** apresenta aviso de que itens podem já ter sido separados ou preparados.

### AC-M4-026 — Invalidação seletiva da preparação em `EM PREPARAÇÃO`

**Dado** uma cesta já marcada como preparada em uma venda `EM PREPARAÇÃO`,
**quando** sua composição for alterada,
**então** a marcação anterior de preparação dessa cesta é invalidada e ela volta a ficar pendente.

### AC-M4-027 — Preservação das demais preparações

**Dado** uma venda em `EM PREPARAÇÃO` com várias cestas preparadas,
**quando** somente uma delas tiver sua composição alterada,
**então** as cestas não alteradas preservam sua marcação de preparação concluída.

### AC-M4-028 — Bloqueio de alteração direta em `PRONTA`

**Dado** uma venda em `PRONTA`,
**quando** o usuário tentar alterar diretamente a composição de uma cesta pelo fluxo normal,
**então** a operação é bloqueada até que a venda seja reaberta explicitamente.

### AC-M4-029 — Bloqueio de alteração comercial em `ENTREGUE` e `CANCELADA`

**Dado** uma venda em `ENTREGUE` ou `CANCELADA`,
**quando** o usuário tentar alterar comercialmente a composição de uma cesta pelo fluxo normal,
**então** a operação é bloqueada.

### AC-M4-030 — Histórico não apagável de composição

**Dado** uma alteração de composição em uma cesta da venda,
**quando** a alteração for salva,
**então** o sistema preserva um histórico não apagável pelo fluxo normal contendo composição anterior, composição nova, identificador textual do operador responsável e data/hora.

## Preparação por cesta e reabertura

### AC-M4-031 — Preparação individual por cesta

**Dado** uma venda em `EM PREPARAÇÃO`,
**quando** o usuário concluir a preparação de uma cesta específica,
**então** ele pode marcá-la individualmente como preparada.

### AC-M4-032 — Reabrir venda `PRONTA`

**Dado** uma venda em `PRONTA`,
**quando** o usuário solicitar a reabertura e informar justificativa e identificador textual do responsável,
**então** a operação exige ação explícita, justificativa obrigatória e identificador textual do responsável com data/hora;
**e** a venda retorna para `EM PREPARAÇÃO`.

### AC-M4-033 — Reabertura não altera preço, não cancela e não move estoque

**Dado** uma venda reaberta a partir de `PRONTA`,
**quando** a reabertura for concluída,
**então** essa ação, por si só, não altera preços acordados, não cancela a venda e não executa ajuste automático de estoque.

### AC-M4-034 — Preparação reaplicada somente às cestas alteradas após reabertura

**Dado** uma venda reaberta para `EM PREPARAÇÃO`,
**quando** a composição de apenas algumas cestas for alterada,
**então** somente essas cestas voltam a exigir nova conclusão de preparação.

### AC-M4-035 — Retorno a `PRONTA` após reabertura

**Dado** uma venda reaberta para `EM PREPARAÇÃO`,
**quando** todas as cestas estiverem novamente consideradas preparadas,
**então** a venda pode voltar para `PRONTA`.

### AC-M4-036 — Preparação não é entrega nem estoque

**Dado** uma cesta marcada como preparada,
**quando** o usuário consultar seu estado operacional,
**então** essa marcação não equivale à entrega da cesta e não representa movimentação automática de estoque.

## Entregas

### AC-M4-037 — Entrega individual e explícita por cesta

**Dado** uma cesta de venda,
**quando** o usuário registrar sua entrega,
**então** a entrega depende de ação explícita do usuário para aquela cesta.

### AC-M4-038 — Data e horário agendados não provam entrega

**Dado** uma cesta com data e horário de entrega preenchidos,
**quando** esses dados forem consultados sem registro explícito de entrega,
**então** eles não bastam para considerar a cesta entregue.

### AC-M4-039 — Histórico de entrega preservado

**Dado** uma entrega registrada para uma cesta,
**quando** o histórico operacional for consultado,
**então** o registro identifica a cesta, o identificador textual do operador responsável e a data/hora do registro;
**e** esse histórico é preservado pelo fluxo normal.

### AC-M4-040 — Sem comprovante de entrega no M4

**Dado** o fluxo de entrega do M4,
**quando** a operação for executada,
**então** o sistema não exige nem registra assinatura, fotografia ou outro comprovante de entrega não aprovado.

## Cancelamento

### AC-M4-041 — Cancelamento permitido antes de qualquer entrega

**Dado** uma venda em `RASCUNHO`, `CONFIRMADA`, `EM PREPARAÇÃO` ou `PRONTA`,
**quando** nenhuma cesta tiver sido entregue,
**então** o cancelamento pelo fluxo normal é permitido.

### AC-M4-042 — Cancelamento bloqueado após entrega parcial

**Dado** uma venda em que pelo menos uma cesta já tenha sido entregue,
**quando** o usuário tentar cancelá-la pelo fluxo normal,
**então** o cancelamento é bloqueado, mesmo que outras cestas ainda estejam pendentes.

### AC-M4-043 — Cestas preparadas não impedem cancelamento

**Dado** uma venda com cestas já preparadas,
**quando** nenhuma cesta tiver sido entregue e o usuário solicitar o cancelamento,
**então** o cancelamento continua permitido.

### AC-M4-044 — Cancelamento preserva venda e histórico

**Dado** uma venda cancelada,
**quando** seu registro for consultado depois,
**então** o estado da venda é `CANCELADA`;
**e** a venda, as cestas e seus históricos permanecem preservados.

### AC-M4-045 — Cancelamento sem efeitos automáticos de reembolso, devolução ou estoque

**Dado** uma venda cancelada pelo fluxo normal,
**quando** o cancelamento for concluído,
**então** a operação não presume reembolso, devolução física de itens nem ajuste automático de estoque;
**e** uma venda `ENTREGUE` não pode ser cancelada pelo fluxo normal.

### AC-M4-046 — Venda persistida exige ao menos uma cesta

**Dado** que o usuário tente salvar uma venda sem cestas,
**quando** a operação de salvamento for executada,
**então** o sistema rejeita a persistência da venda e informa que é obrigatória ao menos uma cesta;
**e** a regra não altera a possibilidade de uma cesta individual estar temporariamente vazia durante sua própria edição.

## Auditoria e identificação textual do responsável

### AC-M4-047 — Identificador textual do operador nas operações auditadas

**Dado** uma operação de alteração de composição, reabertura de venda pronta ou registro individual de entrega,
**quando** o operador preencher o campo obrigatório de identificação textual com nome ou identificador e salvar,
**então** o sistema persiste essa declaração operacional associada ao histórico do evento com data/hora;
**e** a operação não requer autenticação, login ou sessão de usuário.

### AC-M4-048 — Rejeição de operação auditada sem identificador textual

**Dado** uma tentativa de executar alteração de composição, reabertura de venda pronta ou registro individual de entrega,
**quando** o operador não preencher o campo de identificador textual (ou fornecer texto vazio ou exclusivamente com espaços),
**então** o sistema bloqueia o salvamento e apresenta erro de validação de campo obrigatório.

### AC-M4-049 — Identificador textual como declaração operacional sem autenticação

**Dado** qualquer registro de auditoria preservado em M4,
**então** o identificador textual persistido representa uma declaração operacional fornecida na interface e não uma prova de identidade autenticada;
**e** o sistema não implementa módulos de usuários, login, controle de permissões ou controle de sessão nesta fase.

## Cobertura das decisões aprovadas

A cobertura das decisões aprovadas do M4 está distribuída assim (51 critérios no total):

* **Venda e composição:** AC-M4-001 a AC-M4-006, AC-M4-004a, AC-M4-004b e AC-M4-046
* **Cliente e `RASCUNHO`:** AC-M4-007 a AC-M4-011
* **Preço:** AC-M4-012 a AC-M4-014
* **Fronteira M4–M5:** AC-M4-015 a AC-M4-018
* **Estados da venda:** AC-M4-019 a AC-M4-023
* **Alterações de composição e histórico:** AC-M4-024 a AC-M4-030
* **Preparação e reabertura:** AC-M4-031 a AC-M4-036
* **Entregas:** AC-M4-037 a AC-M4-040
* **Cancelamento:** AC-M4-041 a AC-M4-045
* **Auditoria e identificação textual do responsável:** AC-M4-047 a AC-M4-049
