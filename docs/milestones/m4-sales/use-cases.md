# M4 — Casos de Uso de Vendas

**Versão do documento:** 0.2
**Status:** DRAFT — formalização documental para revisão do Product Owner (implementação não iniciada; condicionada ao fechamento da correção de M2 e decisões pendentes de negócio)
**Marco:** M4 — Vendas (Sales)

Os casos de uso abaixo descrevem o comportamento operacional do M4. Pagamentos, confirmação financeira, cálculo de total pago, comprovantes e movimentações automáticas de estoque pertencem ao M5 ou a marcos futuros. As operações auditadas adotam mecanismo provisório de declaração textual do operador responsável, sem sistema de autenticação ou login.

---

## UC-M4-001 — Criar e salvar venda em `RASCUNHO`

**Objetivo:** Criar uma venda operacional vinculada a um cliente ativo e salvá-la em `RASCUNHO`.

**Pré-condições:** O cliente selecionado está ativo em M3.

**Fluxo principal:**
1. O usuário inicia a criação da venda.
2. Seleciona um cliente ativo.
3. Adiciona uma ou mais cestas à venda.
4. Informa os dados de entrega já disponíveis para cada cesta.
5. Salva a venda em `RASCUNHO`.

**Alternativas:**
* Em `RASCUNHO`, destinatário, endereço, data e horário podem permanecer incompletos.
* O usuário pode continuar editando a venda depois de salva em `RASCUNHO`.

**Regras aplicáveis:** cliente ativo para nova venda; `RASCUNHO` admite dados de entrega incompletos; M4 não confirma financeiramente nem deduz estoque.

**Critérios relacionados:** AC-M4-007, AC-M4-008, AC-M4-015, AC-M4-019.

**Resultado esperado:** A venda fica persistida em `RASCUNHO` com o cliente vinculado e as cestas adicionadas.

## UC-M4-002 — Validar cliente para nova venda

**Objetivo:** Garantir que novas vendas só possam ser criadas para clientes ativos.

**Pré-condições:** Existem clientes ativos e inativos em M3.

**Fluxo principal:**
1. O usuário inicia a criação de uma venda.
2. Seleciona um cliente.
3. O sistema verifica o status do cliente antes do salvamento.
4. Se o cliente estiver ativo, a venda pode ser salva.

**Alternativas:**
* Se o cliente estiver inativo, a criação da nova venda é bloqueada.
* Se um cliente vinculado a venda já existente se tornar inativo depois, a venda existente continua válida.

**Regras aplicáveis:** novas vendas exigem cliente ativo; vínculo existente é preservado após inativação posterior.

**Critérios relacionados:** AC-M4-007, AC-M4-010, AC-M4-011.

**Resultado esperado:** O sistema permite novas vendas somente para clientes ativos, sem quebrar vínculos já existentes.

## UC-M4-003 — Adicionar várias cestas e copiar composição e preço

**Objetivo:** Montar uma venda com múltiplas cestas, preservando a independência operacional de cada uma.

**Pré-condições:** Existem cestas de origem disponíveis para adição à venda.

**Fluxo principal:**
1. O usuário adiciona uma cesta à venda.
2. O sistema copia a composição vigente da origem.
3. O sistema copia o preço vigente da origem.
4. O usuário repete a operação para adicionar outras cestas, inclusive baseadas na mesma origem.
5. O sistema registra os dados independentes de cada cesta na venda.

**Alternativas:**
* Cestas diferentes podem compartilhar o mesmo modelo de origem.
* Cada cesta pode ter destinatário, endereço, data e horário próprios.
* Se a cesta de origem não tiver preço de venda definido, a inclusão na venda é bloqueada até correção da origem.

**Regras aplicáveis:** composição e preço são copiados no momento da adição; a cesta na venda torna-se independente da origem; o total da venda usa os preços registrados das cestas; mudanças futuras no preço da origem não alteram o item já adicionado à venda.

**Critérios relacionados:** AC-M4-001, AC-M4-002, AC-M4-003, AC-M4-004, AC-M4-005.

**Resultado esperado:** A venda passa a conter múltiplas cestas independentes dentro do contexto da venda.

## UC-M4-004 — Ajustar preço de cesta em `RASCUNHO`

**Objetivo:** Permitir ajuste manual do preço acordado antes da confirmação financeira.

**Pré-condições:** A venda está em `RASCUNHO`.

**Fluxo principal:**
1. O usuário abre a venda em `RASCUNHO`.
2. Seleciona a cesta cujo preço deseja ajustar.
3. Informa o novo preço acordado.
4. Salva a alteração.
5. O sistema recalcula o total da venda.

**Alternativas:**
* Alterar a composição da cesta não recalcula automaticamente o preço.
* Após `CONFIRMADA`, o ajuste normal de preço deixa de ser permitido.

**Regras aplicáveis:** ajuste manual de preço somente em `RASCUNHO`; total recalculado quando preços mudam; composição não altera automaticamente o preço.

**Critérios relacionados:** AC-M4-005, AC-M4-006, AC-M4-012, AC-M4-013.

**Resultado esperado:** O novo preço fica registrado e o total da venda é recalculado.

## UC-M4-005 — Editar composição em `CONFIRMADA`

**Objetivo:** Atualizar a composição de uma cesta em venda já `CONFIRMADA` sem renegociar automaticamente o preço, registrando auditoria operacional.

**Pré-condições:** A venda está em `CONFIRMADA`.

**Fluxo principal:**
1. O usuário abre a cesta da venda.
2. Adiciona, remove itens ou altera quantidades.
3. Informa seu nome ou identificador textual de operador responsável no campo obrigatório.
4. Salva a nova composição.
5. O sistema registra o histórico da alteração com a composição anterior, a nova composição, o identificador textual informado e data/hora.

**Alternativas:**
* Se o identificador textual não for informado ou estiver em branco, o salvamento é rejeitado pela validação.
* O preço acordado permanece inalterado no fluxo normal.
* A alteração não deduz, devolve nem ajusta estoque automaticamente.

**Regras aplicáveis:** composição é editável em `CONFIRMADA`; histórico com identificador textual é obrigatório (declaração operacional, sem autenticação); preço continua bloqueado; M4 não executa estoque automático.

**Critérios relacionados:** AC-M4-013, AC-M4-024, AC-M4-029, AC-M4-030, AC-M4-047, AC-M4-048, AC-M4-049.

**Resultado esperado:** A composição é atualizada com histórico preservado e sem alterar automaticamente o preço.

## UC-M4-006 — Editar composição em `EM PREPARAÇÃO`

**Objetivo:** Permitir alteração de composição durante a preparação, com advertência, invalidação seletiva da preparação e registro auditável.

**Pré-condições:** A venda está em `EM PREPARAÇÃO`.

**Fluxo principal:**
1. O usuário abre uma cesta da venda.
2. Solicita alteração de composição.
3. O sistema apresenta aviso explícito de que itens podem já ter sido separados ou preparados.
4. O usuário confirma a alteração.
5. O usuário informa seu identificador textual obrigatório de operador responsável.
6. O sistema salva a nova composição e registra o histórico com dados anteriores, novos, identificador textual e data/hora.
7. O sistema invalida a preparação anterior da cesta alterada.

**Alternativas:**
* Se o identificador textual não for informado, a operação é bloqueada com erro de validação.
* Cestas não alteradas preservam sua preparação concluída.
* O preço acordado não é recalculado automaticamente.

**Regras aplicáveis:** alterações em `EM PREPARAÇÃO` exigem confirmação explícita; alteração invalida a preparação somente da cesta alterada; histórico com identificador textual obrigatório (sem autenticação de usuários).

**Critérios relacionados:** AC-M4-025, AC-M4-026, AC-M4-027, AC-M4-029, AC-M4-047, AC-M4-048, AC-M4-049.

**Resultado esperado:** A composição é atualizada e a cesta alterada volta a ficar pendente de preparação.

## UC-M4-007 — Iniciar preparação da venda

**Objetivo:** Mover uma venda `CONFIRMADA` para `EM PREPARAÇÃO`.

**Pré-condições:** A venda está em `CONFIRMADA`.

**Fluxo principal:**
1. O usuário acessa a venda confirmada.
2. Executa a ação explícita de iniciar a preparação.
3. O sistema muda o estado da venda para `EM PREPARAÇÃO`.

**Alternativas:**
* O sistema não deve iniciar a preparação por mudança implícita de composição, por simples consulta ou por data agendada.

**Regras aplicáveis:** `CONFIRMADA → EM PREPARAÇÃO` exige ação explícita do usuário.

**Critérios relacionados:** AC-M4-020.

**Resultado esperado:** A venda entra em `EM PREPARAÇÃO` apenas por ação explícita do usuário.

## UC-M4-008 — Marcar cesta individualmente como preparada

**Objetivo:** Registrar a conclusão da preparação de cada cesta da venda.

**Pré-condições:** A venda está em `EM PREPARAÇÃO`.

**Fluxo principal:**
1. O usuário conclui a preparação de uma cesta específica.
2. Marca essa cesta como preparada.
3. O sistema registra que a preparação daquela cesta foi concluída.
4. O usuário repete a operação para as demais cestas.
5. Quando todas estiverem preparadas, a venda passa para `PRONTA`.

**Alternativas:**
* Marcar uma cesta como preparada não a entrega.
* Marcar uma cesta como preparada não executa movimentação automática de estoque.

**Regras aplicáveis:** preparação é individual por cesta; venda só fica `PRONTA` quando todas as cestas estiverem preparadas.

**Critérios relacionados:** AC-M4-021, AC-M4-022, AC-M4-031, AC-M4-036.

**Resultado esperado:** O progresso de preparação pode ser acompanhado cesta a cesta, e a venda fica `PRONTA` somente quando todas estiverem concluídas.

## UC-M4-009 — Reabrir venda `PRONTA`

**Objetivo:** Retornar uma venda `PRONTA` para `EM PREPARAÇÃO` com justificativa e identificação textual do operador responsável.

**Pré-condições:** A venda está em `PRONTA`.

**Fluxo principal:**
1. O usuário solicita a reabertura da venda.
2. Informa a justificativa obrigatória.
3. Informa seu nome ou identificador textual de operador responsável no campo obrigatório.
4. Confirma a operação.
5. O sistema registra a justificativa, o identificador textual do responsável e data/hora.
6. O sistema retorna a venda para `EM PREPARAÇÃO`.

**Alternativas:**
* Se a justificativa ou o identificador textual do operador estiverem vazios/em branco, o sistema bloqueia a reabertura com erro de validação.
* A reabertura, por si só, não altera preços, não cancela a venda e não executa ajustes automáticos de estoque.
* Cestas que não tiverem sua composição alterada continuam com preparação concluída.

**Regras aplicáveis:** reabertura é explícita, auditável e exige justificativa e identificador textual (declaração operacional sem autenticação); estado volta para `EM PREPARAÇÃO`.

**Critérios relacionados:** AC-M4-028, AC-M4-032, AC-M4-033, AC-M4-034, AC-M4-035, AC-M4-047, AC-M4-048, AC-M4-049.

**Resultado esperado:** A venda volta a `EM PREPARAÇÃO` com registro de auditoria preservado.

## UC-M4-010 — Registrar entrega por cesta

**Objetivo:** Registrar explicitamente a entrega de uma cesta específica com identificação do operador responsável.

**Pré-condições:** A cesta pertence a uma venda em fluxo operacional que ainda não esteja `CANCELADA` ou `ENTREGUE`.

**Fluxo principal:**
1. O usuário seleciona a cesta.
2. Informa seu nome ou identificador textual de operador responsável no campo de registro.
3. Executa a ação explícita de marcar a cesta como entregue.
4. O sistema registra a cesta, o identificador textual do responsável e a data/hora da entrega.

**Alternativas:**
* Se o identificador textual do responsável não for informado, a operação é rejeitada pela validação.
* A data e o horário agendados da cesta não bastam como prova de entrega.
* O sistema não exige assinatura, fotografia ou comprovante adicional no M4.

**Regras aplicáveis:** entrega é individual e explícita; histórico de entrega deve ser preservado com identificador textual (declaração operacional, sem autenticação).

**Critérios relacionados:** AC-M4-037, AC-M4-038, AC-M4-039, AC-M4-040, AC-M4-047, AC-M4-048, AC-M4-049.

**Resultado esperado:** A cesta fica marcada como entregue com histórico preservado.

## UC-M4-011 — Concluir a entrega da venda

**Objetivo:** Encerrar operacionalmente a venda quando todas as cestas tiverem sido entregues.

**Pré-condições:** A venda possui uma ou mais cestas e ainda não está `ENTREGUE`.

**Fluxo principal:**
1. O usuário registra a entrega das cestas individualmente.
2. O sistema acompanha o conjunto de cestas já entregues.
3. Quando a última cesta é marcada como entregue, o sistema muda automaticamente o estado da venda para `ENTREGUE`.

**Alternativas:**
* Enquanto houver ao menos uma cesta não entregue, a venda não passa para `ENTREGUE`.

**Regras aplicáveis:** `ENTREGUE` é consequência automática da entrega de todas as cestas.

**Critérios relacionados:** AC-M4-023, AC-M4-040.

**Resultado esperado:** A venda é concluída como `ENTREGUE` somente quando todas as cestas forem efetivamente entregues.

## UC-M4-012 — Cancelar venda sem entrega realizada

**Objetivo:** Cancelar a venda preservando seu histórico quando nenhuma cesta tiver sido entregue.

**Pré-condições:** A venda está em `RASCUNHO`, `CONFIRMADA`, `EM PREPARAÇÃO` ou `PRONTA` e nenhuma cesta foi entregue.

**Fluxo principal:**
1. O usuário solicita o cancelamento da venda.
2. O sistema verifica se alguma cesta já foi entregue.
3. Como nenhuma foi entregue, o sistema permite o cancelamento.
4. O estado da venda muda para `CANCELADA`.
5. A venda, as cestas e seus históricos permanecem preservados.

**Alternativas:**
* Cestas já preparadas não impedem o cancelamento.
* O cancelamento não presume reembolso, devolução física de itens nem ajuste automático de estoque.

**Regras aplicáveis:** cancelamento permitido antes de qualquer entrega; preservação de histórico; sem efeitos automáticos de pagamento/estoque.

**Critérios relacionados:** AC-M4-041, AC-M4-043, AC-M4-044.

**Resultado esperado:** A venda é cancelada e seu histórico permanece consultável.

## UC-M4-013 — Bloquear cancelamento após entrega parcial

**Objetivo:** Impedir o cancelamento normal quando já houve entrega de pelo menos uma cesta.

**Pré-condições:** Ao menos uma cesta da venda já foi marcada como entregue.

**Fluxo principal:**
1. O usuário solicita o cancelamento da venda.
2. O sistema verifica o histórico de entrega das cestas.
3. Detecta que existe entrega registrada.
4. Bloqueia o cancelamento pelo fluxo normal.

**Alternativas:**
* O bloqueio permanece mesmo que a venda ainda não tenha sido promovida automaticamente para `ENTREGUE` por existirem outras cestas pendentes.
* Uma venda já `ENTREGUE` também não pode ser cancelada pelo fluxo normal.

**Regras aplicáveis:** qualquer entrega impede cancelamento pelo fluxo normal; `ENTREGUE` é terminal.

**Critérios relacionados:** AC-M4-042, AC-M4-045.

**Resultado esperado:** O cancelamento fica indisponível no fluxo normal depois de qualquer entrega registrada.

## UC-M4-014 — Validar a fronteira operacional com M5

**Objetivo:** Garantir que M4 modele os estados da venda sem duplicar a confirmação financeira de M5.

**Pré-condições:** Existe uma venda em `RASCUNHO` com dados operacionais editáveis.

**Fluxo principal:**
1. O usuário opera a venda em `RASCUNHO` dentro do M4.
2. O sistema permite editar composição, preços e dados operacionais conforme as regras de M4.
3. O sistema não registra pagamento, não calcula total pago e não confirma financeiramente a venda por conta própria.
4. A passagem para `CONFIRMADA` depende do fluxo financeiro de M5, que também valida os dados obrigatórios de entrega.

**Alternativas:**
* M4 não cria estado alternativo para "quase confirmada" nem confirmação provisória.
* M4 não deduz, devolve ou ajusta estoque automaticamente por composição, preparação, entrega ou cancelamento.

**Regras aplicáveis:** separação de responsabilidades entre M4 e M5; confirmação financeira única; ausência de movimentações automáticas de estoque no M4.

**Critérios relacionados:** AC-M4-009, AC-M4-015, AC-M4-016, AC-M4-017, AC-M4-018, AC-M4-030.

**Resultado esperado:** O comportamento operacional do M4 permanece íntegro sem invadir as responsabilidades financeiras do M5.
