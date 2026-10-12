# M5 — Plano de Validação

**Versão do documento:** 0.1 (RASCUNHO)
**Status:** Rascunho para revisão humana — não aprovado
**Marco:** M5 — Pagamentos, Reserva e Baixa de Estoque
**Data:** 12 de outubro de 2026

---

## 1. Objetivo da validação

Validar que a implementação do M5 satisfaz as regras de negócio aprovadas (RES-001 a RES-012, PAY-001, PAY-002) e os critérios de aceitação definidos em `acceptance-criteria.md`.

Esta validação cobre:

- Registro de pagamentos com idempotência.
- Confirmação financeira com limiar de 50%.
- Reserva integral de estoque na confirmação.
- Baixa física no início da preparação.
- Alterações de composição com reserva e liberação de diferença.
- Cancelamento com liberação de reservas e inspeção.
- Reintegração de produtos após inspeção.
- Concorrência e prevenção de deadlock.
- Fronteira M4-M5.

---

## 2. Preparação do ambiente

**⚠️ ATENÇÃO:** A migration `c1d2e3f4a5b6_add_payments_reservations_inspection.py` faz parte de alterações locais ainda não commitadas. Antes de executá-la, confirme que o código M5 está na working tree do repositório.

1. Garantir que o banco de dados está populado com os dados de M1–M4.
2. Executar a migration `c1d2e3f4a5b6_add_payments_reservations_inspection.py`.
3. Verificar que as tabelas `payments`, `sale_stock_reservations` e `sale_cancellation_inspection` foram criadas.
4. Verificar que `inventory_movements` aceita o tipo `OUTPUT` e a coluna `sale_id`.

---

## 3. Validação funcional do domínio

### 3.1 Registro de pagamento

**Cenário positivo:**
1. Criar uma venda em `RASCUNHO` com total de R$ 200,00.
2. Registrar um pagamento de R$ 100,00 via PIX.
3. Verificar que o pagamento foi registrado.
4. Verificar que o total pago é R$ 100,00.
5. Verificar que o valor restante é R$ 100,00.

**Cenário de idempotência:**
5. Reenviar o mesmo pagamento com a mesma chave de idempotência.
6. Verificar que o pagamento existente é retornado sem duplicata.

**Cenário negativo:**
7. Tentar registrar pagamento com valor zero.
8. Verificar que o sistema rejeita.

**Cenário de conflito de idempotência:**
9. Tentar reenviar com a mesma chave mas valor diferente.
10. Verificar que o sistema rejeita com erro de conflito.

**Cenário de comprovante opcional:**
11. Registrar um pagamento sem associar comprovante.
12. Verificar que o pagamento foi registrado com sucesso — a ausência de comprovante não bloqueia.

**⚠️ PENDÊNCIA:** Os formatos aceitos, o método de armazenamento e as validações técnicas de comprovante não foram definidos. Quando definidos, adicionar cenários de comprovante com arquivo.

### 3.2 Múltiplos pagamentos

1. Registrar um segundo pagamento de R$ 50,00 com chave diferente.
2. Verificar que o total pago é R$ 150,00.
3. Verificar que o valor restante é R$ 50,00.

### 3.2b Pagamento excedente rejeitado

**Decisão aprovada:** Rejeitar qualquer novo pagamento que faça a soma dos pagamentos registrados ultrapassar o total da venda.

1. Criar uma venda em `RASCUNHO` com total de R$ 200,00.
2. Registrar um pagamento de R$ 180,00.
3. Tentar registrar um novo pagamento de R$ 30,00.
4. Verificar que o sistema rejeita o pagamento.
5. Verificar que o total pago permanece R$ 180,00.
6. Verificar que o valor restante permanece R$ 20,00.

### 3.2c Pagamento exato aceito

1. Com a venda acima (total R$ 200,00, pago R$ 180,00), registrar um pagamento de R$ 20,00.
2. Verificar que o pagamento é aceito.
3. Verificar que o total pago é R$ 200,00.
4. Verificar que o valor restante é R$ 0,00.

### 3.3 Confirmação financeira — limiar atingido

1. Com pagamento de R$ 100,00 (50% de R$ 200,00) e dados de entrega completos.
2. Solicitar confirmação da venda.
3. Verificar que a venda passa para `CONFIRMADA`.
4. Verificar que reservas foram criadas para todos os produtos.
5. Verificar que o saldo de estoque físico permanece inalterado.

### 3.4 Confirmação financeira — limiar não atingido

1. Criar venda com total de R$ 200,00 e pagamento de R$ 99,00 (49,5%).
2. Solicitar confirmação.
3. Verificar que a confirmação é rejeitada.
4. Verificar que a venda permanece em `RASCUNHO`.
5. Verificar que o pagamento de R$ 99,00 permanece registrado.

### 3.5 Confirmação financeira — estoque insuficiente

1. Criar venda com pagamento ≥ 50% mas com produto sem estoque suficiente.
2. Solicitar confirmação.
3. Verificar que a confirmação é rejeitada.
4. Verificar que nenhuma reserva foi criada.
5. Verificar que o pagamento permanece registrado.

### 3.6 Confirmação financeira — dados de entrega incompletos

1. Criar venda com pagamento ≥ 50% e uma cesta sem dados de entrega.
2. Solicitar confirmação.
3. Verificar que a confirmação é rejeitada.

---

## 4. Validação de reserva e baixa física

### 4.1 Reserva não é baixa física

1. Confirmar uma venda (RES-001).
2. Consultar o saldo de estoque físico antes e após a confirmação.
3. Verificar que o saldo não mudou.

### 4.2 Baixa física no início da preparação

**⚠️ DECISÃO TÉCNICA:** O tipo específico da movimentação (`OUTPUT`) é uma decisão do desenho técnico, pendente de aprovação formal.

1. Iniciar a preparação de uma venda `CONFIRMADA`.
2. Verificar que a venda passa para `EM PREPARAÇÃO`.
3. Verificar que movimentações de baixa física foram criadas para todos os produtos.
4. Verificar que o saldo de estoque físico foi reduzido.
5. Verificar que as reservas foram atualizadas (quantidades consumidas).

### 4.3 Baixa física atômica

1. Tentar iniciar preparação com estoque insuficiente para um produto.
2. Verificar que nenhuma baixa parcial foi registrada.
3. Verificar que a venda permanece em `CONFIRMADA`.

### 4.4 Entrega não move estoque

1. Registrar a entrega de uma cesta após a preparação.
2. Verificar que nenhuma nova movimentação de estoque foi criada.

---

## 5. Validação de alterações de composição

### 5.1 Adição com reserva de diferença

1. Em uma venda `CONFIRMADA`, adicionar um item à composição.
2. Verificar que a diferença foi reservada.
3. Verificar que a composição foi atualizada.

### 5.2 Adição rejeitada sem estoque

1. Tentar adicionar um item sem estoque suficiente para a diferença.
2. Verificar que a alteração foi rejeitada.
3. Verificar que a composição e a reserva permanecem inalteradas.

### 5.3 Redução com liberação de reserva

1. Em uma venda com produtos parcialmente consumidos, reduzir a quantidade.
2. Verificar que apenas as quantidades ainda reservadas foram liberadas.
3. Verificar que nenhuma entrada de estoque foi criada para as quantidades já baixadas.

### 5.4 Remoção não gera entrada automática

1. Remover um produto já baixado fisicamente da composição.
2. Verificar que nenhuma movimentação `ENTRY` foi criada.

---

## 6. Validação de reabertura

### 6.1 Reabertura sem repetição de baixas

**⚠️ DECISÃO TÉCNICA:** O tipo específico da movimentação (`OUTPUT`) é uma decisão do desenho técnico, pendente de aprovação formal.

1. Reabrir uma venda `PRONTA` para `EM PREPARAÇÃO`.
2. Verificar que nenhuma nova movimentação de baixa física foi criada.
3. Verificar que o estoque físico permanece inalterado.

---

## 7. Validação de cancelamento

### 7.1 Cancelamento antes da preparação

1. Cancelar uma venda `CONFIRMADA`.
2. Verificar que todas as reservas foram liberadas.
3. Verificar que nenhuma movimentação física foi criada.
4. Verificar que a venda passou para `CANCELADA`.

### 7.2 Cancelamento após preparação

1. Cancelar uma venda `EM PREPARAÇÃO` com baixas físicas registradas.
2. Verificar que as reservas remanescentes foram liberadas.
3. Verificar que registros de inspeção foram criados para os produtos baixados.
4. Verificar que a venda passou para `CANCELADA`.

### 7.3 Inspeção de produtos cancelados

**⚠️ DECISÃO TÉCNICA:** Os estados `PENDING`, `INSPECTED`, `REINTEGRATED` e `DISCARDED` são decisões do desenho técnico, pendentes de aprovação formal.

1. Registrar a inspeção de um produto com quantidade aproveitável.
2. Verificar que o registro de inspeção foi atualizado para `INSPECTED`.

### 7.4 Reintegração

1. Reintegrar a quantidade aproveitável.
2. Verificar que uma movimentação `ENTRY` foi criada.
3. Verificar que o registro de inspeção foi atualizado.
4. Tentar reintegrar novamente a mesma quantidade.
5. Verificar que a reintegração duplicada foi rejeitada.

### 7.5 Cancelamento bloqueado após entrega

1. Tentar cancelar uma venda com cesta entregue.
2. Verificar que o cancelamento foi bloqueado.

---

## 8. Validação de concorrência

### 8.1 Duas vendas concorrentes pelo mesmo estoque

1. Criar duas vendas com pagamento ≥ 50% para o mesmo produto com estoque limitado.
2. Executar as confirmações concorrentemente.
3. Verificar que apenas uma confirmação foi bem-sucedida.

### 8.2 Confirmação e ajuste concorrentes

1. Executar confirmação de venda e ajuste de estoque concorrentemente sobre o mesmo produto.
2. Verificar que a consistência do estoque foi preservada.

### 8.3 Hierarquia de locks

1. Executar múltiplas operações concorrentes.
2. Verificar que nenhum deadlock ocorreu.

---

## 9. Validação de ajustes de estoque com cobertura de reservas

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** A regra de rejeitar ajustes negativos que comprometam a cobertura de reservas é uma decisão do desenho técnico, não uma regra de negócio aprovada.

### 9.1 Ajuste rejeitado quando viola cobertura

1. Criar reserva ativa de 8 unidades para um produto com saldo 10.
2. Tentar ajuste de -5.
3. Verificar que o ajuste foi rejeitado.

### 9.2 Ajuste permitido dentro da cobertura

1. Com o mesmo cenário, tentar ajuste de -2.
2. Verificar que o ajuste foi permitido.

---

## 10. Validação da fronteira M4–M5

1. Verificar que M4 não registra pagamentos (inspeção de código).
2. Verificar que M4 não calcula total pago (inspeção de código).
3. Verificar que M4 não move estoque automaticamente (inspeção de código).
4. Verificar que M5 autoriza `RASCUNHO → CONFIRMADA` financeiramente.

---

## 11. Testes automatizados — resultado conhecido

Os testes em `test_m5_concurrency.py` cobrem os seguintes cenários:

| Teste | Critério | Status |
|-------|----------|--------|
| `test_two_sales_competing_for_stock` | AC-M5-032 | Implementado |
| `test_preparation_start_rollback_on_insufficient_stock` | AC-M5-016, AC-M5-017 | Implementado |
| `test_cancel_after_prep_inspection_reintegration` | AC-M5-025, AC-M5-029 | Implementado |
| `test_concurrent_composition_edits` | AC-M5-034 | Implementado |
| `test_adjustment_vs_confirmation_concurrent` | AC-M5-033 | Implementado |
| `test_lock_hierarchy_no_deadlock` | AC-M5-035 | Implementado |
| Testes de idempotência | AC-M5-004, AC-M5-005 | Implementado |

**⚠️ ATENÇÃO:** Os testes existem em código não commitado. Os resultados conhecidos são baseados na execução durante a sessão de implementação. A validação formal requer a execução dos testes após o commit.

**⚠️ ATENÇÃO:** `test_m4_sales.py` foi modificado para importar entidades M5 (`Payment`, `SaleStockReservation`, `SaleCancellationInspection`). A evidência de testes M4 que depende de M5 não é independente.

---

## 12. Validação manual

**⚠️ NÃO VALIDADA.**

A validação manual do fluxo completo M5 não foi realizada. Os passos a seguir devem ser executados por um operador humano após a revisão e aprovação dos documentos:

1. Seguir os cenários das seções 3 a 10.
2. Registrar o resultado de cada passo.
3. Identificar discrepâncias entre o comportamento esperado e o observado.
4. Documentar os resultados.

---

## 13. Cenários negativos mínimos

Os seguintes cenários negativos devem ser testados:

- Pagamento com valor zero → rejeitado.
- Pagamento com método inválido (incluindo `DINHEIRO` e `OUTRO`) → rejeitado.
- Pagamento que excede o total da venda → rejeitado.
- Confirmação com pagamento < 50% → rejeitada.
- Confirmação com dados de entrega incompletos → rejeitada.
- Confirmação com estoque insuficiente → rejeitada, pagamento preservado.
- Baixa física com estoque insuficiente → rejeitada, venda permanece `CONFIRMADA`.
- Adição sem estoque para diferença → rejeitada.
- Cancelamento com entrega → bloqueado.
- Reintegração duplicada → rejeitada.
- Ajuste que viola cobertura de reservas → rejeitado.

---

## 14. Cobertura mínima dos critérios de aceitação

| Grupo | Critérios | Cobertura de Testes |
|-------|-----------|---------------------|
| Pagamentos | AC-M5-001 a AC-M5-008, AC-M5-039 a AC-M5-043 | Parcial (idempotência: direta; AC-M5-039 a AC-M5-043: não verificada; demais: não verificada) |
| Confirmação financeira | AC-M5-009 a AC-M5-015 | Indireta |
| Baixa física | AC-M5-016 a AC-M5-018 | Direta / Não verificada |
| Alterações de composição | AC-M5-019 a AC-M5-022 | Indireta / Não verificada |
| Reabertura | AC-M5-023 | Não verificada |
| Cancelamento | AC-M5-024 a AC-M5-029 | Parcial / Direta / Não verificada |
| Ajustes e cobertura | AC-M5-030 a AC-M5-031 | Não verificada |
| Concorrência | AC-M5-032 a AC-M5-035 | Direta |
| Fronteira M4-M5 | AC-M5-036 a AC-M5-038 | Indireta / Estática |

---

## 15. Revisão final da validação

Antes de considerar o M5 validado, os seguintes itens devem ser concluídos:

- [ ] Executar todos os testes automatizados após commit.
- [ ] Executar a validação manual (seções 3 a 10).
- [ ] Verificar que todos os critérios de aceitação com cobertura "Não verificada" possuem teste dedicado.
- [ ] Resolver as pendências de decisão humana listadas no `executive-summary.md`.
- [ ] Obter aprovação do Product Owner.

**⚠️ O M5 não está validado neste momento.** A validação formal depende da aprovação dos documentos e da execução dos testes após commit.

---

**Versão 0.1 — 12 de outubro de 2026**

Preparado para: Revisão humana e aprovação do Product Owner
Status: Rascunho — não aprovado
