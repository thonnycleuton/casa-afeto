# M8 — Casos de Uso

**Versão:** 0.2 (Aprovado)
**Milestone:** M8 — Gestão de Vencimentos

---

## UC-M8-001 — Registrar compra com vencimento

**Atores:** Operador
**Pré-condição:** Produto ativo cadastrado
**Fluxo principal:**
1. O operador abre o modal de nova compra.
2. Adiciona um item de compra selecionando o produto.
3. Informa quantidade, preço e **data de vencimento**.
4. Confirma a compra.
5. O sistema cria o lote com `expiry_date` herdada do item.
6. O sistema registra a movimentação de ENTRY vinculada ao lote.

**Fluxo alternativo:**
- 3a. O operador não informa data de vencimento.
- 3b. O sistema cria o lote com `expiry_date = NULL`.

**Pós-condição:** Lote criado com vencimento informado ou NULL.

---

## UC-M8-002 — Registrar entrada manual com vencimento

**Atores:** Operador
**Pré-condição:** Produto ativo cadastrado
**Fluxo principal:**
1. O operador abre o modal de estoque do produto.
2. Preenche o formulário de entrada manual: quantidade e custo.
3. Informa **data de vencimento** (opcional).
4. Confirma a entrada.
5. O sistema cria o lote com `expiry_date` informada.

**Fluxo alternativo:**
- 3a. O operador não informa data de vencimento.
- 3b. O sistema cria o lote com `expiry_date = NULL`.

**Pós-condição:** Lote criado com vencimento informado ou NULL.

---

## UC-M8-003 — Consultar lotes com vencimento

**Atores:** Operador
**Pré-condição:** Produto com lotes ativos
**Fluxo principal:**
1. O operador abre o modal de estoque do produto.
2. O sistema exibe a tabela de lotes ativos com coluna "Vencimento" e "Status".
3. Lotes vencidos exibem badge vermelho.
4. Lotes próximos do vencimento exibem badge amarelo.
5. Lotes sem vencimento exibem "—" na coluna de vencimento.

**Pós-condição:** O operador visualiza o estado de vencimento de cada lote.

---

## UC-M8-004 — Consultar lista global de vencimentos

**Atores:** Operador
**Pré-condição:** Lotes com vencimento próximo ou vencido no sistema
**Fluxo principal:**
1. O operador acessa a seção de vencimentos.
2. O sistema consulta `GET /inventory/expiry-alerts`.
3. O sistema exibe uma lista ordenada por urgência: vencidos primeiro, depois próximos do vencimento.
4. Cada item mostra: produto, quantidade restante, data de vencimento e dias até o vencimento.

**Fluxo alternativo:**
- 2a. Nenhum lote tem vencimento próximo ou vencido.
- 2b. O sistema exibe "Nenhum vencimento pendente".

**Pós-condição:** O operador identifica os lotes que precisam de atenção.

---

## UC-M8-005 — Consumo FEFO automático

**Atores:** Sistema (automático)
**Pré-condição:** Produto com múltiplos lotes ativos, alguns com vencimento
**Fluxo principal:**
1. Uma venda confirma a saída de um produto.
2. O sistema identifica os lotes ativos do produto.
3. O sistema ordena os lotes por FEFO: vencimento mais próximo primeiro, depois FIFO para lotes sem vencimento.
4. O sistema consome do primeiro lote até esgotar ou completar a quantidade.
5. Se o lote for esgotado, seu status muda para EXHAUSTED.
6. O sistema continua para o próximo lote se necessário.

**Pós-condição:** Estoque consumido seguindo a política FEFO.

---

## UC-M8-006 — Ajustar threshold de alerta

**Atores:** Administrador
**Pré-condição:** Acesso à configuração do sistema
**Fluxo principal:**
1. O administrador define a variável `EXPIRY_ALERT_DAYS = 14`.
2. O sistema recarrega a configuração.
3. A partir desse momento, lotes que vencem em até 14 dias são considerados "próximos do vencimento".

**Pós-condição:** O threshold de alerta é atualizado para todos os usuários.

---

*Fim dos casos de uso do M8.*
