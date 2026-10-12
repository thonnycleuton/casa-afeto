# M5 — Resumo Executivo para Revisão

**Versão do documento:** 0.1 (RASCUNHO)
**Status:** Rascunho para revisão humana — não aprovado
**Marco:** M5 — Pagamentos, Reserva e Baixa de Estoque
**Data:** 12 de outubro de 2026

---

## Objetivo

Registrar o resultado da reconstrução documental do M5 (Pagamentos, Reserva e Baixa de Estoque), recuperando a rastreabilidade do marco conforme o padrão documental de M1–M4.

Este documento é um **RASCUNHO PARA REVISÃO**. Nenhuma decisão aqui registrada é considerada aprovada até revisão e aprovação explícita pelo Product Owner.

---

## ✅ Entregáveis do Rascunho

Os seguintes documentos foram elaborados como rascunhos e estão prontos para revisão:

1. **`executive-summary.md`** — Este documento
2. **`specification.md`** — Especificação técnica e funcional completa
3. **`use-cases.md`** — Casos de uso detalhados
4. **`acceptance-criteria.md`** — Critérios de aceitação em formato BDD
5. **`validation.md`** — Plano de validação operacional

Todos os documentos estão no diretório: `docs/milestones/m5-payments/`

---

## Visão Geral do M5

### O que M5 faz

M5 implementa o **ciclo financeiro e de estoque da venda** na Casa Afeto:

- ✅ Registrar pagamentos vinculados a uma venda
- ✅ Suportar múltiplos pagamentos por venda
- ✅ Garantir idempotência no registro de pagamentos
- ✅ Calcular total pago e verificar limiar de 50%
- ✅ Autorizar financeiramente a transição `RASCUNHO → CONFIRMADA`
- ✅ Validar dados obrigatórios de entrega antes da confirmação
- ✅ Reservar integralmente o estoque no momento da confirmação
- ✅ Executar baixa física no início da preparação
- ✅ Gerenciar alterações de composição com reserva/liberação de diferença
- ✅ Liberar reservas ao cancelar antes da preparação
- ✅ Criar inspeção de produtos baixados ao cancelar após preparação
- ✅ Reintegrar fisicamente produtos recuperados após inspeção

### O que M5 NÃO faz

M5 **explicitamente não toca em:**

- ❌ Integração com gateways de pagamento
- ❌ Conciliação bancária automática
- ❌ Verificação automática de PIX
- ❌ Processamento de cartão de crédito externo
- ❌ Reembolsos por meio de provedores externos
- ❌ Relatórios financeiros avançados

---

## Fronteira entre M4 e M5

| Responsabilidade | M4 | M5 |
|------------------|----|----|
| Criar e gerenciar vendas | ✅ | |
| Definir estados operacionais | ✅ | |
| Permitir edições conforme estado | ✅ | |
| Registrar pagamentos | | ✅ |
| Calcular total pago | | ✅ |
| Verificar limiar de 50% | | ✅ |
| **Autorizar `RASCUNHO → CONFIRMADA`** | Valida dados obrigatórios | ✅ Autoriza financeiramente |
| Reservar estoque na confirmação | | ✅ |
| Baixar fisicamente no início da preparação | | ✅ |
| Gerenciar alterações de composição com reserva | | ✅ |
| Liberar reservas no cancelamento | | ✅ |
| Inspeção e reintegração de cancelamento | | ✅ |

**Critérios de aceitação que garantem esta fronteira:**
- AC-M4-015: M4 não registra pagamentos
- AC-M4-016: M5 autoriza confirmação financeira
- AC-M4-017: Sem regra paralela de confirmação em M4
- AC-M4-018: Sem efeitos automáticos de estoque em M4

---

## Regras de Negócio Aprovadas

As regras a seguir foram aprovadas pelo Product Owner e registradas no `business-contract.md` v0.6 (seção 37), via commit `5d42959` (2026-10-11).

| Regra | Descrição |
|-------|-----------|
| RES-001 | Confirmação financeira e reserva como operação atômica |
| RES-002 | Bloqueio por estoque insuficiente |
| RES-003 | Pagamento registrado independente da confirmação |
| RES-004 | Reserva não é baixa física |
| RES-005 | Baixa física e liberação da reserva no início da preparação |
| RES-006 | Adições e aumentos exigem reserva da diferença |
| RES-007 | Reduções e remoções liberam a reserva |
| RES-008 | Quantidades já baixadas não geram entradas automáticas |
| RES-009 | Reabertura não repete baixas |
| RES-010 | Cancelamento antes da preparação libera reservas |
| RES-011 | Cancelamento após preparação exige inspeção |
| RES-012 | Proibição de cancelamento com entrega |

Além disso, as regras `PAY-001` e `PAY-002` do contrato de negócio definem que:
- Pagamentos pertencem ao M5.
- O limiar de confirmação é 50% do valor total da venda.

---

## Conceitos Fundamentais

### Pagamento

Um pagamento é um registro de valor recebido para uma venda. Cada pagamento possui:

- Valor (sempre positivo)
- Método de pagamento (`PIX` ou `CARTAO`)
- Chave de idempotência para evitar duplicação

**Decisão aprovada:** Somente `PIX` e `CARTAO` são aceitos em M5. `DINHEIRO` e `OUTRO` são rejeitados.

**⚠️ DIVERGÊNCIA COM IMPLEMENTAÇÃO:** O código atual suporta `DINHEIRO` e `OUTRO`. Esta discrepância deve ser corrigida no código.

Múltiplos pagamentos podem ser registrados para a mesma venda. O total pago é a soma de todos os pagamentos registrados.

### Comprovante de Pagamento

O `phase-1.md` inclui "comprovante de pagamento, quando aplicável" no escopo do M5.

**Decisão aprovada:** O comprovante de pagamento é opcional para `PIX` e `CARTAO`. A ausência de comprovante não pode bloquear o registro do pagamento.

**⚠️ PENDÊNCIA:** Os formatos aceitos, o método de armazenamento e as validações técnicas de comprovante não foram definidos.

### Valor Restante

O `phase-1.md` inclui "valor restante, quando aplicável ao fluxo financeiro aprovado" no escopo do M5. O valor restante é a diferença entre o valor total da venda e o total pago.

**Decisão aprovada:** O sistema rejeita qualquer novo pagamento que faça a soma dos pagamentos registrados ultrapassar o total da venda. O valor restante não pode ficar negativo. Não criar crédito ou reembolso automático.

### Reserva de Estoque

A reserva aloca logicamente as quantidades necessárias dos produtos da venda, impedindo que sejam reservadas para outras vendas. A reserva **não é baixa física** — o saldo de estoque permanece inalterado enquanto os produtos estiverem apenas reservados.

### Baixa Física

A baixa física é a dedução real do saldo de estoque, registrada como movimentação de estoque. Ocorre no início da preparação (`CONFIRMADA → EM PREPARAÇÃO`).

**⚠️ DECISÃO TÉCNICA:** O tipo específico da movimentação (`OUTPUT`) é uma decisão do desenho técnico, pendente de aprovação formal.

### Inspeção de Cancelamento

Quando uma venda é cancelada após o início da preparação, os produtos já baixados fisicamente devem ser conferidos. A inspeção registra quantos produtos foram recuperados e quantos são aproveitáveis para reintegração ao estoque.

### Reintegração

A reintegração retorna produtos fisicamente recuperados ao estoque, mediante movimentação `ENTRY` registrada. Apenas as quantidades confirmadas como aproveitáveis pela inspeção podem ser reintegradas.

---

## Fluxo Operacional do M5

```
Venda em RASCUNHO
    ↓
Registrar pagamento(s)
    ↓
Verificar: total pago ≥ 50% do valor da venda?
    ↓ Sim
Verificar: todas as cestas com dados de entrega?
    ↓ Sim
Verificar: estoque disponível para reserva integral?
    ↓ Sim
Reservar todas as quantidades + confirmar venda (atômico)
    ↓
Venda CONFIRMADA
    ↓ (ação do usuário)
Iniciar preparação: baixa física + liberação de reservas
    ↓
Venda EM PREPARAÇÃO
    ↓ (preparação concluída)
Venda PRONTA
    ↓ (entregas concluídas)
Venda ENTREGUE

Fluxos excepcionais:
• Cancelamento antes da preparação → liberar reservas
• Cancelamento após preparação → inspeção + reintegração
```

---

## ⚠️ Pendências que Exigem Decisão Humana

### 1. Comprovante de pagamento

O `phase-1.md` inclui "comprovante de pagamento, quando aplicável" no escopo do M5. A obrigatoriedade já foi definida como opcional.

**Decisão necessária:** Definir formatos aceitos, método de armazenamento e validações técnicas de comprovante.

### 1b. Pagamento excedente — validação concorrente

A rejeição de pagamento excedente foi aprovada. A implementação e a validação concorrente ainda não estão concluídas.

**Decisão necessária:** Confirmar se a implementação de rejeição de excedente com tratamento de concorrência está correta antes da validação manual.

### 2. Revisão do desenho técnico

O documento `.junie/plans/stock-reservation-technical-design.md` contém decisões técnicas detalhadas (modelo de 3 contadores, tipo OUTPUT, hierarquia de locks, tabela de inspeção) que foram implementadas sem aprovação formal.

**Decisão necessária:** Revisar e aprovar o desenho técnico ou solicitar alterações.

### 3. Necessidade de ADR

As decisões arquiteturais do M5 (novo tipo OUTPUT, nova tabela de reservas, nova tabela de inspeção, FK sale_id em inventory_movements) são mudanças estruturais significativas.

**Decisão necessária:** Confirmar se um ADR é necessário para essas decisões, conforme a convenção do repositório.

### 4. Cobertura de testes

Várias regras RES não possuem teste dedicado e direto. A cobertura existente é parcial ou indireta. Além disso, os novos critérios AC-M5-041 a AC-M5-043 (pagamento excedente) não possuem testes.

**Decisão necessária:** Confirmar se a cobertura atual é aceitável para o encerramento do marco ou se testes adicionais são exigidos.

### 5. Validação manual

Não há evidência de validação manual documentada do fluxo completo M5.

**Decisão necessária:** Realizar e documentar a validação manual antes de aprovar o marco.

### 6. Dependência em `test_m4_sales.py`

Os testes do M4 foram modificados para importar entidades M5 (`Payment`, `SaleStockReservation`, `SaleCancellationInspection`).

**Decisão necessária:** Avaliar se essa dependência é aceitável ou se os testes M4 devem ser isolados das entidades M5.

---

## Implementação Atual

A implementação M5 existe em código não commitado na working tree do repositório. Os principais componentes são:

- **Módulo de pagamentos:** `backend/app/payments/` (models, schemas, service)
- **API de pagamentos:** `backend/app/api/v1/payments.py`
- **API de inspeção:** `backend/app/api/v1/inspections.py`
- **Modelos de reserva e inspeção:** `backend/app/sales/models.py` (estendido)
- **Serviço de vendas:** `backend/app/sales/service.py` (estendido)
- **Migration:** `backend/alembic/versions/c1d2e3f4a5b6_add_payments_reservations_inspection.py`
- **Testes de concorrência:** `backend/tests/test_m5_concurrency.py`

**Atenção:** O código não foi commitado. Toda a implementação M5 reside em mudanças não rastreadas pelo Git.

---

## Referência Rápida

- **Especificação:** `docs/milestones/m5-payments/specification.md`
- **Casos de uso:** `docs/milestones/m5-payments/use-cases.md`
- **Critérios de aceitação:** `docs/milestones/m5-payments/acceptance-criteria.md`
- **Plano de validação:** `docs/milestones/m5-payments/validation.md`
- **Regras de negócio:** `docs/domain/business-contract.md` (seção 37, RES-001 a RES-012)
- **Desenho técnico:** `.junie/plans/stock-reservation-technical-design.md`
- **Fronteira M4-M5:** `docs/milestones/m4-sales/specification.md` (seção 8)
- **Escopo M5:** `docs/milestones/phase-1.md` (seção 7)

---

**Versão 0.1 — 12 de outubro de 2026**

Preparado para: Revisão humana e aprovação do Product Owner
Status: Rascunho — não aprovado
