# M5 — Casos de Uso de Pagamentos, Reserva e Baixa de Estoque

**Versão do documento:** 1.0
**Status:** Aprovado
**Marco:** M5 — Pagamentos, Reserva e Baixa de Estoque
**Data:** 15 de outubro de 2026

---

## UC-M5-001 — Registrar pagamento de venda

**Objetivo:** Registrar um pagamento recebido para uma venda existente.

**Pré-condições:**
- Venda existe no sistema.

**Fluxo principal:**
1. O operador informa o valor, o método de pagamento e uma chave de idempotência.
2. O sistema valida que o valor é positivo.
3. O sistema valida que o método é um dos aprovados (`PIX` ou `CARTAO`).
4. O sistema verifica que o total pago resultante não excede o valor total da venda.
5. O sistema registra o pagamento vinculado à venda.
6. O sistema confirma o registro.

**Decisão aprovada:** Somente `PIX` e `CARTAO` são aceitos. `DINHEIRO` e `OUTRO` são rejeitados.

**Fluxos alternativos:**
- 2a. Valor inválido (zero ou negativo): o sistema rejeita e informa o erro.
- 3a. Método inválido (incluindo `DINHEIRO` e `OUTRO`): o sistema rejeita e informa os métodos aceitos.
- 4a. Pagamento excedente: o total pago resultante ultrapassaria o valor total da venda. O sistema rejeita e informa o valor restante.
- 5a. Chave de idempotência já usada com os mesmos valores: o sistema retorna o pagamento existente (idempotência).
- 5b. Chave de idempotência já usada com valores diferentes: o sistema rejeita com erro de conflito.

**Pós-condições:**
- Pagamento registrado e vinculado à venda.
- Total pago da venda atualizado.

**Regras aplicáveis:** PAY-001, RES-003

---

## UC-M5-002 — Registrar múltiplos pagamentos

**Objetivo:** Registrar vários pagamentos parciais para a mesma venda.

**Pré-condições:**
- Venda existe no sistema.

**Fluxo principal:**
1. O operador registra o primeiro pagamento (UC-M5-001).
2. O operador registra o segundo pagamento com chave de idempotência diferente (UC-M5-001).
3. O sistema soma os pagamentos e atualiza o total pago.
4. O sistema exibe o total pago e o valor restante.
**Pós-condições:**
- Múltiplos pagamentos registrados.
- Total pago reflete a soma de todos os pagamentos.

**Regras aplicáveis:** PAY-001

---

## UC-M5-003 — Confirmar venda com pagamento suficiente e estoque disponível

**Objetivo:** Autorizar financeiramente a transição `RASCUNHO → CONFIRMADA` quando todas as condições são satisfeitas.

**Pré-condições:**
- Venda em `RASCUNHO`.
- Pagamento registrado atingiu pelo menos 50% do valor total.
- Todas as cestas têm dados de entrega completos.
- Estoque disponível para reserva integral.

**Fluxo principal:**
1. O operador solicita a confirmação da venda.
2. O sistema verifica que o total pago ≥ 50% do valor total.
3. O sistema verifica que todas as cestas têm dados de entrega completos.
4. O sistema verifica a disponibilidade integral de todos os produtos.
5. O sistema reserva todas as quantidades necessárias.
6. O sistema efetiva a confirmação (`RASCUNHO → CONFIRMADA`).
7. O sistema confirma a operação.

**Pós-condições:**
- Venda no estado `CONFIRMADA`.
- Reservas criadas para todos os produtos.
- Estoque físico inalterado (reserva não é baixa).

**Regras aplicáveis:** PAY-002, RES-001, RES-004

---

## UC-M5-004 — Bloquear confirmação por pagamento insuficiente

**Objetivo:** Impedir a confirmação quando o pagamento não atingiu o limiar de 50%.

**Pré-condições:**
- Venda em `RASCUNHO`.
- Pagamento registrado é inferior a 50% do valor total.

**Fluxo principal:**
1. O operador solicita a confirmação da venda.
2. O sistema verifica que o total pago < 50% do valor total.
3. O sistema rejeita a confirmação e informa o limiar não atingido.

**Pós-condições:**
- Venda permanece em `RASCUNHO`.
- Pagamento registrado preservado.
- Nenhuma reserva criada.

**Regras aplicáveis:** PAY-002

---

## UC-M5-005 — Bloquear confirmação por estoque insuficiente

**Objetivo:** Impedir a confirmação quando o estoque não cobre integralmente os produtos da venda.

**Pré-condições:**
- Venda em `RASCUNHO`.
- Pagamento registrado atingiu pelo menos 50% do valor total.
- Estoque insuficiente para um ou mais produtos.

**Fluxo principal:**
1. O operador solicita a confirmação da venda.
2. O sistema verifica que o total pago ≥ 50%.
3. O sistema verifica a disponibilidade de estoque.
4. O sistema identifica produtos com estoque insuficiente.
5. O sistema rejeita a confirmação e informa os produtos e quantidades faltantes.

**Pós-condições:**
- Venda permanece em `RASCUNHO`.
- Pagamento registrado preservado.
- Nenhuma reserva criada.

**Regras aplicáveis:** RES-001, RES-002, RES-003

---

## UC-M5-006 — Bloquear confirmação por dados de entrega incompletos

**Objetivo:** Impedir a confirmação quando alguma cesta não possui dados de entrega completos.

**Pré-condições:**
- Venda em `RASCUNHO`.
- Pagamento registrado atingiu pelo menos 50% do valor total.
- Pelo menos uma cesta sem destinatário, endereço, data ou horário de entrega.

**Fluxo principal:**
1. O operador solicita a confirmação da venda.
2. O sistema verifica que o total pago ≥ 50%.
3. O sistema verifica os dados de entrega de todas as cestas.
4. O sistema identifica cestas com dados incompletos.
5. O sistema rejeita a confirmação e informa quais dados faltam.

**Pós-condições:**
- Venda permanece em `RASCUNHO`.
- Nenhuma reserva criada.

**Regras aplicáveis:** PAY-002

---

## UC-M5-007 — Iniciar preparação com baixa física

**Objetivo:** Executar a baixa física de todos os produtos ao iniciar a preparação.

**Pré-condições:**
- Venda no estado `CONFIRMADA`.
- Reservas ativas para todos os produtos.

**Fluxo principal:**
1. O operador solicita o início da preparação.
2. O sistema valida que a venda está em `CONFIRMADA`.
3. O sistema executa a baixa física de todos os produtos como movimentação de estoque para baixa física.
4. O sistema libera as reservas correspondentes.
5. O sistema muda o estado para `EM PREPARAÇÃO`.
6. O sistema confirma a operação.

**⚠️ DECISÃO TÉCNICA:** O tipo específico da movimentação (`OUTPUT`) é uma decisão do desenho técnico, pendente de aprovação formal.

**Pós-condições:**
- Venda no estado `EM PREPARAÇÃO`.
- Movimentações de baixa física registradas para todos os produtos.
- Reservas atualizadas (quantidades consumidas).
- Estoque físico reduzido.

**Fluxos alternativos:**
- 3a. Estoque físico insuficiente para baixa: o sistema rejeita, reverte tudo e mantém a venda em `CONFIRMADA`.

**Regras aplicáveis:** RES-005

---

## UC-M5-008 — Alterar composição com reserva de diferença

**Objetivo:** Adicionar itens ou aumentar quantidades em uma venda confirmada, reservando a diferença.

**Pré-condições:**
- Venda em `CONFIRMADA` ou `EM PREPARAÇÃO`.
- Estoque disponível para a diferença de quantidades.

**Fluxo principal:**
1. O operador solicita a alteração da composição de uma cesta.
2. O sistema calcula a diferença de quantidades para cada produto.
3. O sistema verifica a disponibilidade para a diferença.
4. O sistema reserva a diferença de quantidades.
5. O sistema atualiza a composição da cesta.
6. O sistema registra o histórico da alteração.
7. O sistema confirma a operação.

**Pós-condições:**
- Composição atualizada.
- Reserva da diferença criada.
- Histórico registrado.

**Fluxos alternativos:**
- 4a. Estoque insuficiente para a diferença: o sistema rejeita a alteração inteira. A composição e a reserva permanecem inalteradas.

**Regras aplicáveis:** RES-006

---

## UC-M5-009 — Reduzir composição com liberação de reserva

**Objetivo:** Reduzir quantidades ou remover itens, liberando apenas as quantidades ainda reservadas.

**Pré-condições:**
- Venda em `CONFIRMADA` ou `EM PREPARAÇÃO`.

**Fluxo principal:**
1. O operador solicita a redução de um item ou a remoção de um produto.
2. O sistema calcula a diferença de quantidades.
3. O sistema libera as quantidades ainda reservadas (não consumidas).
4. O sistema atualiza a composição da cesta.
5. O sistema registra o histórico da alteração.
6. O sistema confirma a operação.

**Pós-condições:**
- Composição atualizada.
- Reservas liberadas apenas para quantidades não consumidas.
- Quantidades já baixadas fisicamente não geram entrada de estoque.
- Histórico registrado.

**Regras aplicáveis:** RES-007, RES-008

---

## UC-M5-010 — Cancelar venda antes da preparação

**Objetivo:** Cancelar uma venda antes do início da preparação.

**Pré-condições:**
- Venda em `RASCUNHO` ou `CONFIRMADA`.
- Nenhuma cesta entregue.

**Fluxo principal — venda em `RASCUNHO`:**
1. O operador solicita o cancelamento da venda.
2. O sistema valida que nenhuma cesta foi entregue.
3. O sistema muda o estado para `CANCELADA`.
4. O sistema confirma o cancelamento.

**Fluxo principal — venda em `CONFIRMADA`:**
1. O operador solicita o cancelamento da venda.
2. O sistema valida que nenhuma cesta foi entregue.
3. O sistema libera todas as reservas sem movimentação física.
4. O sistema muda o estado para `CANCELADA`.
5. O sistema confirma o cancelamento.

**Pós-condições:**
- Venda no estado `CANCELADA`.
- Em `RASCUNHO`: sem efeito no estoque (não havia reserva).
- Em `CONFIRMADA`: reservas liberadas.
- Estoque físico inalterado em ambos os casos.
- Pagamentos registrados preservados.

**Regras aplicáveis:**
- Fluxo `RASCUNHO`: sem regra RES específica (comportamento de cancelamento de venda em rascunho, sem reserva).
- Fluxo `CONFIRMADA`: RES-010

---

## UC-M5-011 — Cancelar venda após preparação com inspeção

**Objetivo:** Cancelar uma venda após o início da preparação, criando registros de inspeção.

**Pré-condições:**
- Venda em `EM PREPARAÇÃO` ou `PRONTA`.
- Nenhuma cesta entregue.

**Fluxo principal:**
1. O operador solicita o cancelamento da venda.
2. O sistema valida que nenhuma cesta foi entregue.
3. O sistema libera as reservas remanescentes (produtos não baixados).
4. O sistema cria registros de inspeção para cada produto com quantidades baixadas.
5. O sistema muda o estado para `CANCELADA`.
6. O sistema confirma o cancelamento e informa a necessidade de inspeção.

**Pós-condições:**
- Venda no estado `CANCELADA`.
- Reservas remanescentes liberadas.
- Registros de inspeção criados com estado `PENDING`.
- Pagamentos registrados preservados.

**Regras aplicáveis:** RES-011

---

## UC-M5-012 — Registrar inspeção de produtos cancelados

**Objetivo:** Registrar o resultado da conferência física dos produtos baixados após cancelamento.

**Pré-condições:**
- Registro de inspeção com estado `PENDING`.

**Fluxo principal:**
1. O operador confere fisicamente os produtos baixados.
2. O operador informa a quantidade inspecionada e a quantidade aproveitável.
3. O sistema atualiza o registro de inspeção com os resultados.
4. O sistema muda o estado para `INSPECTED` (ou `DISCARDED` se nada for aproveitável).
5. O sistema confirma a inspeção.

**Pós-condições:**
- Registro de inspeção atualizado.
- Quantidade aproveitável definida para reintegração.

**Regras aplicáveis:** RES-011

---

## UC-M5-013 — Reintegrar produtos ao estoque

**Objetivo:** Retornar produtos fisicamente recuperados ao estoque após inspeção.

**Pré-condições:**
- Registro de inspeção com estado `INSPECTED`.
- Quantidade aproveitável > 0.

**Fluxo principal:**
1. O operador solicita a reintegração de uma quantidade.
2. O sistema valida que a quantidade não excede a quantidade aproveitável não reintegrada.
3. O sistema cria uma movimentação `ENTRY` com a quantidade reintegrada.
4. O sistema atualiza o registro de inspeção.
5. Se toda a quantidade aproveitável foi reintegrada, o estado muda para `REINTEGRATED`.
6. O sistema confirma a reintegração.

**Pós-condições:**
- Movimentação `ENTRY` registrada.
- Estoque físico aumentado.
- Registro de inspeção atualizado.

**Fluxos alternativos:**
- 2a. Quantidade excede a aproveitável: o sistema rejeita.

**Regras aplicáveis:** RES-011

---

## UC-M5-014 — Bloquear cancelamento após entrega

**Objetivo:** Impedir o cancelamento quando alguma cesta já foi entregue.

**Pré-condições:**
- Venda com pelo menos uma cesta entregue.

**Fluxo principal:**
1. O operador solicita o cancelamento da venda.
2. O sistema verifica que alguma cesta foi entregue.
3. O sistema rejeita o cancelamento.

**Pós-condições:**
- Venda permanece no estado atual.
- Nenhuma mudança nas reservas ou no estoque.

**Regras aplicáveis:** RES-012

---

## UC-M5-015 — Reabertura sem repetição de baixas

**Objetivo:** Reabrir uma venda `PRONTA` sem repetir baixas físicas já realizadas.

**Pré-condições:**
- Venda no estado `PRONTA`.
- Baixas físicas já realizadas durante a preparação anterior.

**Fluxo principal:**
1. O operador solicita a reabertura da venda com justificativa.
2. O sistema registra a reabertura no histórico.
3. O sistema muda o estado para `EM PREPARAÇÃO`.
4. O sistema **não** executa nova baixa física.
5. O sistema confirma a reabertura.

**Pós-condições:**
- Venda no estado `EM PREPARAÇÃO`.
- Histórico de reabertura registrado.
- Estoque físico inalterado.
- Reservas inalteradas.

**Regras aplicáveis:** RES-009

---

## UC-M5-016 — Validar a fronteira operacional com M4

**Objetivo:** Confirmar que M5 não duplica responsabilidades do M4.

**Pré-condições:**
- M4 e M5 implementados.

**Fluxo principal:**
1. Verificar que M4 não registra pagamentos.
2. Verificar que M4 não calcula total pago.
3. Verificar que M4 não implementa lógica de confirmação financeira.
4. Verificar que M4 não move estoque automaticamente.
5. Verificar que M5 autoriza `RASCUNHO → CONFIRMADA` financeiramente.
6. Verificar que M5 reserva estoque na confirmação.

**Pós-condições:**
- Fronteira M4-M5 validada.
- Nenhuma duplicação de responsabilidades.

**Regras aplicáveis:** AC-M4-015 a AC-M4-018
