# M5 — Critérios de Aceitação

**Versão do documento:** 1.0
**Status:** Aprovado
**Marco:** M5 — Pagamentos, Reserva e Baixa de Estoque
**Data:** 15 de outubro de 2026

---

## Registro de Pagamentos

### AC-M5-001 — Pagamento vinculado a venda

**Dado** uma venda existente em qualquer estado operacional
**Quando** o operador registra um pagamento com valor positivo, método válido e chave de idempotência
**Então** o pagamento é registrado e vinculado à venda

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-002 — Valor do pagamento deve ser positivo

**Dado** uma venda existente
**Quando** o operador tenta registrar um pagamento com valor zero ou negativo
**Então** o sistema rejeita o registro e informa o erro

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-003 — Método de pagamento válido

**Dado** uma venda existente
**Quando** o operador registra um pagamento com método `PIX` ou `CARTAO`
**Então** o pagamento é registrado com o método informado

**Cobertura de testes:** Não verificada diretamente

**Decisão aprovada:** Somente `PIX` e `CARTAO` são aceitos. `DINHEIRO` e `OUTRO` são rejeitados.

---

### AC-M5-004 — Idempotência: retry com mesma chave e mesmos valores

**Dado** um pagamento já registrado com chave de idempotência K, valor V e método M
**Quando** o operador envia novamente a mesma chave K com o mesmo valor V e método M
**Então** o sistema retorna o pagamento existente sem criar duplicata

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (2 testes de idempotência)

---

### AC-M5-005 — Idempotência: mesma chave, valores diferentes

**Dado** um pagamento já registrado com chave de idempotência K
**Quando** o operador envia a mesma chave K com valor ou método diferente
**Então** o sistema rejeita com erro de conflito

**Cobertura de testes:** Direta — `test_m5_concurrency.py`

---

### AC-M5-006 — Pagamentos distintos usam chaves diferentes

**Dado** uma venda existente
**Quando** o operador registra dois pagamentos com chaves de idempotência diferentes
**Então** ambos os pagamentos são registrados como entradas distintas

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-007 — Total pago é soma dos pagamentos

**Dado** uma venda com dois pagamentos registrados (R$ 80,00 e R$ 70,00)
**Quando** o sistema calcula o total pago
**Então** o total pago é R$ 150,00

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-039 — Valor restante é diferença entre total da venda e total pago

**Dado** uma venda com total de R$ 200,00
**E** pagamento registrado de R$ 150,00
**Quando** o sistema calcula o valor restante
**Então** o valor restante é R$ 50,00

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-040 — Comprovante de pagamento fora do escopo M5

O comprovante de pagamento não faz parte do escopo do M5. Pagamentos são registrados sem comprovante.

---

### AC-M5-041 — Pagamento excedente é rejeitado

**Dado** uma venda com total de R$ 200,00
**E** pagamentos registrados totalizando R$ 180,00
**Quando** o operador tenta registrar um novo pagamento de R$ 30,00
**Então** o sistema rejeita o pagamento porque o total resultante (R$ 210,00) excede o total da venda
**E** o valor restante não fica negativo

**Cobertura de testes:** Não verificada diretamente

**Decisão aprovada:** Rejeitar qualquer novo pagamento que faça a soma dos pagamentos registrados ultrapassar o total da venda. A validação deve considerar os pagamentos mais recentes e tratar adequadamente operações concorrentes. Não criar crédito ou reembolso automático.

---

### AC-M5-042 — Pagamento exato é aceito

**Dado** uma venda com total de R$ 200,00
**E** pagamentos registrados totalizando R$ 180,00
**Quando** o operador registra um novo pagamento de R$ 20,00
**Então** o pagamento é aceito, o total pago é R$ 200,00 e o valor restante é R$ 0,00

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-043 — Pagamento excedente rejeitado em concorrência

**Dado** uma venda com total de R$ 200,00
**E** pagamentos registrados totalizando R$ 175,00
**Quando** duas operações concorrentes tentam registrar pagamentos de R$ 25,00 cada
**Então** a primeira operação é aceita, elevando o total pago para R$ 200,00
**E** a segunda operação é rejeitada porque o total resultante (R$ 225,00) excederia o total da venda
**E** o total pago final é R$ 200,00, sem ultrapassar o limite

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (teste de pagamento excedente concorrente).

---

### AC-M5-008 — Pagamento independente da confirmação (RES-003)

**Dado** uma venda em `RASCUNHO` com pagamento registrado
**Quando** a confirmação financeira falha por falta de estoque
**Então** o pagamento permanece registrado e a venda permanece em `RASCUNHO`

**Cobertura de testes:** Indireta — verificada em parte por `test_m4_sales.py` (modificado). **Atenção:** `test_m4_sales.py` foi alterado para importar entidades M5 (`Payment`, `SaleStockReservation`, `SaleCancellationInspection`), portanto esta evidência não é independente — o teste M4 depende de código M5 não commitado.

---

## Confirmação Financeira

### AC-M5-009 — Limiar de 50% atingido autoriza confirmação

**Dado** uma venda em `RASCUNHO` com total de R$ 200,00
**E** pagamento registrado de R$ 100,00 (50%)
**E** todas as cestas com dados de entrega completos
**E** estoque disponível para reserva integral
**Quando** o operador solicita a confirmação
**Então** a venda é confirmada financeiramente e passa para `CONFIRMADA`

**Cobertura de testes:** Indireta — `test_m4_sales.py` (modificado). **Atenção:** `test_m4_sales.py` foi alterado para importar entidades M5, portanto esta evidência não é independente.

---

### AC-M5-010 — Limiar de 50% não atingido bloqueia confirmação

**Dado** uma venda em `RASCUNHO` com total de R$ 200,00
**E** pagamento registrado de R$ 99,00 (49,5%)
**Quando** o operador solicita a confirmação
**Então** a confirmação é rejeitada e a venda permanece em `RASCUNHO`

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-011 — Dados de entrega incompletos bloqueiam confirmação

**Dado** uma venda em `RASCUNHO` com pagamento ≥ 50%
**E** uma cesta sem destinatário, endereço, data ou horário de entrega
**Quando** o operador solicita a confirmação
**Então** a confirmação é rejeitada e a venda permanece em `RASCUNHO`

**Cobertura de testes:** Direta — `test_m4_sales.py` (`test_confirmation_requires_complete_delivery_data`)

---

### AC-M5-012 — Confirmação e reserva são atômicas (RES-001)

**Dado** uma venda em `RASCUNHO` com pagamento ≥ 50%
**E** estoque disponível para todos os produtos
**Quando** o operador solicita a confirmação
**Então** a reserva de todos os produtos e a mudança de estado ocorrem na mesma transação

**Cobertura de testes:** Indireta — `test_m5_concurrency.py` (`test_two_sales_competing_for_stock`)

---

### AC-M5-013 — Falha na reserva impede confirmação (RES-001)

**Dado** uma venda em `RASCUNHO` com pagamento ≥ 50%
**E** estoque insuficiente para um dos produtos
**Quando** o operador solicita a confirmação
**Então** nenhuma reserva é criada e a venda permanece em `RASCUNHO`

**Cobertura de testes:** Indireta — `test_m5_concurrency.py` (`test_two_sales_competing_for_stock`)

---

### AC-M5-014 — Bloqueio por estoque insuficiente informa faltantes (RES-002)

**Dado** uma venda em `RASCUNHO` com pagamento ≥ 50%
**E** estoque insuficiente para o produto X (necessário: 5, disponível: 2)
**Quando** o operador solicita a confirmação
**Então** a confirmação é bloqueada e o sistema informa que faltam 3 unidades do produto X

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-015 — Reserva não é baixa física (RES-004)

**Dado** uma venda confirmada com reservas ativas
**Quando** o saldo de estoque físico é consultado
**Então** o saldo permanece inalterado em relação ao momento anterior à confirmação

**Cobertura de testes:** Não verificada diretamente

---

## Baixa Física

### AC-M5-016 — Baixa física no início da preparação (RES-005)

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** O tipo `OUTPUT` é uma decisão do desenho técnico.

**Dado** uma venda em `CONFIRMADA` com reservas ativas
**Quando** o operador inicia a preparação (`CONFIRMADA → EM PREPARAÇÃO`)
**Então** movimentações de baixa física são criadas para todos os produtos e as reservas são atualizadas

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (`test_preparation_start_rollback_on_insufficient_stock`)

---

### AC-M5-017 — Baixa física é atômica (RES-005)

**Dado** uma venda em `CONFIRMADA`
**Quando** a baixa física falha para um produto
**Então** nenhuma baixa parcial é registrada e a venda permanece em `CONFIRMADA`

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (`test_preparation_start_rollback_on_insufficient_stock`)

---

### AC-M5-018 — Entrega não move estoque

**Dado** uma venda com preparação iniciada e baixa física já registrada
**Quando** o operador registra a entrega de uma cesta
**Então** nenhuma nova movimentação de estoque é criada

**Cobertura de testes:** Não verificada diretamente

---

## Alterações de Composição com Reserva

### AC-M5-019 — Adição exige reserva da diferença (RES-006)

**Dado** uma venda confirmada com reserva ativa
**E** estoque disponível para a diferença
**Quando** o operador adiciona um item ou aumenta a quantidade
**Então** a diferença de quantidades é reservada e a composição é atualizada

**Cobertura de testes:** Indireta — `test_m5_concurrency.py` (`test_concurrent_composition_edits`)

---

### AC-M5-020 — Adição rejeitada sem estoque (RES-006)

**Dado** uma venda confirmada com reserva ativa
**E** estoque insuficiente para a diferença
**Quando** o operador tenta adicionar um item ou aumentar a quantidade
**Então** a alteração é rejeitada e a composição e a reserva permanecem inalteradas

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-021 — Redução libera apenas quantidades reservadas (RES-007)

**Dado** uma venda com produtos parcialmente consumidos (baixados fisicamente)
**Quando** o operador reduz a quantidade de um produto
**Então** apenas as quantidades ainda reservadas são liberadas; as quantidades já baixadas não geram entrada de estoque

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-022 — Quantidades baixadas não geram entrada automática (RES-008)

**Dado** uma venda com produtos já baixados fisicamente
**Quando** o operador remove o produto da composição
**Então** nenhuma movimentação `ENTRY` é criada automaticamente

**Cobertura de testes:** Não verificada diretamente

---

## Reabertura

### AC-M5-023 — Reabertura não repete baixas (RES-009)

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** O tipo `OUTPUT` é uma decisão do desenho técnico.

**Dado** uma venda `PRONTA` com baixas físicas já realizadas
**Quando** o operador reabre a venda para `EM PREPARAÇÃO`
**Então** nenhuma nova movimentação de baixa física é criada

**Cobertura de testes:** Não verificada diretamente

---

## Cancelamento

### AC-M5-024 — Cancelamento antes da preparação libera reservas (RES-010)

**Dado** uma venda em `CONFIRMADA` com reservas ativas
**Quando** o operador cancela a venda
**Então** todas as reservas são liberadas sem movimentação física e a venda passa para `CANCELADA`

**Cobertura de testes:** Parcial — `test_m5_concurrency.py` (`test_cancel_after_prep_inspection_reintegration`)

---

### AC-M5-025 — Cancelamento após preparação cria inspeção (RES-011)

**Dado** uma venda em `EM PREPARAÇÃO` com baixas físicas registradas
**Quando** o operador cancela a venda
**Então** as reservas remanescentes são liberadas e registros de inspeção são criados para os produtos baixados

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (`test_cancel_after_prep_inspection_reintegration`)

---

### AC-M5-026 — Inspeção registra quantidade aproveitável (RES-011)

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** Os estados `PENDING` e `INSPECTED` são uma decisão do desenho técnico.

**Dado** um registro de inspeção com estado `PENDING`
**Quando** o operador registra a inspeção com quantidade aproveitável
**Então** o registro é atualizado com estado `INSPECTED` e a quantidade reintegrável é definida

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-027 — Reintegração cria ENTRY e atualiza inspeção (RES-011)

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** O estado `INSPECTED` é uma decisão do desenho técnico.

**Dado** um registro de inspeção com estado `INSPECTED` e quantidade aproveitável > 0
**Quando** o operador reintegra uma quantidade
**Então** uma movimentação `ENTRY` é criada e o registro de inspeção é atualizado

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-028 — Reintegração duplicada é impedida (RES-011)

**Dado** um registro de inspeção com quantidade aproveitável de 3 unidades
**E** 3 unidades já reintegradas
**Quando** o operador tenta reintegrar mais unidades
**Então** o sistema rejeita a reintegração

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-029 — Cancelamento bloqueado após entrega (RES-012)

**Dado** uma venda com pelo menos uma cesta entregue
**Quando** o operador tenta cancelar a venda
**Então** o cancelamento é bloqueado

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (`test_cancel_after_prep_inspection_reintegration`)

---

## Ajustes de Estoque e Cobertura

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** Os critérios abaixo referem-se à regra de rejeitar ajustes negativos que comprometam a cobertura de reservas, que é uma decisão do desenho técnico, não uma regra de negócio aprovada.

### AC-M5-030 — Ajuste negativo rejeitado quando viola cobertura de reservas

**Dado** um produto com saldo 10 e reservas ativas de 8
**Quando** o operador tenta um ajuste de -5
**Então** o ajuste é rejeitado porque o saldo resultante (5) é inferior às reservas ativas (8)

**Cobertura de testes:** Não verificada diretamente

---

### AC-M5-031 — Ajuste negativo permitido dentro da cobertura

**Dado** um produto com saldo 10 e reservas ativas de 8
**Quando** o operador tenta um ajuste de -2
**Então** o ajuste é permitido porque o saldo resultante (8) cobre as reservas ativas (8)

**Cobertura de testes:** Não verificada diretamente

---

## Concorrência

### AC-M5-032 — Duas vendas concorrentes pelo mesmo estoque

**Dado** um produto com 3 unidades em estoque
**E** duas vendas em `RASCUNHO` com pagamento ≥ 50%, cada uma necessitando de 3 unidades
**Quando** as duas confirmações são solicitadas concorrentemente
**Então** apenas uma confirmação é bem-sucedida; a outra é rejeitada por estoque insuficiente

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (`test_two_sales_competing_for_stock`)

---

### AC-M5-033 — Confirmação e ajuste concorrentes

**Dado** um produto com estoque limitado
**E** uma confirmação de venda e um ajuste de estoque executados concorrentemente sobre o mesmo produto
**Então** as operações são serializadas e a consistência do estoque é preservada

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (`test_adjustment_vs_confirmation_concurrent`)

---

### AC-M5-034 — Alterações de composição concorrentes

**Dado** uma venda confirmada
**E** duas alterações de composição solicitadas concorrentemente
**Então** as operações são serializadas e a consistência da composição e das reservas é preservada

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (`test_concurrent_composition_edits`)

---

### AC-M5-035 — Hierarquia de locks previne deadlock

**Dado** múltiplas operações concorrentes sobre vendas, reservas e produtos
**Quando** as operações adquirem locks
**Então** a hierarquia de locks (Sale → Reservation → Inspection → Product) previne deadlocks

**Cobertura de testes:** Direta — `test_m5_concurrency.py` (`test_lock_hierarchy_no_deadlock`)

---

## Fronteira M4-M5

### AC-M5-036 — M5 autoriza confirmação financeira

**Dado** uma venda em `RASCUNHO` com pagamento ≥ 50% e estoque disponível
**Quando** o operador solicita a confirmação
**Então** M5 autoriza a transição `RASCUNHO → CONFIRMADA`

**Cobertura de testes:** Indireta — `test_m4_sales.py` (modificado). **Atenção:** `test_m4_sales.py` foi alterado para importar entidades M5, portanto esta evidência não é independente.

---

### AC-M5-037 — M4 não registra pagamentos

**Dado** o código do M4
**Quando** o código é inspecionado
**Então** nenhuma função ou endpoint do M4 registra pagamentos

**Cobertura de testes:** Verificação estática — AC-M4-015

---

### AC-M5-038 — M4 não move estoque automaticamente

**Dado** o código do M4
**Quando** o código é inspecionado
**Então** nenhuma função ou endpoint do M4 cria movimentações de estoque

**Cobertura de testes:** Verificação estática — AC-M4-018

---

## Cobertura das Regras Aprovadas

| Regra | Critérios M5 | Cobertura de Testes |
|-------|-------------|---------------------|
| RES-001 | AC-M5-012, AC-M5-013 | Indireta |
| RES-002 | AC-M5-014 | Não verificada |
| RES-003 | AC-M5-008 | Indireta |
| RES-004 | AC-M5-015 | Não verificada |
| RES-005 | AC-M5-016, AC-M5-017 | Direta |
| RES-006 | AC-M5-019, AC-M5-020 | Indireta / Não verificada |
| RES-007 | AC-M5-021 | Não verificada |
| RES-008 | AC-M5-022 | Não verificada |
| RES-009 | AC-M5-023 | Não verificada |
| RES-010 | AC-M5-024 | Parcial |
| RES-011 | AC-M5-025, AC-M5-026, AC-M5-027, AC-M5-028 | Direta / Não verificada |
| RES-012 | AC-M5-029 | Direta |
| PAY-001 | AC-M5-001, AC-M5-037 | Não verificada |
| PAY-002 | AC-M5-009, AC-M5-010, AC-M5-011 | Indireta |
| Valor restante | AC-M5-039 | Não verificada |
| Pagamento excedente | AC-M5-041, AC-M5-042, AC-M5-043 | Direta |

---

**Versão 1.0 — 15 de outubro de 2026**

Preparado para: Em uso — M5 aprovado e Fase 1 concluída
Status: Aprovado — 15 de outubro de 2026
