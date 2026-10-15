# M5 — Roteiro de Validação Manual (Corrigido)

**Versão:** 0.2 (corrigida com base na auditoria de precisão)  
**Data:** 13 de outubro de 2026  
**Base:** `docs/milestones/m5-payments/validation.md` (seções 3–10)  
**Ambiente:** Aplicação em execução local via `docker-compose`  
**API base:** `http://localhost:8000/api/v1`

---

## Instruções de Preparação de Dados

### Produtos exclusivos de teste

Para evitar interferência com dados reais, criar produtos exclusivos para validação:

```bash
# Criar produto de teste: "Tomate - Validação M5"
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Tomate - Validação M5", "base_unit": "unidade", "reference_price": "5.00"}'

# Criar produto de teste: "Cenoura - Validação M5"
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Cenoura - Validação M5", "base_unit": "unidade", "reference_price": "3.00"}'
```

### Entrada de estoque nos produtos de teste

```bash
# Adicionar 50 unidades de Tomate
curl -X POST http://localhost:8000/api/v1/products/{tomate_id}/inventory/entries \
  -H "Content-Type: application/json" \
  -d '{"quantity": 50, "unit_cost": "5.00"}'

# Adicionar 50 unidades de Cenoura
curl -X POST http://localhost:8000/api/v1/products/{cenoura_id}/inventory/entries \
  -H "Content-Type: application/json" \
  -d '{"quantity": 50, "unit_cost": "3.00"}'
```

### Consultar saldo

```bash
curl http://localhost:8000/api/v1/products/{product_id}/inventory/balance
```

### Modelos de Cesta (Templates)

Criados via interface na tela de Modelos de Cesta (`TemplatesView`). Usar os produtos de teste.

### Clientes

Criados via interface na tela de Clientes (`CustomersView`).

---

## Cenários Já Executados (não repetir)

| Seção | Cenário | Resultado |
|-------|---------|-----------|
| 3.1 | Registro de pagamento | ✓ Aprovado |
| 3.3 | Confirmação com pagamento ≥ 50% e estoque disponível | ✓ Aprovado |
| 3.5 | Confirmação com pagamento ≥ 50% e estoque insuficiente | ✓ Aprovado |

---

## Legenda de Resultado

Para cada cenário, marque o resultado:

- ☐ **Aprovado** — comportamento conforme esperado
- ☐ **Reprovado** — comportamento divergente (descrever o que ocorreu)
- ☐ **Bloqueado** — não foi possível executar (descrever o motivo)

---

## Códigos HTTP — Referência

| Tipo de Erro | Código HTTP | Exemplo |
|-------------|-------------|---------|
| Schema validation (Pydantic `ValueError`) | **422** | Valor zero, método inválido, campo extra |
| Business rule (`BusinessRuleError`) | **409** | Estoque insuficiente, pagamento < 50% |
| Recurso não encontrado (`ResourceNotFoundError`) | **404** | Venda não encontrada |

---

## Endpoints Utilizados

| Operação | Método | Endpoint | Status de Sucesso |
|----------|--------|----------|-------------------|
| Consultar saldo | GET | `/products/{id}/inventory/balance` | 200 |
| Entrada de estoque | POST | `/products/{id}/inventory/entries` | 201 |
| Ajuste de estoque | POST | `/products/{id}/inventory/adjustments` | 201 |
| Movimentações | GET | `/products/{id}/inventory/movements` | 200 |
| Criar venda | POST | `/sales` | 201 |
| Consultar venda | GET | `/sales/{id}` | 200 |
| Confirmar venda | POST | `/sales/{id}/confirm` | 200 |
| Iniciar preparação | POST | `/sales/{id}/start-preparation` | 200 |
| Marcar cesta preparada | POST | `/sales/{id}/baskets/{id}/prepare` | 200 |
| Reabrir venda | POST | `/sales/{id}/reopen` | 200 |
| Entregar cesta | POST | `/sales/{id}/baskets/{id}/deliver` | 200 |
| Cancelar venda | POST | `/sales/{id}/cancel` | 200 |
| Editar composição | PUT | `/sales/{id}/baskets/{id}/composition` | 200 |
| Registrar pagamento | POST | `/sales/{id}/payments` | 201 |
| Listar pagamentos | GET | `/sales/{id}/payments` | 200 |
| Total pago | GET | `/sales/{id}/payments/total` | 200 |
| Listar inspeções | GET | `/sales/{id}/inspections` | 200 |
| Registrar inspeção | POST | `/sales/{id}/inspections/{id}/record` | 200 |
| Reintegrar inspeção | POST | `/sales/{id}/inspections/{id}/reintegrate` | 200 |

---

## 1. Cenário V-M5-01 — Idempotência de Pagamento (Seção 3.1)

**Critérios:** AC-M5-004, AC-M5-005  
**Objetivo:** Verificar que reenviar o mesmo pagamento com a mesma chave de idempotência retorna o pagamento existente sem duplicar.

**Pré-condições:**
- Venda em `RASCUNHO` com total de R$ 200,00 e pelo menos um pagamento registrado.
- Chave de idempotência do pagamento conhecida (ex.: `idem-test-001`).

**Passos na interface:**
1. Abra a venda → clique em "Registrar Pagamento".
2. Preencha: método `PIX`, valor `100.00`, chave de idempotência `idem-test-001`.
3. Clique em "Registrar".
4. Observe a mensagem de sucesso: "Pagamento registrado com sucesso."
5. Sem fechar o modal, clique novamente em "Registrar" (reenvio com mesmos dados).
6. Observe que o sistema não duplica o pagamento.

**Resultado esperado:**
- O segundo envio retorna o mesmo pagamento sem criar duplicata.
- O total pago permanece R$ 100,00.
- O histórico de pagamentos mostra apenas 1 registro.

**Evidência a registrar:**
- Screenshot do resumo de pagamentos após o reenvio.
- Número de registros no histórico: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 2. Cenário V-M5-02 — Pagamento com Valor Zero (Seção 3.1)

**Critérios:** AC-M5-002  
**Objetivo:** Verificar que o sistema rejeita pagamento com valor zero ou negativo.

**Pré-condições:** Venda em `RASCUNHO` ou `CONFIRMADA` com total pago < 100%.

**Passos na interface:**
1. Abra a venda → clique em "Registrar Pagamento".
2. Preencha: método `PIX`, valor `0` (ou `0.00`).
3. Clique em "Registrar".

**Resultado esperado:**
- O botão "Registrar" permanece desabilitado ou o sistema exibe erro.
- Na camada API, o schema `PaymentCreate` rejeita com **HTTP 422** (schema validation).
- Mensagem: "O valor do pagamento deve ser maior que zero."
- Nenhum pagamento é registrado.

**Evidência a registrar:**
- Mensagem de erro exibida: ___
- Código HTTP (se via API): ___ (esperado: 422)

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 3. Cenário V-M5-03 — Conflito de Idempotência (Seção 3.1)

**Critérios:** AC-M5-005  
**Objetivo:** Verificar que reenviar com a mesma chave mas valor diferente é rejeitado.

**Pré-condições:**
- Pagamento já registrado com chave `idem-conflict-001`, valor R$ 100,00.

**Passos na interface:**
1. Abra a venda → clique em "Registrar Pagamento".
2. Preencha: método `PIX`, valor `150.00`, chave de idempotência `idem-conflict-001`.
3. Clique em "Registrar".

**Resultado esperado:**
- O sistema rejeita com erro de conflito (**HTTP 409** — business rule).
- Mensagem de erro visível na interface.
- O total pago permanece inalterado.

**Evidência a registrar:**
- Mensagem de erro: ___
- Total pago antes: R$ ___ | Total pago depois: R$ ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 4. Cenário V-M5-04 — Múltiplos Pagamentos (Seção 3.2)

**Critérios:** AC-M5-006, AC-M5-007, AC-M5-039  
**Objetivo:** Verificar que múltiplos pagamentos com chaves distintas somam corretamente.

**Pré-condições:** Venda em `RASCUNHO` com total R$ 200,00 e pagamento de R$ 100,00 já registrado.

**Passos na interface:**
1. Abra a venda → clique em "Registrar Pagamento".
2. Preencha: método `CARTAO`, valor `50.00`, chave `idem-multi-002`.
3. Clique em "Registrar".
4. Verifique o resumo de pagamentos.

**Resultado esperado:**
- Total pago: R$ 150,00.
- Valor restante: R$ 50,00.
- Histórico mostra 2 registros distintos.

**Evidência a registrar:**
- Total pago exibido: R$ ___
- Valor restante exibido: R$ ___
- Número de registros no histórico: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 5. Cenário V-M5-05 — Pagamento Excedente Rejeitado (Seção 3.2b)

**Critérios:** AC-M5-041  
**Objetivo:** Verificar que pagamento que excede o total da venda é rejeitado.

**Pré-condições:** Venda com total R$ 200,00 e total pago R$ 180,00.

**Passos na interface:**
1. Abra a venda → clique em "Registrar Pagamento".
2. Preencha: método `PIX`, valor `30.00` (excede o restante de R$ 20,00).
3. Clique em "Registrar".

**Resultado esperado:**
- O sistema rejeita com **HTTP 409** (business rule).
- Mensagem de erro: "O pagamento de R$30.00 excede o valor restante de R$20.00. Total da venda: R$200.00. Total pago: R$180.00."
- Nenhum pagamento é registrado.
- Total pago permanece R$ 180,00.

**Evidência a registrar:**
- Mensagem de erro: ___
- Total pago após tentativa: R$ ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 6. Cenário V-M5-06 — Pagamento Exato Aceito (Seção 3.2c)

**Critérios:** AC-M5-042  
**Objetivo:** Verificar que pagamento que completa exatamente o saldo restante é aceito.

**Pré-condições:** Venda com total R$ 200,00 e total pago R$ 180,00 (restante R$ 20,00).

**Passos na interface:**
1. Abra a venda → clique em "Registrar Pagamento".
2. Preencha: método `PIX`, valor `20.00`.
3. Clique em "Registrar".

**Resultado esperado:**
- Pagamento registrado com sucesso.
- Total pago: R$ 200,00.
- Valor restante: R$ 0,00.
- Barra de progresso atinge 100%.

**Evidência a registrar:**
- Total pago: R$ ___
- Valor restante: R$ ___
- Percentual exibido: ___%

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 7. Cenário V-M5-07 — Confirmação com Limiar Não Atingido (Seção 3.4)

**Critérios:** AC-M5-010  
**Objetivo:** Verificar que confirmação é bloqueada quando o pagamento é inferior a 50%.

**Pré-condições:**
- Venda em `RASCUNHO` com total R$ 200,00.
- Pagamento registrado: R$ 99,00 (49,5%).
- Dados de entrega completos em todas as cestas.

**Passos na interface:**
1. Abra a venda.
2. Clique em "Confirmar Venda".

**Resultado esperado:**
- Confirmação rejeitada com **HTTP 409** (business rule).
- Mensagem de erro: "Pagamento insuficiente para confirmação. Total pago: R$99.00 (49.5% de R$200.00). Mínimo requerido: 50%."
- Venda permanece em `RASCUNHO`.
- Pagamento de R$ 99,00 permanece registrado.

**Evidência a registrar:**
- Status da venda após tentativa: ___
- Mensagem de erro: ___
- Total pago preservado: R$ ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 8. Cenário V-M5-08 — Confirmação com Dados de Entrega Incompletos (Seção 3.6)

**Critérios:** AC-M5-011  
**Objetivo:** Verificar que confirmação é bloqueada quando alguma cesta não tem dados de entrega.

**Pré-condições:**
- Venda em `RASCUNHO` com pagamento ≥ 50%.
- Pelo menos uma cesta sem destinatário, endereço, data ou hora de entrega.

**Passos na interface:**
1. Abra a venda.
2. Verifique que uma cesta mostra "—" nos campos de entrega.
3. Clique em "Confirmar Venda".

**Resultado esperado:**
- Confirmação rejeitada com **HTTP 409** (business rule).
- Mensagem de erro: "Todas as cestas devem possuir destinatário, endereço, data e horário de entrega preenchidos para confirmação."
- Venda permanece em `RASCUNHO`.

**Evidência a registrar:**
- Status da venda: ___
- Mensagem de erro: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 9. Cenário V-M5-09 — Reserva sem Baixa Física (Seção 4.1)

**Critérios:** AC-M5-015  
**Objetivo:** Confirmar que a confirmação cria reservas sem reduzir o estoque físico.

**Pré-condições:**
- Produto de teste com saldo conhecido (ex.: "Tomate - Validação M5", saldo = 50 unidades).
- Venda em `RASCUNHO` com 1 cesta contendo 5 unidades de Tomate.
- Pagamento ≥ 50% registrado.
- Dados de entrega completos.

**Passos na interface:**
1. Consulte o saldo do produto via API: `GET /api/v1/products/{product_id}/inventory/balance`.
2. Registre o saldo antes: ___
3. Abra a venda → clique em "Confirmar Venda".
4. Verifique que a venda passou para `CONFIRMADA`.
5. Consulte novamente o saldo do produto via API.

**Resultado esperado:**
- Status da venda: `CONFIRMADA`.
- Saldo do produto inalterado (50 unidades).
- Reservas criadas (verificável via inspeção do banco).

**Evidência a registrar:**
- Saldo antes: ___ | Saldo depois: ___
- Status da venda: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 10. Cenário V-M5-10 — Baixa Física no Início da Preparação (Seção 4.2)

**Critérios:** AC-M5-016, AC-M5-017  
**Objetivo:** Verificar que iniciar a preparação cria as baixas físicas e reduz o estoque.

**Pré-condições:**
- Venda em `CONFIRMADA` com reservas ativas (ex.: 5 unidades de "Tomate - Validação M5").
- Saldo do Tomate antes: 50 unidades.

**Passos na interface:**
1. Abra a venda → clique em "Iniciar Preparação".
2. Verifique que a venda passou para `EM PREPARAÇÃO`.
3. Consulte o saldo do Tomate via API: `GET /api/v1/products/{product_id}/inventory/balance`.

**Resultado esperado:**
- Status da venda: `EM PREPARAÇÃO`.
- Saldo do Tomate reduzido: 45 unidades.
- Movimentação `OUTPUT` criada (verificável via `GET /api/v1/products/{product_id}/inventory/movements`).

**Evidência a registrar:**
- Status da venda: ___
- Saldo antes: ___ | Saldo depois: ___
- Tipo da movimentação mais recente: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 11. Cenário V-M5-11 — Baixa Física Atômica (Seção 4.3)

**Critérios:** AC-M5-017  
**Objetivo:** Verificar que se o estoque for insuficiente para um produto, nenhuma baixa parcial ocorre.

**⚠️ CENÁRIO NÃO EXECUTÁVEL MANUALMENTE COM SEGURANÇA**

**Justificativa:** Para reproduzir a situação de estoque insuficiente em um produto durante a preparação, seria necessário reduzir o estoque físico abaixo das reservas ativas. Contudo, a regra de cobertura de reservas (`inventory/service.py`, linhas 193–199) rejeita ajustes negativos quando o saldo resultante fica abaixo das reservas ativas:

> "Ajuste rejeitado: estoque físico insuficiente para cobrir reservas ativas."

Criar uma segunda venda `CONFIRMADA` que reserve o mesmo produto também não é viável, pois a confirmação exige estoque reservável (saldo − reservas ativas ≥ quantidade necessária). Assim, não é possível preparar um cenário reproduzível e seguro via fluxo normal da aplicação que leve a preparação a falhar por estoque insuficiente — a própria reserva na confirmação impede que uma venda seja confirmada sem estoque suficiente.

**Cobertura automatizada:** Este cenário é coberto pelo teste `test_preparation_start_rollback_on_insufficient_stock()` em `test_m5_concurrency.py`, que prepara o estado diretamente no banco de dados.

**Resultado:** ☐ Bloqueado — não executável manualmente (coberto por teste automatizado)  
**Observações:** A atomicidade da preparação é garantida pela transação do banco de dados e pelo teste automatizado dedicado.

---

## 12. Cenário V-M5-12 — Entrega sem Movimentação de Estoque (Seção 4.4)

**Critérios:** AC-M5-018  
**Objetivo:** Verificar que registrar a entrega de uma cesta não cria movimentação de estoque.

**Pré-condições:**
- Venda em `EM PREPARAÇÃO` com pelo menos uma cesta marcada como preparada.
- Saldo do produto de teste registrado antes da entrega.

**Passos na interface:**
1. Abra a venda.
2. Na cesta preparada, clique em "Registrar Entrega".
3. Preencha o nome do operador e confirme.

**Via API (alternativa):**
```bash
curl -X POST http://localhost:8000/api/v1/sales/{sale_id}/baskets/{basket_id}/deliver \
  -H "Content-Type: application/json" \
  -d '{"operator_name": "validador"}'
```

**Resultado esperado:**
- Cesta marcada como "Entregue".
- Saldo do produto inalterado.
- Nenhuma nova movimentação de estoque criada.

**Evidência a registrar:**
- Status da cesta: ___
- Saldo antes: ___ | Saldo depois: ___
- Número de movimentações antes: ___ | Depois: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 13. Cenário V-M5-13 — Adição com Reserva de Diferença (Seção 5.1)

**Critérios:** AC-M5-019  
**Objetivo:** Verificar que alterar a composição de uma cesta em uma venda confirmada reserva a diferença.

**⚠️ IMPORTANTE — Semântica de edição de composição:** A operação `PUT /sales/{id}/baskets/{id}/composition` **substitui integralmente** a lista de itens da cesta — não é uma adição incremental. Se a cesta original tem `[Produto A: 5]` e o payload envia `[Produto B: 10]`, o Produto A é removido e o Produto B é adicionado.

**⚠️ IMPORTANTE — `confirmed_warning`:** Quando a venda está `CONFIRMADA` ou `EM_PREPARAÇÃO`, o campo `confirmed_warning` deve ser `true`, caso contrário o serviço rejeita com HTTP 409.

**Pré-condições:**
- Venda em `CONFIRMADA` com 1 cesta contendo produto de teste.
- Estoque suficiente para o produto adicional.

**Passos via API:**
```bash
curl -X PUT http://localhost:8000/api/v1/sales/{sale_id}/baskets/{basket_id}/composition \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": {produto_id}, "quantity": 10}], "operator_name": "validador", "confirmed_warning": true}'
```

**Resultado esperado:**
- Composição substituída com sucesso (HTTP 200).
- Reserva da diferença criada ou ampliada.

**Evidência a registrar:**
- Status HTTP: ___
- Composição atualizada: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ⚠️ Este cenário requer chamada direta à API — não há UI para edição de composição em vendas confirmadas.

---

## 14. Cenário V-M5-14 — Adição Rejeitada sem Estoque (Seção 5.2)

**Critérios:** AC-M5-020  
**Objetivo:** Verificar que alterar a composição para incluir produto sem estoque suficiente é rejeitada.

**Pré-condições:**
- Venda em `CONFIRMADA`.
- Produto de teste com saldo 3 unidades; tentativa de alterar composição para 10 unidades.

**Passos via API:**
```bash
curl -X PUT http://localhost:8000/api/v1/sales/{sale_id}/baskets/{basket_id}/composition \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": {produto_id}, "quantity": 10}], "operator_name": "validador", "confirmed_warning": true}'
```

**Resultado esperado:**
- HTTP 409 — rejeição.
- Composição inalterada.
- Reserva inalterada.

**Evidência a registrar:**
- Status HTTP: ___
- Mensagem de erro: ___
- Composição inalterada: ☐ Sim ☐ Não

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ⚠️ Requer chamada direta à API.

---

## 15. Cenário V-M5-15 — Redução com Liberação de Reserva (Seção 5.3)

**Critérios:** AC-M5-021  
**Objetivo:** Verificar que reduzir a quantidade libera apenas as quantidades ainda reservadas (não consumidas).

**Pré-condições:**
- Venda em `CONFIRMADA` (antes da preparação) com cesta contendo 10 unidades de produto de teste.
- Reserva ativa de 10 unidades.

**Passos via API:**
```bash
curl -X PUT http://localhost:8000/api/v1/sales/{sale_id}/baskets/{basket_id}/composition \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": {produto_id}, "quantity": 5}], "operator_name": "validador", "confirmed_warning": true}'
```

**Resultado esperado:**
- Composição atualizada para 5 unidades.
- Reserva reduzida de 10 para 5 unidades.
- Nenhuma entrada de estoque criada para as 5 unidades liberadas.

**Evidência a registrar:**
- Quantidade na composição: ___
- Reserva ativa: ___
- Movimentações ENTRY criadas: ☐ Sim ☐ Não

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ⚠️ Requer chamada direta à API.

---

## 16. Cenário V-M5-16 — Remoção sem Entrada Física (Seção 5.4)

**Critérios:** AC-M5-022  
**Objetivo:** Verificar que remover um item da composição não gera entrada de estoque automática.

**⚠️ IMPORTANTE — Remoção por omissão:** O schema `SaleBasketItemInput` valida `quantity > 0`. **Não é possível remover um item enviando `quantity: 0`** — o schema rejeita com HTTP 422. A remoção é feita **omitindo o produto da lista de itens**.

**Pré-condições:**
- Venda em `CONFIRMADA` com cesta contendo produto de teste.
- Saldo do produto registrado antes.

**Passos via API:**
```bash
# Remover o produto da composição (omitir o item da lista)
curl -X PUT http://localhost:8000/api/v1/sales/{sale_id}/baskets/{basket_id}/composition \
  -H "Content-Type: application/json" \
  -d '{"items": [], "operator_name": "validador", "confirmed_warning": true}'
```

**Resultado esperado:**
- Produto removido da composição.
- Reserva liberada (status `RELEASED`).
- Nenhuma movimentação `ENTRY` criada.
- Saldo do produto inalterado.

**Evidência a registrar:**
- Produto na composição: ☐ Presente ☐ Removido
- Saldo antes: ___ | Saldo depois: ___
- Movimentações ENTRY criadas: ☐ Sim ☐ Não

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ⚠️ Requer chamada direta à API.

---

## 17. Cenário V-M5-17 — Reabertura sem Repetição de Baixas (Seção 6.1)

**Critérios:** AC-M5-023  
**Objetivo:** Verificar que reabrir uma venda `PRONTA` não repete as baixas físicas.

**Pré-condições:**
- Venda em `PRONTA` (todas as cestas preparadas, baixas físicas já realizadas).
- ⚠️ Para atingir o status `PRONTA`, todas as cestas da venda devem ser marcadas como preparadas. A transição `EM_PREPARAÇÃO → PRONTA` ocorre automaticamente quando todas as cestas são preparadas.
- Saldo do produto de teste registrado antes.

**Passos na interface:**
1. Abra a venda (status `PRONTA`).
2. Clique em "Reabrir Venda".
3. Preencha motivo e nome do operador.
4. Confirme.

**Via API (alternativa):**
```bash
curl -X POST http://localhost:8000/api/v1/sales/{sale_id}/reopen \
  -H "Content-Type: application/json" \
  -d '{"reason": "Validação M5", "operator_name": "validador"}'
```

**Resultado esperado:**
- Venda passa para `EM PREPARAÇÃO`.
- Saldo do produto inalterado (nenhuma nova baixa).
- Histórico de reaberturas registrado.

**Evidência a registrar:**
- Status da venda: ___
- Saldo antes: ___ | Saldo depois: ___
- Nova movimentação OUTPUT criada: ☐ Sim ☐ Não

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 18. Cenário V-M5-18 — Cancelamento antes da Preparação (Seção 7.1)

**Critérios:** AC-M5-024  
**Objetivo:** Verificar que cancelar uma venda `CONFIRMADA` libera as reservas sem criar movimentações físicas.

**Pré-condições:**
- Venda em `CONFIRMADA` com reservas ativas.
- Saldo do produto de teste registrado antes.

**Passos na interface:**
1. Abra a venda.
2. Clique em "Cancelar Venda".

**Resultado esperado:**
- Venda passa para `CANCELADA`.
- Reservas liberadas (status `RELEASED`).
- Nenhuma movimentação física criada.
- Saldo do produto inalterado.

**Evidência a registrar:**
- Status da venda: ___
- Saldo antes: ___ | Saldo depois: ___
- Reservas liberadas: ☐ Sim ☐ Não

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 19. Cenário V-M5-19 — Cancelamento após Preparação (Seção 7.2)

**Critérios:** AC-M5-025  
**Objetivo:** Verificar que cancelar uma venda `EM PREPARAÇÃO` cria registros de inspeção para os produtos baixados.

**Pré-condições:**
- Venda em `EM PREPARAÇÃO` com baixas físicas registradas.

**Passos na interface:**
1. Abra a venda.
2. Clique em "Cancelar Venda".

**Resultado esperado:**
- Venda passa para `CANCELADA`.
- Registros de inspeção criados com estado `PENDING`.
- Reservas remanescentes liberadas.

**Verificação via API:**
```bash
curl http://localhost:8000/api/v1/sales/{sale_id}/inspections
```

**Resultado esperado da API:**
- Lista de inspeções com estado `PENDING`.

**Evidência a registrar:**
- Status da venda: ___
- Número de inspeções criadas: ___
- Estado das inspeções: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 20. Cenário V-M5-20 — Inspeção de Produtos Cancelados (Seção 7.3)

**Critérios:** AC-M5-026  
**Objetivo:** Verificar que registrar a inspeção atualiza o estado de `PENDING` para `INSPECTED`.

**Pré-condições:**
- Venda `CANCELADA` com inspeção em estado `PENDING`.
- `inspection_id` conhecido.

**Passos via API:**
```bash
curl -X POST http://localhost:8000/api/v1/sales/{sale_id}/inspections/{inspection_id}/record \
  -H "Content-Type: application/json" \
  -d '{"inspected_quantity": 5, "reusable_quantity": 3, "operator_name": "validador"}'
```

**Resultado esperado:**
- HTTP 200.
- Estado da inspeção: `INSPECTED`.
- `reusable_quantity`: 3.

**Evidência a registrar:**
- Status HTTP: ___
- Estado da inspeção: ___
- reusable_quantity: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ⚠️ Requer chamada direta à API — não há UI para inspeção.

---

## 21. Cenário V-M5-21 — Reintegração (Seção 7.4)

**Critérios:** AC-M5-027, AC-M5-028  
**Objetivo:** Verificar que reintegrar a quantidade aproveitável cria ENTRY e que a reintegração duplicada é rejeitada.

**Pré-condições:**
- Inspeção em estado `INSPECTED` com `reusable_quantity` = 3.
- Saldo do produto de teste registrado antes.

**Passos via API:**
```bash
# 1. Reintegrar a quantidade
curl -X POST http://localhost:8000/api/v1/sales/{sale_id}/inspections/{inspection_id}/reintegrate \
  -H "Content-Type: application/json" \
  -d '{"quantity": 3, "operator_name": "validador"}'

# 2. Tentar reintegrar novamente (deve falhar)
curl -X POST http://localhost:8000/api/v1/sales/{sale_id}/inspections/{inspection_id}/reintegrate \
  -H "Content-Type: application/json" \
  -d '{"quantity": 3, "operator_name": "validador"}'
```

**Resultado esperado:**
- Primeira chamada: HTTP 200, estado `REINTEGRATED`, movimentação `ENTRY` criada.
- Segunda chamada: HTTP 409, reintegração duplicada rejeitada.
- Saldo do produto aumentado em 3 unidades após a primeira reintegração.

**Evidência a registrar:**
- Status HTTP 1ª chamada: ___
- Status HTTP 2ª chamada: ___
- Estado da inspeção: ___
- Saldo antes: ___ | Saldo depois: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ⚠️ Requer chamada direta à API.

---

## 22. Cenário V-M5-22 — Cancelamento Bloqueado após Entrega (Seção 7.5)

**Critérios:** AC-M5-029  
**Objetivo:** Verificar que o botão "Cancelar Venda" não aparece quando há cesta entregue.

**Pré-condições:**
- Venda com pelo menos uma cesta entregue.

**Passos na interface:**
1. Abra a venda.
2. Verifique os botões disponíveis na barra de ações.

**Resultado esperado:**
- Botão "Cancelar Venda" não visível.
- A venda não pode ser cancelada pela interface.

**Evidência a registrar:**
- Botão "Cancelar Venda" visível: ☐ Sim ☐ Não

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 23. Cenário V-M5-23 — Ajuste Rejeitado quando Viola Cobertura (Seção 9.1)

**Critérios:** AC-M5-030  
**Objetivo:** Verificar que ajuste negativo é rejeitado quando o saldo resultante fica abaixo das reservas ativas.

**Pré-condições:**
- Produto de teste com saldo 10 unidades.
- Reserva ativa de 5 unidades (venda `CONFIRMADA`).

**Passos via API:**
```bash
# Tentar ajustar -6 (saldo resultante seria 4, abaixo das 5 reservas)
curl -X POST http://localhost:8000/api/v1/products/{product_id}/inventory/adjustments \
  -H "Content-Type: application/json" \
  -d '{"quantity": -6}'
```

**⚠️ Atenção:** O schema `AdjustmentRequest` contém apenas `quantity` e tem `extra="forbid"`. **Não incluir `operator_name`** no payload — será rejeitado com HTTP 422.

**Resultado esperado:**
- HTTP 409 — rejeição.
- Mensagem: "Ajuste rejeitado: estoque físico insuficiente para cobrir reservas ativas. Saldo resultante: 4, reservas ativas: 5."
- Saldo inalterado: 10 unidades.

**Evidência a registrar:**
- Status HTTP: ___
- Saldo após tentativa: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ⚠️ Requer chamada direta à API — não há UI para ajustes de estoque.

---

## 24. Cenário V-M5-24 — Ajuste Permitido dentro da Cobertura (Seção 9.2)

**Critérios:** AC-M5-031  
**Objetivo:** Verificar que ajuste negativo é permitido quando o saldo resultante ainda cobre as reservas.

**Pré-condições:**
- Produto de teste com saldo 10 unidades.
- Reserva ativa de 5 unidades.

**Passos via API:**
```bash
# Ajustar -4 (saldo resultante seria 6, acima das 5 reservas)
curl -X POST http://localhost:8000/api/v1/products/{product_id}/inventory/adjustments \
  -H "Content-Type: application/json" \
  -d '{"quantity": -4}'
```

**⚠️ Atenção:** O schema `AdjustmentRequest` contém apenas `quantity` e tem `extra="forbid"`. **Não incluir `operator_name`** no payload.

**Resultado esperado:**
- HTTP 201 — aceito.
- Saldo atualizado para 6 unidades.

**Evidência a registrar:**
- Status HTTP: ___
- Saldo após ajuste: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ⚠️ Requer chamada direta à API.

---

## 25. Cenário V-M5-25 — Pagamento com Método Inválido (Seção 3.1, cenário negativo)

**Critérios:** AC-M5-003  
**Objetivo:** Verificar que métodos `DINHEIRO` e `OUTRO` são rejeitados.

**Pré-condições:** Venda em `RASCUNHO` ou `CONFIRMADA`.

**Passos via API:**
```bash
# Tentar registrar com método DINHEIRO
curl -X POST http://localhost:8000/api/v1/sales/{sale_id}/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": "50.00", "method": "DINHEIRO", "idempotency_key": "idem-invalid-001"}'
```

**Resultado esperado:**
- **HTTP 422** — schema validation (não HTTP 409).
- Mensagem: "Método de pagamento inválido. Use um de: PIX, CARTAO"
- Nenhum pagamento registrado.

**Evidência a registrar:**
- Status HTTP: ___ (esperado: 422)
- Mensagem de erro: ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ⚠️ A UI só oferece PIX e CARTAO no `<select>`. Este teste requer chamada direta à API.

---

## 26. Cenário V-M5-26 — Comprovante Opcional (Seção 3.1)

**Critérios:** AC-M5-040  
**Objetivo:** Verificar que registrar pagamento sem comprovante é aceito.

**Pré-condições:** Venda em `RASCUNHO` ou `CONFIRMADA` com total pago < 100%.

**Passos na interface:**
1. Abra a venda → clique em "Registrar Pagamento".
2. Preencha: método `PIX`, valor `50.00`.
3. Não anexe nenhum comprovante.
4. Clique em "Registrar".

**Resultado esperado:**
- Pagamento registrado com sucesso.
- Ausência de comprovante não bloqueia.

**Evidência a registrar:**
- Mensagem de sucesso: ___
- Pagamento no histórico: ☐ Sim ☐ Não

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## 27. Cenário V-M5-27 — Confirmação com Estoque Insuficiente — Mensagem de Erro (Seção 3.5)

**Critérios:** AC-M5-014  
**Objetivo:** Verificar que a mensagem de erro identifica os produtos com insuficiência.

**Pré-condições:**
- Venda em `RASCUNHO` com pagamento ≥ 50%.
- Cesta contendo produto de teste com estoque insuficiente (ex.: "Cenoura - Validação M5", precisa 5, disponível 2).
- Dados de entrega completos.

**Passos na interface:**
1. Abra a venda.
2. Clique em "Confirmar Venda".

**Resultado esperado:**
- Confirmação rejeitada com **HTTP 409** (business rule).
- Mensagem de erro: "Estoque insuficiente para confirmação. Produtos faltantes: Cenoura - Validação M5: necessário 5 unidade"
- A mensagem identifica o produto faltante por nome, com quantidade e unidade.
- Venda permanece em `RASCUNHO`.
- Pagamento preservado.

**Evidência a registrar:**
- Mensagem de erro: ___
- Status da venda: ___
- Total pago preservado: R$ ___

**Resultado:** ☐ Aprovado ☐ Reprovado ☐ Bloqueado  
**Observações:** ___

---

## Resumo dos Cenários

| ID | Seção | Critérios | Método | Status |
|----|-------|-----------|--------|--------|
| V-M5-01 | 3.1 | AC-M5-004, 005 | UI | ☐ Pendente |
| V-M5-02 | 3.1 | AC-M5-002 | UI | ☐ Pendente |
| V-M5-03 | 3.1 | AC-M5-005 | UI | ☐ Pendente |
| V-M5-04 | 3.2 | AC-M5-006, 007, 039 | UI | ☐ Pendente |
| V-M5-05 | 3.2b | AC-M5-041 | UI | ☐ Pendente |
| V-M5-06 | 3.2c | AC-M5-042 | UI | ☐ Pendente |
| V-M5-07 | 3.4 | AC-M5-010 | UI | ☐ Pendente |
| V-M5-08 | 3.6 | AC-M5-011 | UI | ☐ Pendente |
| V-M5-09 | 4.1 | AC-M5-015 | UI + API | ☐ Pendente |
| V-M5-10 | 4.2 | AC-M5-016, 017 | UI + API | ☐ Pendente |
| V-M5-11 | 4.3 | AC-M5-017 | **Bloqueado** | ☐ Bloqueado |
| V-M5-12 | 4.4 | AC-M5-018 | UI + API | ☐ Pendente |
| V-M5-13 | 5.1 | AC-M5-019 | API | ☐ Pendente |
| V-M5-14 | 5.2 | AC-M5-020 | API | ☐ Pendente |
| V-M5-15 | 5.3 | AC-M5-021 | API | ☐ Pendente |
| V-M5-16 | 5.4 | AC-M5-022 | API | ☐ Pendente |
| V-M5-17 | 6.1 | AC-M5-023 | UI + API | ☐ Pendente |
| V-M5-18 | 7.1 | AC-M5-024 | UI | ☐ Pendente |
| V-M5-19 | 7.2 | AC-M5-025 | UI + API | ☐ Pendente |
| V-M5-20 | 7.3 | AC-M5-026 | API | ☐ Pendente |
| V-M5-21 | 7.4 | AC-M5-027, 028 | API | ☐ Pendente |
| V-M5-22 | 7.5 | AC-M5-029 | UI | ☐ Pendente |
| V-M5-23 | 9.1 | AC-M5-030 | API | ☐ Pendente |
| V-M5-24 | 9.2 | AC-M5-031 | API | ☐ Pendente |
| V-M5-25 | 3.1 | AC-M5-003 | API | ☐ Pendente |
| V-M5-26 | 3.1 | AC-M5-040 | UI | ☐ Pendente |
| V-M5-27 | 3.5 | AC-M5-014 | UI | ☐ Pendente |

**Total:** 26 cenários pendentes + 1 bloqueado = 27 cenários.

---

## Cenários Não Executáveis Manualmente

| Cenário | Motivo |
|---------|--------|
| **V-M5-11** (Baixa atômica) | Não é possível preparar estoque insuficiente após confirmação sem violar as regras de reserva e cobertura. A confirmação exige estoque reservável; o ajuste negativo é bloqueado pela regra de cobertura. Coberto por `test_preparation_start_rollback_on_insufficient_stock()`. |
| Seção 8.1 — Duas vendas concorrentes | Requer execução simultânea de requisições — não viável manualmente. Coberto por `test_two_sales_competing_for_stock`. |
| Seção 8.2 — Confirmação e ajuste concorrentes | Mesma limitação. Coberto por `test_adjustment_vs_confirmation_concurrent`. |
| Seção 8.3 — Hierarquia de locks | Requer múltiplas operações concorrentes. Coberto por `test_lock_hierarchy_no_deadlock`. |
| Seção 10 — Fronteira M4-M5 | Verificação estática de código — não é teste manual. |

---

## Consultas Úteis no Banco de Dados

Para inspeção direta das reservas e movimentações, use o cliente PostgreSQL configurado no `docker-compose.yml`.

```sql
-- Verificar reservas ativas
SELECT * FROM sale_stock_reservations WHERE sale_id = {sale_id} AND status = 'ACTIVE';

-- Verificar movimentações de estoque
SELECT * FROM inventory_movements WHERE product_id = {product_id} ORDER BY created_at DESC;

-- Verificar pagamentos
SELECT * FROM payments WHERE sale_id = {sale_id} ORDER BY created_at;

-- Verificar inspeções
SELECT * FROM sale_cancellation_inspection WHERE sale_id = {sale_id};
```

---

## Critérios de Conclusão

A validação manual do M5 considera-se concluída quando:

- [ ] Todos os cenários executáveis foram executados.
- [ ] O cenário V-M5-11 foi considerado coberto pelo teste automatizado.
- [ ] Os cenários de concorrência (seção 8) foram considerados cobertos pelos testes automatizados.
- [ ] Os resultados foram registrados neste roteiro.
- [ ] As divergências encontradas foram documentadas e comunicadas ao Product Owner.
