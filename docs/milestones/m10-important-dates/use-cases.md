# M10 — Casos de Uso

**Versão do documento:** 0.1 (Rascunho)
**Status:** Rascunho — pendente de aprovação pelo Product Owner
**Marco:** M10 — Datas Afetivas

---

## UC-M10-1 — Ver datas afetivas próximas

**Ator:** Operador

**Descrição:** O operador consulta a lista de datas afetivas próximas para saber quais clientes têm datas importantes chegando.

**Pré-condições:**
- Existem clientes com datas importantes ativas cadastradas (M3).

**Fluxo principal:**
1. O operador acessa a seção "Datas Afetivas" pela navegação lateral.
2. O sistema carrega as datas dos próximos 7 dias (padrão).
3. O sistema exibe uma lista com: próxima ocorrência, nome do cliente, descrição e indicador de recorrência.
4. O operador identifica quais clientes têm datas chegando.

**Fluxo alternativo A — Filtrar por janela de dias:**
1. Após o passo 1, o operador seleciona um filtro diferente ("Hoje", "7 dias" ou "30 dias").
2. O sistema recarrega a lista com a nova janela.
3. Retoma no passo 3.

**Fluxo alternativo B — Sem datas próximas:**
1. Após o passo 2, não há datas na janela selecionada.
2. O sistema exibe uma mensagem informando que não há datas afetivas próximas.

**Pós-condições:**
- Nenhuma alteração é feita nos dados.

---

## UC-M10-2 — Consultar datas de hoje

**Ator:** Operador

**Descrição:** O operador verifica quais datas afetivas são hoje para tomar ação imediata.

**Pré-condições:**
- Existem clientes com datas importantes ativas cuja próxima ocorrência é hoje.

**Fluxo principal:**
1. O operador acessa a seção "Datas Afetivas".
2. O operador seleciona o filtro "Hoje".
3. O sistema exibe apenas as datas cuja próxima ocorrência é hoje.
4. O operador identifica os clientes com datas de hoje.

**Fluxo alternativo A — Nenhuma data hoje:**
1. Após o passo 3, não há datas para hoje.
2. O sistema exibe a mensagem de estado vazio.

**Pós-condições:**
- Nenhuma alteração é feita nos dados.

---

## UC-M10-3 — Consultar datas do mês

**Ator:** Operador

**Descrição:** O operador verifica as datas afetivas dos próximos 30 dias para planejamento.

**Pré-condições:**
- Existem clientes com datas importantes ativas.

**Fluxo principal:**
1. O operador acessa a seção "Datas Afetivas".
2. O operador seleciona o filtro "30 dias".
3. O sistema exibe as datas dos próximos 30 dias, ordenadas por próxima ocorrência.
4. O operador planeja os contatos proativos.

**Pós-condições:**
- Nenhuma alteração é feita nos dados.

---

## UC-M10-4 — Endpoint de datas próximas via API

**Ator:** Sistema externo ou integração

**Descrição:** Consumir o endpoint de datas próximas via API.

**Pré-condições:**
- O endpoint `GET /api/v1/important-dates/upcoming` está disponível.

**Fluxo principal:**
1. O consumidor faz uma requisição `GET /api/v1/important-dates/upcoming?days=7`.
2. O sistema calcula a próxima ocorrência de cada data ativa.
3. O sistema filtra pelas datas dentro da janela.
4. O sistema retorna a lista ordenada por próxima ocorrência.

**Fluxo alternativo A — Janela personalizada:**
1. O consumidor envia `?days=30` para ampliar a janela.
2. Retoma no passo 2.

**Fluxo alternativo B — Sem datas:**
1. Após o passo 3, não há datas na janela.
2. O sistema retorna `{"items": [], "total": 0}`.

**Fluxo alternativo C — Parâmetro inválido:**
1. O consumidor envia `?days=0` ou `?days=366`.
2. O sistema retorna erro 422.

**Pós-condições:**
- Nenhuma alteração é feita nos dados.

---

*Fim dos casos de uso do M10.*
