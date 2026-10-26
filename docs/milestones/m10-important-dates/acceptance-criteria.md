# M10 — Critérios de Aceitação

**Versão do documento:** 0.1 (Rascunho)
**Status:** Rascunho — pendente de aprovação pelo Product Owner
**Marco:** M10 — Datas Afetivas

---

## Backend

### AC-M10-001 [Backend] — Apenas datas ativas são retornadas

O endpoint retorna apenas datas importantes com status `ACTIVE`. Datas inativas não aparecem na lista.

**Verificação:**
- Dado 2 datas ativas e 1 inativa na janela, apenas 2 são retornadas.
- Dado todas as datas inativas, a lista é vazia.

### AC-M10-002 [Backend] — Próxima ocorrência de data recorrente no ano atual

Para uma data recorrente cuja data dia/mês ainda não passou no ano corrente, a próxima ocorrência é calculada no ano atual.

**Verificação:**
- Dado hoje = 2026-10-26, data recorrente 15/11, a próxima ocorrência é 2026-11-15.
- Dado hoje = 2026-10-26, data recorrente 01/01, a próxima ocorrência é 2027-01-01.

### AC-M10-003 [Backend] — Próxima ocorrência de data recorrente no ano seguinte

Para uma data recorrente cuja data dia/mês já passou no ano corrente, a próxima ocorrência é calculada no ano seguinte.

**Verificação:**
- Dado hoje = 2026-10-26, data recorrente 15/03, a próxima ocorrência é 2027-03-15.
- Dado hoje = 2026-10-26, data recorrente 26/10 (hoje), a próxima ocorrência é 2026-10-26.

### AC-M10-004 [Backend] — Data 29 de fevereiro em ano não bissexto

Para uma data recorrente 29/02, a próxima ocorrência é calculada no próximo ano bissexto válido.

**Verificação:**
- Dado hoje = 2026-10-26, data recorrente 29/02, a próxima ocorrência é 2028-02-29 (próximo bissexto).
- Dado hoje = 2027-01-01, data recorrente 29/02, a próxima ocorrência é 2028-02-29.

### AC-M10-005 [Backend] — Próxima ocorrência de data não recorrente futura

Para uma data não recorrente com data no futuro, a próxima ocorrência é a própria data armazenada.

**Verificação:**
- Dado hoje = 2026-10-26, data não recorrente 2026-11-15, a próxima ocorrência é 2026-11-15.

### AC-M10-006 [Backend] — Data não recorrente passada não é listada

Para uma data não recorrente com data já passada, a data não entra na lista de datas próximas.

**Verificação:**
- Dado hoje = 2026-10-26, data não recorrente 2026-01-15, a data não é retornada.
- Dado hoje = 2026-10-26, data não recorrente 2026-10-26 (hoje), a data é retornada.

### AC-M10-007 [Backend] — Janela de tempo padrão é 7 dias

Sem parâmetro `days`, o endpoint retorna datas cuja próxima ocorrência está entre hoje e hoje + 7 dias.

**Verificação:**
- Dado hoje = 2026-10-26, sem parâmetro, a janela é 2026-10-26 a 2026-11-02.
- Uma data com próxima ocorrência em 2026-11-03 não é retornada.

### AC-M10-008 [Backend] — Janela de tempo configurável via parâmetro days

O parâmetro `days` ajusta a janela de tempo.

**Verificação:**
- `?days=1` retorna apenas datas de hoje.
- `?days=30` retorna datas dos próximos 30 dias.
- `?days=365` retorna datas dos próximos 365 dias.

### AC-M10-009 [Backend] — Validação do parâmetro days

O parâmetro `days` deve estar entre 1 e 365. Valores fora desse intervalo retornam erro 422.

**Verificação:**
- `?days=0` retorna 422.
- `?days=366` retorna 422.
- `?days=-1` retorna 422.

### AC-M10-010 [Backend] — Ordenação por próxima ocorrência

Os resultados são ordenados por próxima ocorrência crescente. Em caso de empate, por nome do cliente crescente.

**Verificação:**
- Dado datas com ocorrências em 02/11, 01/11 e 03/11, a ordem é 01/11, 02/11, 03/11.
- Dado duas datas no mesmo dia com clientes "Ana" e "Zé", a ordem é "Ana", "Zé".

### AC-M10-011 [Backend] — Cliente inativo não impede listagem

Uma data importante `ACTIVE` vinculada a um cliente `INACTIVE` aparece na lista.

**Verificação:**
- Dado um cliente inativo com uma data ativa na janela, a data é retornada.
- O nome do cliente inativo aparece normalmente na resposta.

### AC-M10-012 [Backend] — Resposta inclui todos os campos esperados

Cada item da resposta contém: `id`, `customer_id`, `customer_name`, `description`, `recurring`, `next_occurrence` e `status`.

**Verificação:**
- A resposta contém `items` e `total`.
- Cada item tem todos os 7 campos.

### AC-M10-013 [Backend] — Lista vazia quando não há datas próximas

Quando não há datas ativas na janela, o endpoint retorna uma lista vazia com total 0.

**Verificação:**
- Sem nenhuma data importante cadastrada, a resposta é `{"items": [], "total": 0}`.
- Com datas fora da janela, a resposta é `{"items": [], "total": 0}`.

---

## Frontend

### AC-M10-014 [Frontend] — Seção "Datas Afetivas" na navegação

O aplicativo possui uma seção "Datas Afetivas" acessível pela navegação lateral.

**Verificação:**
- O item "Datas Afetivas" aparece na sidebar.
- Clicar no item exibe a página de datas afetivas.

### AC-M10-015 [Frontend] — Lista de datas próximas

A página exibe uma lista de datas próximas com: próxima ocorrência formatada (pt-BR), nome do cliente, descrição e indicador de recorrência.

**Verificação:**
- A data é formatada como "2 nov 2026" ou similar em pt-BR.
- O nome do cliente é exibido.
- A descrição da data é exibida.
- Datas recorrentes têm um indicador visual (ícone ou texto).

### AC-M10-016 [Frontend] — Filtros por janela de dias

A página possui filtros rápidos por janela de dias: "Hoje", "7 dias", "30 dias".

**Verificação:**
- Clicar em "Hoje" mostra apenas datas de hoje.
- Clicar em "7 dias" mostra datas dos próximos 7 dias.
- Clicar em "30 dias" mostra datas dos próximos 30 dias.

### AC-M10-017 [Frontend] — Estado vazio quando não há datas

Quando não há datas na janela selecionada, a página exibe uma mensagem informando que não há datas afetivas próximas.

**Verificação:**
- Sem datas na janela, a lista é substituída por uma mensagem de estado vazio.

---

*Fim dos critérios de aceitação do M10.*
