# M10 — Plano de Validação

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — implementado e validado
**Marco:** M10 — Datas Afetivas

---

## 1. Pré-requisitos

- M3 (Clientes e Datas Importantes) implementado e funcionando;
- Backend rodando localmente;
- Frontend rodando localmente;
- Pelo menos 2 clientes com datas importantes ativas cadastrados.

---

## 2. Validação do Backend

### 2.1 Endpoint de datas próximas

**Passos:**

1. Acesse `GET /api/v1/important-dates/upcoming` via navegador ou ferramenta API (ex: Swagger UI em `/docs`).
2. Verifique que a resposta contém `items` e `total`.
3. Verifique que cada item tem: `id`, `customer_id`, `customer_name`, `description`, `recurring`, `next_occurrence`, `status`.

**Critérios de sucesso:**
- A resposta é válida e contém os campos esperados.
- As datas retornadas estão dentro da janela de 7 dias (padrão).

---

### 2.2 Janela de tempo padrão (7 dias)

**Passos:**

1. Cadastre uma data recorrente cuja próxima ocorrência é dentro de 7 dias.
2. Cadastre uma data recorrente cuja próxima ocorrência é dentro de 30 dias, mas fora de 7 dias.
3. Acesse `GET /api/v1/important-dates/upcoming` sem parâmetros.
4. Verifique que apenas a data dentro de 7 dias é retornada.

**Critérios de sucesso:**
- Apenas a data dentro da janela de 7 dias aparece.

---

### 2.3 Janela de tempo configurável

**Passos:**

1. Acesse `GET /api/v1/important-dates/upcoming?days=30`.
2. Verifique que datas dos próximos 30 dias são retornadas.
3. Acesse `GET /api/v1/important-dates/upcoming?days=1`.
4. Verifique que apenas datas de hoje são retornadas.

**Critérios de sucesso:**
- O parâmetro `days` ajusta corretamente a janela.

---

### 2.4 Validação do parâmetro days

**Passos:**

1. Acesse `GET /api/v1/important-dates/upcoming?days=0`.
2. Verifique que o erro 422 é retornado.
3. Acesse `GET /api/v1/important-dates/upcoming?days=366`.
4. Verifique que o erro 422 é retornado.

**Critérios de sucesso:**
- Valores fora do intervalo 1–365 retornam erro 422.

---

### 2.5 Datas inativas não são listadas

**Passos:**

1. Crie uma data importante ativa para um cliente.
2. Verifique que ela aparece na lista.
3. Altere o status da data para `INACTIVE` via `PATCH /api/v1/customers/{id}/important-dates/{date_id}/status`.
4. Verifique que a data não aparece mais na lista.

**Critérios de sucesso:**
- Datas inativas não aparecem no endpoint.

---

### 2.6 Data recorrente — cálculo da próxima ocorrência

**Passos:**

1. Crie uma data recorrente (ex: aniversário, dia 15, mês 11).
2. Verifique que `next_occurrence` é calculada corretamente:
   - Se 15/11 ainda não passou este ano, a ocorrência é 15/11/ano_atual.
   - Se 15/11 já passou, a ocorrência é 15/11/ano_seguido.

**Critérios de sucesso:**
- A próxima ocorrência é calculada conforme IDA-002.

---

### 2.7 Data não recorrente — cálculo da próxima ocorrência

**Passos:**

1. Crie uma data não recorrente futura (ex: 2026-12-25).
2. Verifique que `next_occurrence` é a própria data.
3. Crie uma data não recorrente passada (ex: 2026-01-01).
4. Verifique que ela não aparece na lista.

**Critérios de sucesso:**
- Datas futuras são listadas, datas passadas não.

---

### 2.8 Cliente inativo não impede listagem

**Passos:**

1. Crie um cliente e uma data importante ativa.
2. Verifique que a data aparece na lista.
3. Altere o status do cliente para `INACTIVE`.
4. Verifique que a data ainda aparece na lista.

**Critérios de sucesso:**
- A data de cliente inativo continua aparecendo.

---

### 2.9 Ordenação

**Passos:**

1. Cadastre datas com próximas ocorrências em dias diferentes.
2. Verifique que a lista vem ordenada por `next_occurrence` crescente.
3. Cadastre duas datas no mesmo dia para clientes com nomes diferentes.
4. Verifique que a ordem é por nome do cliente.

**Critérios de sucesso:**
- A ordenação segue IDA-005.

---

### 2.10 Lista vazia

**Passos:**

1. Remova ou inative todas as datas importantes.
2. Acesse `GET /api/v1/important-dates/upcoming`.
3. Verifique que a resposta é `{"items": [], "total": 0}`.

**Critérios de sucesso:**
- Lista vazia é retornada corretamente.

---

## 3. Validação do Frontend

### 3.1 Navegação

**Passos:**

1. Abra o aplicativo.
2. Verifique que "Datas Afetivas" aparece na navegação lateral.
3. Clique em "Datas Afetivas".
4. Verifique que a página é exibida.

**Critérios de sucesso:**
- A seção é acessível e carrega corretamente.

---

### 3.2 Lista de datas

**Passos:**

1. Acesse a seção "Datas Afetivas".
2. Verifique que as datas próximas são exibidas com:
   - Próxima ocorrência formatada em pt-BR.
   - Nome do cliente.
   - Descrição da data.
   - Indicador de recorrência para datas recorrentes.

**Critérios de sucesso:**
- Todos os campos são exibidos corretamente.

---

### 3.3 Filtros por janela

**Passos:**

1. Acesse a seção "Datas Afetivas".
2. Clique em "Hoje" e verifique que apenas datas de hoje aparecem.
3. Clique em "7 dias" e verifique que a lista se atualiza.
4. Clique em "30 dias" e verifique que a lista se atualiza.

**Critérios de sucesso:**
- Os filtros funcionam e atualizam a lista.

---

### 3.4 Estado vazio

**Passos:**

1. Garanta que não há datas próximas na janela selecionada.
2. Acesse a seção "Datas Afetivas".
3. Verifique que uma mensagem de estado vazio é exibida.

**Critérios de sucesso:**
- A mensagem de estado vazio é clara e informativa.

---

## 4. Execução de Testes Automatizados

**Passos:**

1. Execute os testes do backend:
   ```bash
   cd backend && python -m pytest tests/test_important_dates_upcoming.py -v
   ```
2. Verifique que todos os testes passam.

**Critérios de sucesso:**
- Todos os testes passam sem erros.

---

## 5. Checklist de Validação Final

| Item | Status |
|------|--------|
| Endpoint retorna dados corretos | ☐ |
| Janela de tempo funciona | ☐ |
| Validação do parâmetro days | ☐ |
| Datas inativas não aparecem | ☐ |
| Cálculo de próxima ocorrência recorrente | ☐ |
| Cálculo de próxima ocorrência não recorrente | ☐ |
| Cliente inativo não impede listagem | ☐ |
| Ordenação correta | ☐ |
| Lista vazia funciona | ☐ |
| Seção "Datas Afetivas" na navegação | ☐ |
| Lista de datas exibida corretamente | ☐ |
| Filtros por janela funcionam | ☐ |
| Estado vazio exibido | ☐ |
| Testes automatizados passam | ☐ |

---

*Fim do plano de validação do M10.*
