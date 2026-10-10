# M4 — Plano de Validação

**Versão do documento:** 0.3
**Status:** VALIDATED — validação concluída e aceita pelo Product Owner (2026-10-10)
**Marco:** M4 — Vendas (Sales)

Este documento definiu como o M4 seria validado. A validação foi concluída com sucesso: 6 testes automatizados passaram e a validação manual foi aprovada pelo Product Owner em 2026-10-10.

---

## 1. Objetivo da validação

A validação de M4 deve confirmar que o sistema implementado reproduz o comportamento operacional aprovado para vendas, sem antecipar pagamentos, confirmação financeira independente ou movimentações automáticas de estoque.

A validação deve cobrir:

* criação e edição de vendas;
* múltiplas cestas por venda;
* cópia independente de composição e preço;
* regras de cliente e `RASCUNHO`;
* estados e transições;
* preparação individual por cesta;
* reabertura auditável;
* entregas individuais e conclusão automática da venda;
* cancelamento com preservação de histórico;
* fronteira inequívoca entre M4 e M5.

## 2. Preparação do ambiente

1. Usar ambiente de validação com dados de teste identificáveis.
2. Preparar produtos e cestas válidos de M1/M2 para servir como origem das cestas da venda.
3. Preparar clientes ativos e inativos em M3.
4. Garantir que o ambiente de validação permita observar histórico operacional e mudanças de estado.
5. Não depender de pagamentos reais, conciliação, comprovantes ou alterações automáticas de estoque para validar M4.

## 3. Validação funcional do domínio

### 3.1 Criação da venda e vínculo com cliente

Validar que:

* uma nova venda só pode ser salva com cliente ativo;
* cliente inativo não pode originar nova venda;
* uma venda em `RASCUNHO` pode ser salva com dados de entrega incompletos;
* se o cliente se tornar inativo depois da criação, o vínculo da venda existente permanece.

### 3.2 Múltiplas cestas e independência operacional

Validar que:

* uma venda pode conter várias cestas;
* várias cestas podem ser baseadas na mesma origem;
* cada cesta mantém composição, destinatário, endereço, data e horário independentes;
* a composição da origem é copiada no momento da adição;
* alterações posteriores na origem não alteram a cesta já adicionada à venda;
* alterações na cesta da venda não alteram a origem.

### 3.3 Preço e total

Validar que:

* o preço vigente da origem é copiado ao adicionar a cesta à venda;
* a inclusão da cesta na venda é bloqueada quando a origem não possui preço definido;
* o preço da cesta pode ser ajustado manualmente apenas em `RASCUNHO`;
* o total da venda corresponde à soma dos preços registrados das cestas;
* o total é recalculado quando um preço muda;
* alterar composição não recalcula automaticamente o preço acordado;
* a partir de `CONFIRMADA`, o preço fica bloqueado no fluxo normal;
* alterações futuras no preço da cesta-origem não alteram o preço já registrado no item da venda.

### 3.4 Venda persistida com ao menos uma cesta

Validar que:

* uma venda persistida contém pelo menos uma cesta;
* tentativa de salvar venda sem cestas é rejeitada de forma observável;
* essa validação não altera a regra de que uma cesta individual pode estar temporariamente vazia durante sua própria edição.

## 4. Validação dos estados e transições

Validar que os estados observáveis são exatamente:

* `RASCUNHO`
* `CONFIRMADA`
* `EM PREPARAÇÃO`
* `PRONTA`
* `ENTREGUE`
* `CANCELADA`

Validar também que:

* o fluxo normal respeita `RASCUNHO → CONFIRMADA → EM PREPARAÇÃO → PRONTA → ENTREGUE`;
* `CONFIRMADA → EM PREPARAÇÃO` exige ação explícita do usuário;
* não existe transição que permita pular etapas;
* `ENTREGUE` e `CANCELADA` se comportam como estados terminais do fluxo comercial normal;
* `PRONTA → EM PREPARAÇÃO` só ocorre por reabertura explícita e auditável.

## 5. Validação de composição por estado

### 5.1 `RASCUNHO`

Validar que a composição pode ser alterada livremente e que essas alterações não recalculam automaticamente o preço.

### 5.2 `CONFIRMADA`

Validar que é possível:

* adicionar itens;
* remover itens;
* alterar quantidades.

Confirmar também que o preço acordado continua bloqueado no fluxo normal e que não há ajuste automático de estoque.

### 5.3 `EM PREPARAÇÃO`

Validar que:

* as mesmas alterações continuam permitidas;
* a alteração exige confirmação explícita antes do salvamento;
* o aviso sobre itens já separados ou preparados é apresentado;
* a cesta alterada perde a marcação anterior de preparada;
* cestas não alteradas preservam sua preparação concluída.

### 5.4 `PRONTA`, `ENTREGUE` e `CANCELADA`

Validar que:

* `PRONTA` bloqueia alteração direta de composição até reabertura explícita;
* `ENTREGUE` bloqueia alterações comerciais de composição;
* `CANCELADA` bloqueia alterações comerciais de composição.

## 6. Validação de preparação por cesta

Validar que:

* cada cesta pode ser marcada individualmente como preparada;
* a preparação de uma cesta não equivale à entrega;
* a preparação não executa movimentação automática de estoque;
* a venda só passa para `PRONTA` quando todas as cestas estiverem preparadas;
* o progresso de preparação pode ser verificado por cesta.

## 7. Validação de reabertura e auditoria

Validar que:

* somente uma venda `PRONTA` pode ser reaberta pelo fluxo aprovado;
* a reabertura exige ação explícita;
* a justificativa é obrigatória;
* o identificador textual do operador responsável é obrigatório e rejeitado se vazio;
* a informação de responsável é registrada como declaração operacional sem requerer autenticação ou sessão;
* o registro de auditoria preserva justificativa, responsável textual e data/hora;
* a reabertura retorna a venda para `EM PREPARAÇÃO`;
* a reabertura, por si só, não altera preços, não cancela a venda e não cria efeito automático de estoque;
* após reabertura, somente cestas alteradas voltam a exigir nova preparação;
* cestas não alteradas preservam sua preparação concluída;
* a venda só volta para `PRONTA` quando todas as cestas estiverem novamente consideradas preparadas.

## 8. Validação de entrega

Validar que:

* cada cesta é marcada como entregue por ação explícita do usuário;
* data e horário agendados não bastam para considerá-la entregue;
* o registro de entrega exige e preserva o identificador textual do operador responsável, a cesta e a data/hora;
* tentativa de registrar entrega sem identificador textual do responsável é rejeitada;
* o histórico de entrega permanece consultável pelo fluxo normal;
* quando a última cesta for entregue, a venda muda automaticamente para `ENTREGUE`;
* o fluxo não exige assinatura, fotografia ou comprovante de entrega;
* a operação não requer autenticação nem módulo de usuários.

## 9. Validação de cancelamento

Validar que:

* o cancelamento é permitido em `RASCUNHO`, `CONFIRMADA`, `EM PREPARAÇÃO` e `PRONTA` quando nenhuma cesta foi entregue;
* cestas já preparadas não impedem o cancelamento, desde que nenhuma tenha sido entregue;
* qualquer entrega registrada bloqueia o cancelamento pelo fluxo normal, mesmo com outras cestas pendentes;
* uma venda `ENTREGUE` não pode ser cancelada pelo fluxo normal;
* o cancelamento muda o estado para `CANCELADA`;
* venda, cestas e históricos permanecem preservados;
* o cancelamento não presume reembolso, devolução física de itens nem ajuste automático de estoque.

## 10. Validação da fronteira M4–M5

Validar explicitamente que M4:

* não registra pagamentos;
* não calcula total pago;
* não calcula saldo pago;
* não implementa regra própria de 50%;
* não cria confirmação financeira provisória;
* não duplica a responsabilidade do M5 para `RASCUNHO → CONFIRMADA`.

Validar também que a venda só está apta a ser autorizada para `CONFIRMADA` quando todas as cestas tiverem destinatário, endereço, data e horário preenchidos, ficando a verificação financeira sob responsabilidade de M5.

## 11. Validação de histórico e persistência

Validar que:

* toda alteração de composição gera histórico não apagável pelo fluxo normal;
* o histórico de composição registra composição anterior, composição nova, identificador textual do responsável e data/hora;
* tentativa de salvar alteração de composição sem identificador textual do responsável é bloqueada;
* a reabertura registra justificativa, identificador textual do responsável e data/hora;
* o histórico de entrega registra cesta, identificador textual do responsável e data/hora;
* os identificadores textuais são persistidos como declarações operacionais, sem módulos de usuários ou controle de sessão;
* a venda cancelada continua consultável com suas cestas e históricos.

## 12. Testes automatizados — resultado

A suíte automatizada foi implementada em `backend/tests/test_m4_sales.py` com 6 testes, todos aprovados:

| Teste | Resultado |
|-------|-----------|
| `test_create_sale_requires_active_customer_and_at_least_one_basket` | ✅ PASSOU |
| `test_reject_template_without_price_and_preserve_snapshot_price` | ✅ PASSOU |
| `test_multiple_baskets_and_independent_delivery_and_price_in_draft` | ✅ PASSOU |
| `test_confirmation_requires_complete_delivery_data` | ✅ PASSOU |
| `test_composition_change_audit_and_preparation_flow` | ✅ PASSOU |
| `test_delivery_flow_and_cancellation_rules` | ✅ PASSOU |

Os testes cobrem os fluxos principais: criação de venda, múltiplas cestas, confirmação com dados de entrega, alteração de composição com auditoria, preparação, entrega e cancelamento.

## 13. Validação manual

A validação manual foi realizada pelo Product Owner em 2026-10-10, confirmando:

1. Todas as decisões aprovadas aparecem no comportamento observado.
2. Os nomes dos estados estão consistentes em backend, frontend e documentação.
3. Nenhuma transição permite pular etapas.
4. A fronteira M4–M5 permanece inequívoca.
5. Não existe implementação implícita de pagamentos no M4.
6. Não existe movimentação automática de estoque acionada pelo M4.
7. Os históricos exigidos estão preservados.
8. Não foram introduzidos comprovantes de entrega, renegociações excepcionais ou outras capacidades não aprovadas.

**Resultado:** M4 validado e aceito pelo Product Owner.

## 14. Cenários negativos mínimos

Cobrir, no mínimo:

* tentativa de criar nova venda para cliente inativo;
* tentativa de salvar venda sem cestas;
* tentativa de submeter alteração de composição sem identificador textual do responsável;
* tentativa de reabrir venda `PRONTA` sem justificativa ou sem identificador textual do responsável;
* tentativa de registrar entrega sem identificador textual do responsável;
* tentativa de confirmar financeiramente no M4 sem o fluxo de M5;
* tentativa de passar para `EM PREPARAÇÃO` sem ação explícita do usuário;
* tentativa de marcar venda `PRONTA` com cesta pendente de preparação;
* tentativa de alterar preço após `CONFIRMADA`;
* tentativa de alterar composição diretamente em `PRONTA` sem reabertura;
* tentativa de alterar composição em `ENTREGUE` ou `CANCELADA`;
* tentativa de cancelar venda após entrega parcial;
* tentativa de usar data/horário agendados como prova automática de entrega;
* tentativa de inferir ajuste automático de estoque por alteração, entrega ou cancelamento.

## 15. Cobertura mínima dos critérios de aceitação

A validação deve demonstrar cobertura, no mínimo, dos seguintes grupos:

* **Estrutura da venda e composição:** AC-M4-001 a AC-M4-006, AC-M4-004a, AC-M4-004b e AC-M4-046
* **Cliente e `RASCUNHO`:** AC-M4-007 a AC-M4-011
* **Preço:** AC-M4-012 a AC-M4-014
* **Fronteira M4–M5:** AC-M4-015 a AC-M4-018
* **Estados da venda:** AC-M4-019 a AC-M4-023
* **Alterações de composição e histórico:** AC-M4-024 a AC-M4-030
* **Preparação e reabertura:** AC-M4-031 a AC-M4-036
* **Entregas:** AC-M4-037 a AC-M4-040
* **Cancelamento:** AC-M4-041 a AC-M4-045
* **Auditoria e identificação textual do responsável:** AC-M4-047 a AC-M4-049

## 16. Revisão final da validação

A revisão final foi concluída em 2026-10-10 durante a validação manual pelo Product Owner. Todos os 8 pontos foram confirmados como satisfeitos.
