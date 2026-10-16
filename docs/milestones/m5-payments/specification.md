# M5 — Especificação de Pagamentos, Reserva e Baixa de Estoque

**Versão do documento:** 1.0
**Status:** Aprovado
**Marco:** M5 — Pagamentos, Reserva e Baixa de Estoque
**Data:** 15 de outubro de 2026

---

## 1. Objetivo

M5 registra pagamentos de vendas e autoriza financeiramente a transição `RASCUNHO → CONFIRMADA`, conforme as regras aprovadas no contrato de negócio.

Além disso, M5 implementa a política de reserva e baixa de estoque associada às vendas, aprovada pelo Product Owner e registrada em `business-contract.md` v0.6 (seção 37, regras RES-001 a RES-012).

---

## 2. Escopo

M5 inclui:

- registro de pagamentos vinculados a uma venda;
- múltiplos pagamentos por venda;
- idempotência no registro de pagamentos;
- cálculo do total pago;
- cálculo do valor restante;
- verificação do limiar de 50% para confirmação financeira;
- validação dos dados obrigatórios de entrega antes da confirmação;
- reserva integral de estoque no momento da confirmação;
- bloqueio da confirmação quando estoque é insuficiente;
- baixa física no início da preparação;
- liberação de reservas correspondentes à baixa física;
- reserva e liberação de diferença em alterações de composição;
- baixa física adicional ao marcar cesta preparada após alteração;
- liberação de reservas ao cancelar antes da preparação;
- criação de inspeção ao cancelar após preparação;
- registro de inspeção e reintegração de produtos recuperados;
- preservação do pagamento registrado mesmo quando a confirmação falha.

---

## 3. Dependências

M5 depende de M1, M2, M3 e M4.

- **M1:** Produtos e estoque, movimentações, saldo, regra INV-006 (estoque não negativo).
- **M2:** Cestas e templates, composição, preço de venda persistido.
- **M3:** Clientes.
- **M4:** Vendas, estados operacionais, cestas da venda, preparação, entrega, cancelamento.

---

## 4. Pagamentos

### 4.1 Registro de Pagamento

Um pagamento é registrado vinculando um valor positivo a uma venda existente. Cada pagamento possui:

- **Valor:** quantidade monetária positiva com precisão de duas casas decimais.
- **Método:** tipo de pagamento utilizado.
- **Chave de idempotência:** identificador único fornecido pelo cliente para evitar duplicação.

O registro de pagamento é independente da confirmação financeira. Um pagamento pode ser registrado a qualquer momento após a criação da venda, independentemente do estado operacional da venda.

### 4.2 Métodos de Pagamento

Os métodos de pagamento aprovados para M5 são:

- `PIX`
- `CARTAO`

**Decisão aprovada:** Somente `PIX` e `CARTAO` são aceitos em M5. Os métodos `DINHEIRO` e `OUTRO` não são aceitos.

### 4.3 Múltiplos Pagamentos

Uma venda pode ter múltiplos pagamentos registrados. O total pago é a soma de todos os pagamentos da venda.

Exemplo:

```
Venda total: R$ 200,00
Pagamento 1: R$ 80,00 (PIX)
Pagamento 2: R$ 70,00 (CARTAO)
Total pago: R$ 150,00 (75%)
Valor restante: R$ 50,00 (25%)
```

### 4.4 Valor Restante

O `phase-1.md` inclui "valor restante, quando aplicável ao fluxo financeiro aprovado" no escopo do M5.

O valor restante é a diferença entre o valor total da venda e o total pago:

```
valor_restante = valor_total_da_venda - total_pago
```

**Decisão aprovada — Pagamento excedente:** O sistema rejeita qualquer novo pagamento que faça a soma dos pagamentos registrados ultrapassar o total da venda. O valor restante não pode ficar negativo. A validação deve considerar os pagamentos mais recentes e tratar adequadamente operações concorrentes. Não criar crédito ou reembolso automático.

Exemplo:

```
Venda total: R$ 200,00
Total pago: R$ 180,00
Valor restante: R$ 20,00

Tentativa de pagamento: R$ 30,00
Total resultante: R$ 210,00 (excede R$ 200,00)
→ REJEITADO

Tentativa de pagamento: R$ 20,00
Total resultante: R$ 200,00 (exato)
→ ACEITO

Tentativa de pagamento: R$ 15,00
Total resultante: R$ 195,00 (dentro do limite)
→ ACEITO
```

### 4.5 Idempotência

O registro de pagamento é idempotente: enviar a mesma chave de idempotência com os mesmos valores retorna o pagamento existente, sem criar duplicata.

Se a mesma chave for enviada com valores diferentes (valor ou método), o sistema rejeita a operação — a chave já foi consumida pelo primeiro pagamento.

Pagamentos legítimos distintos usam chaves de idempotência diferentes.

### 4.6 Pagamento Independente da Confirmação

Um pagamento registrado permanece registrado mesmo quando a venda não pode ser confirmada financeiramente. Pagamento e confirmação são conceitos distintos.

Se a confirmação falhar por falta de estoque, o pagamento recebido continua registrado e visível.

---

## 5. Confirmação Financeira

### 5.1 Condições para Confirmação

A transição `RASCUNHO → CONFIRMADA` exige que **todas** as condições a seguir sejam satisfeitas simultaneamente:

1. **Limiar financeiro:** o total pago deve ser pelo menos 50% do valor total da venda.
2. **Dados de entrega:** todas as cestas da venda devem ter destinatário, endereço, data e horário de entrega preenchidos.
3. **Estoque disponível:** todos os produtos necessários devem ter estoque suficiente para reserva integral.

Se qualquer condição falhar, a confirmação é rejeitada e a venda permanece em `RASCUNHO`.

### 5.2 Operação Atômica

A confirmação financeira e a reserva de estoque constituem uma única operação atômica:

1. Verificar pagamento ≥ 50%.
2. Verificar disponibilidade integral de todos os produtos.
3. Reservar todas as quantidades necessárias.
4. Efetivar a confirmação (`RASCUNHO → CONFIRMADA`).

Se qualquer etapa falhar, nenhuma mudança é persistida — a venda permanece em `RASCUNHO` e nenhuma reserva é criada.

### 5.3 Bloqueio por Estoque Insuficiente

Se faltar estoque para reservar integralmente os produtos da venda, a confirmação é bloqueada. O sistema informa quais produtos e quantidades estão faltantes.

O pagamento recebido permanece registrado, mas a venda não é confirmada e nenhuma reserva é criada.

### 5.4 Exemplo de Limiar

```
Total da venda: R$ 200,00
Pagamento registrado: R$ 100,00
                    ↓
100 / 200 = 50% → confirmação autorizada (se estoque disponível)

Pagamento registrado: R$ 99,00
                    ↓
99 / 200 = 49,5% → confirmação bloqueada
```

---

## 6. Reserva de Estoque

### 6.1 Conceito

A reserva de estoque aloca logicamente as quantidades necessárias dos produtos da venda, impedindo que sejam reservadas para outras vendas.

A reserva **não é baixa física**. O saldo de estoque físico permanece inalterado enquanto os produtos estiverem apenas reservados.

### 6.2 Disponibilidade para Reserva

A disponibilidade de um produto para reserva é calculada como:

```
disponível = saldo_físico - reservas_ativas

onde:
  saldo_físico = soma de todas as movimentações do produto
  reservas_ativas = soma de (reservado - consumido) de todas as reservas ativas do produto
```

### 6.3 Reserva Integral

A reserva é sempre integral: se um produto não puder ser reservado na quantidade necessária, nenhuma quantidade é reservada. Não há reservas parciais.

### 6.4 Estado da Reserva

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** Os estados abaixo são uma decisão do desenho técnico, não uma regra de negócio aprovada. Consulte a seção 13 para detalhes.

Cada reserva possui um estado:

- **ACTIVE:** reserva ativa; pode ter quantidades consumidas (baixadas fisicamente).
- **RELEASED:** reserva liberada; nada resta para consumir.
- **CONSUMED:** reserva totalmente consumida; quantidades reservadas e consumidas são iguais.

---

## 7. Baixa Física

### 7.1 Início da Preparação

No início da preparação (`CONFIRMADA → EM PREPARAÇÃO`), o sistema executa atomicamente:

1. A baixa física das quantidades necessárias de todos os produtos da venda, registrada como movimentação de estoque.
2. A liberação das reservas correspondentes, pois as quantidades baixadas fisicamente deixam de estar reservadas.

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** O tipo específico da movimentação (`OUTPUT`) é uma decisão do desenho técnico. Consulte a seção 13 para detalhes.

O estoque físico é atualizado por movimentações registradas, sem permitir saldo físico negativo.

Se a operação falhar, não há baixa parcial nem atualização parcial das reservas — toda a transação é revertida.

### 7.2 Entrega Não Move Estoque

A entrega subsequente de cestas não executa nova movimentação de estoque. A baixa física ocorre apenas no início da preparação.

### 7.3 Baixa Adicional por Alteração de Composição

Quando a composição de uma cesta é alterada durante `EM PREPARAÇÃO` e a cesta é marcada como preparada, a baixa física das quantidades adicionais reservadas ocorre nesse momento, atomicamente com a liberação das reservas correspondentes.

Se a baixa física falhar ou não houver estoque físico suficiente, a cesta não pode ser marcada como preparada e não pode ocorrer baixa parcial nem atualização parcial das reservas.

Quantidades já baixadas fisicamente em etapas anteriores nunca podem ser baixadas novamente.

---

## 8. Alterações de Composição com Reserva

### 8.1 Adições e Aumentos

Adições de itens e aumentos de quantidade em uma venda com reserva ou baixa ativa exigem disponibilidade e reserva atômica somente da diferença de quantidades.

Se não houver estoque suficiente para a diferença, a alteração é rejeitada sem modificar a composição ou a reserva existentes.

Três situações são distinguidas:

- **Quantidades ainda reservadas:** produtos reservados mas ainda não baixados fisicamente. Adições reservam a diferença; a baixa física ocorre quando o operador marca explicitamente como preparada a cesta cuja composição foi alterada.
- **Quantidades já baixadas fisicamente:** produtos cuja baixa física já foi registrada. Adições de quantidade reservam a diferença, mas não alteram as quantidades já baixadas.
- **Baixa física de quantidades adicionais:** quando uma adição ou aumento é reservado após o início da preparação, a baixa física da diferença ocorre quando o operador marca explicitamente como preparada a cesta cuja composição foi alterada.

### 8.2 Reduções e Remoções

Reduções de quantidade e remoções de itens liberam somente as quantidades ainda reservadas, sem gerar movimentação física fictícia.

A remoção ou redução de quantidades já baixadas fisicamente não gera entrada automática de estoque. Quantidades já baixadas fisicamente não são liberadas por redução ou remoção — não geram entradas automáticas de estoque nem são consideradas recuperadas por inferência.

### 8.3 Quantidades Já Baixadas

Quantidades já baixadas fisicamente não geram entradas automáticas de estoque por alterações de composição. Qualquer reintegração exige confirmação física e movimentação registrada.

---

## 9. Reabertura

### 9.1 Sem Repetição de Baixas

A reabertura de uma venda `PRONTA` para `EM PREPARAÇÃO` não repete baixas físicas já realizadas durante a preparação anterior.

Quantidades já baixadas fisicamente nunca podem ser baixadas novamente.

---

## 10. Cancelamento

### 10.1 Cancelamento Antes da Preparação

O cancelamento antes do início da preparação distingue dois estados:

- **`RASCUNHO`:** a venda não possui reserva, pois a reserva é criada apenas na confirmação. O cancelamento muda o estado para `CANCELADA` sem efeito no estoque.
- **`CONFIRMADA`:** a venda possui reserva ativa. O cancelamento libera integralmente a reserva sem movimentação física fictícia.

Em ambos os casos, os pagamentos registrados são preservados.

### 10.2 Cancelamento Após o Início da Preparação

No cancelamento de uma venda após o início da preparação (estados `EM PREPARAÇÃO` ou `PRONTA`):

1. As reservas remanescentes (produtos reservados mas ainda não baixados) são liberadas.
2. Exige-se conferência dos produtos já baixados fisicamente.
3. Somente as quantidades fisicamente recuperadas e aproveitáveis são reintegradas ao estoque, mediante movimentação de estoque registrada.
4. O histórico, o responsável e o motivo do cancelamento são preservados.

### 10.3 Inspeção de Cancelamento

Ao cancelar uma venda após o início da preparação, o sistema cria registros de inspeção para cada produto que teve quantidades baixadas fisicamente.

Cada registro de inspeção acompanha:

- **Quantidade consumida:** produtos que foram baixados e precisam de inspeção.
- **Quantidade inspecionada:** produtos efetivamente conferidos.
- **Quantidade aproveitável:** produtos em condições de reintegração.
- **Quantidade reintegrada:** produtos já retornados ao estoque.

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** Os estados da inspeção são uma decisão do desenho técnico, não uma regra de negócio aprovada. Consulte a seção 13 para detalhes.

Os estados da inspeção implementados são:

- **PENDING:** inspeção pendente.
- **INSPECTED:** inspeção concluída, quantidade aproveitável definida.
- **REINTEGRATED:** todos os produtos aproveitáveis foram reintegrados.
- **DISCARDED:** nenhum produto aproveitável.

### 10.4 Reintegração Física

A reintegração retorna produtos fisicamente recuperados ao estoque, mediante movimentação `ENTRY` registrada.

Apenas as quantidades confirmadas como aproveitáveis pela inspeção podem ser reintegradas. O sistema impede a reintegração duplicada — cada quantidade é reintegrada no máximo uma vez.

### 10.5 Proibição de Cancelamento com Entrega

O cancelamento de uma venda é bloqueado quando alguma cesta já tiver sido entregue.

---

## 11. Ajustes de Estoque e Cobertura de Reservas

**⚠️ DECISÃO TÉCNICA — pendente de aprovação formal.** A regra de rejeitar ajustes negativos que comprometam a cobertura de reservas é uma decisão do desenho técnico, não uma regra de negócio aprovada no `business-contract.md` nem no `phase-1.md`. Consulte a seção 13 para detalhes.

### 11.1 Verificação de Cobertura

Um ajuste negativo de estoque é rejeitado se o saldo resultante for inferior às reservas ativas do produto.

Isso impede que um ajuste manual de estoque quebre a cobertura de reservas existentes.

### 11.2 Exemplo

```
Produto: saldo = 10, reservas ativas = 8
Ajuste: -5
Saldo resultante: 5
5 < 8 → REJEITADO

Ajuste: -2
Saldo resultante: 8
8 >= 8 → PERMITIDO
```

---

## 12. Fronteira entre M4 e M5

### 12.1 Responsabilidade do M4

O M4 define a estrutura operacional da venda:

- Criação e gerenciamento de vendas.
- Estados operacionais e transições.
- Composição e preço por cesta.
- Preparação individual por cesta.
- Entrega individual por cesta.
- Reabertura auditável.
- Cancelamento com restrições.

O M4 **não** registra pagamentos, não calcula valores pagos e não implementa lógica de confirmação financeira.

### 12.2 Responsabilidade do M5

O M5 implementa:

- Registro de pagamentos.
- Cálculo do total pago.
- Verificação do limiar de 50%.
- Autorização financeira da transição `RASCUNHO → CONFIRMADA`.
- Reserva de estoque na confirmação.
- Baixa física no início da preparação.
- Gerenciamento de reservas em alterações de composição.
- Liberação de reservas no cancelamento.
- Inspeção e reintegração de cancelamento.

### 12.3 Restrições para Evitar Duplicação

- O M4 não pode efetivar a confirmação financeira independentemente do M5.
- O M4 não move estoque automaticamente.
- O M5 não altera os estados operacionais definidos pelo M4, exceto `RASCUNHO → CONFIRMADA` via autorização financeira.

---

## 13. Decisões Técnicas Documentadas

As decisões a seguir estão registradas no desenho técnico (`.junie/plans/stock-reservation-technical-design.md`) e foram implementadas. Elas **não foram formalmente aprovadas** pelo Product Owner.

### 13.1 Modelo de Três Contadores

A reserva usa três contadores independentes:

- `current_quantity`: quantidade atual necessária pelas cestas.
- `reserved_quantity`: quantidade cumulativa reservada (aumenta na reserva, diminui na liberação).
- `consumed_quantity`: quantidade cumulativa baixada fisicamente (nunca diminui).

Invariante: `consumed_quantity <= reserved_quantity`.

### 13.2 Tipo OUTPUT em InventoryMovement

Adição do tipo `OUTPUT` ao enum `MovementType` para registrar baixas físicas de vendas.

### 13.3 sale_id em InventoryMovement

Coluna opcional `sale_id` em `inventory_movements` para rastreabilidade de baixas físicas.

### 13.4 Tabela de Inspeção

Tabela dedicada `sale_cancellation_inspection` para acompanhar o ciclo de inspeção e reintegração.

### 13.5 Hierarquia de Locks

Hierarquia global de locks para prevenir deadlocks:

1. Sale row
2. Reservation rows
3. Inspection rows
4. Product rows

---

## 14. Decisões Pendentes

1. **Pagamento excedente:** ✓ Resolvido — implementação e testes concorrentes concluídos.
2. **Desenho técnico:** ✓ Decisões técnicas registradas e aprovadas no ADR-002.
3. **Regras de negócio:** As regras RES-001 a RES-012 estão documentadas em `docs/domain/business-contract.md` seção 37.
4. **Cobertura de testes:** 101 testes automatizados + 54 verificações do script API. Cobertura considerada suficiente.
5. **Validação manual:** Três cenários básicos executados com sucesso via UI. O roteiro está em `manual-validation-checklist.md`.
6. **Dependência em `test_m4_sales.py`:** Dependência puramente técnica para respeitar FKs RESTRICT. Aceitável.

---

## 15. Explicitamente Fora do Escopo

Os itens a seguir estão fora do escopo do M5 conforme `phase-1.md` §7:

- Integração com gateways de pagamento.
- Conciliação bancária automática.
- Verificação automática de PIX.
- Processamento de cartão de crédito externo.
- Reembolsos por meio de provedores externos.
- Relatórios financeiros avançados.

Os itens a seguir são **delimitações propostas**, não decisões aprovadas:

- Renegociação excepcional de preço após confirmação.
- Reembolso automático ao cancelar venda.

---

## 16. Referências do Marco

- `docs/milestones/phase-1.md` (seção 7) — Escopo M5
- `docs/domain/business-contract.md` (seção 37) — RES-001 a RES-012
- `docs/domain/business-contract.md` (seção 36) — PAY-001, PAY-002
- `docs/milestones/m4-sales/specification.md` (seção 8) — Fronteira M4-M5
- `.junie/plans/stock-reservation-technical-design.md` — Desenho técnico

---

**Versão 0.1 — 12 de outubro de 2026**

Preparado para: Em uso — M5 aprovado e Fase 1 concluída
Status: Aprovado — 15 de outubro de 2026
