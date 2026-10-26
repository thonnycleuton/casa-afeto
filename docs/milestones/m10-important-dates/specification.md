# M10 — Especificação de Datas Afetivas

**Versão do documento:** 0.1 (Rascunho)
**Status:** Rascunho — pendente de aprovação pelo Product Owner
**Marco:** M10 — Datas Afetivas
**Fase:** 2 — Evolução do Estoque e dos Clientes

---

# 1. Finalidade

O M10 introduz a capacidade de **listar todas as datas afetivas próximas** de todos os clientes, em uma visão global.

Antes do M10, o operador precisa abrir o detalhe de cada cliente individualmente para ver suas datas importantes. Não há forma de ver, de uma só vez, quais datas estão chegando.

Após o M10, o sistema oferece uma **lista de datas próximas** que mostra:

```
Data
    ↓
Cliente
    ↓
Descrição da data
    ↓
Tipo (recorrente ou não)
```

O M10 segue o mesmo princípio do M9:

> **Visibilidade antes de automação.**

O sistema mostra quais datas estão chegando. Não envia notificações, não registra contatos realizados, não gera lembretes automáticos.

---

# 2. Escopo

## 2.1 Dentro do escopo

O M10 inclui:

### Endpoint global de datas próximas

* Novo endpoint `GET /api/v1/important-dates/upcoming` que retorna todas as datas afetivas ativas dos próximos N dias;
* O parâmetro `days` define a janela de tempo (padrão 7 dias a partir de hoje);
* O cálculo considera:
  * **Datas recorrentes:** calcula a próxima ocorrência no ano corrente ou próximo, a partir do dia/mês armazenado;
  * **Datas não recorrentes:** usa a data armazenada diretamente;
* Apenas datas com status `ACTIVE` são retornadas;
* Resultados ordenados pela próxima ocorrência crescente;
* A resposta inclui: data da próxima ocorrência, descrição, nome do cliente, ID do cliente, e se é recorrente.

### Página de datas afetivas no frontend

* Nova seção "Datas Afetivas" na navegação lateral;
* Lista mostrando: próxima ocorrência, cliente, descrição e tipo;
* Filtro por janela de dias (hoje, 7 dias, 30 dias);
* Estado vazio quando não há datas próximas.

## 2.2 Explicitamente fora do escopo

O seguinte **não** deve ser implementado como parte do M10:

* notificações automáticas ou push — Fase 3;
* badge ou alerta in-app de datas próximas;
* registro de "contato realizado" para uma data afetiva;
* histórico de contatos;
* categorias personalizáveis de datas;
* integração com WhatsApp ou e-mail;
* jobs agendados para verificação de datas;
* campanhas de marketing baseadas em datas.

---

# 3. Dependências

O M10 depende de:

* `docs/domain/business-contract.md` — regras de negócio;
* `docs/product/roadmap.md` — direção da Fase 2;
* `docs/milestones/m3-customers/specification.md` — clientes e datas importantes;
* `docs/architecture/technical-foundation.md` — fundamentos técnicos.

O M10 depende da implementação do M3 (clientes e datas importantes) para ter dados de datas afetivas.

O M10 é independente dos outros marcos da Fase 2 (M6, M7, M8, M9).

---

# 4. Conceitos de Domínio

O M10 não introduz novas entidades persistentes. Reutiliza:

```
ImportantDate (já existe no M3)
```

O M10 introduz um conceito de cálculo:

```
Próxima Ocorrência (NextOccurrence)
```

Uma **Próxima Ocorrência** é a data em que uma ImportantDate vai ocorrer pela próxima vez, calculada a partir de hoje:

* Para datas **recorrentes** (`recurring=true`): usa `day` e `month` para calcular a próxima ocorrência no ano corrente. Se `day/month` já passou neste ano, usa o ano seguinte. O dia 29 de fevereiro em anos bissextos ocorre no próximo ano bissexto.
* Para datas **não recorrentes** (`recurring=false`): usa `date` diretamente. Se `date` já passou, a data não é considerada "próxima".

---

# 5. Regras de Negócio

## IDA-001 — Apenas datas ativas são listadas

Apenas datas importantes com status `ACTIVE` são consideradas para a lista de datas próximas.

## IDA-002 — Próxima ocorrência de data recorrente

Para uma data recorrente (`recurring=true`), a próxima ocorrência é calculada usando `day` e `month`:

1. Monta a data `day/month/ano_atual`;
2. Se a data resultante já passou (é anterior a hoje), usa `ano_atual + 1`;
3. Se `day/month` não existe no ano calculado (ex: 29/02 em ano não bissexto), encontra o próximo ano válido;
4. A próxima ocorrência é a data resultante.

## IDA-003 — Próxima ocorrência de data não recorrente

Para uma data não recorrente (`recurring=false`), a próxima ocorrência é o próprio campo `date`:

1. Se `date` é hoje ou futuro, a próxima ocorrência é `date`;
2. Se `date` já passou, a data não é considerada "próxima" e não entra na lista.

## IDA-004 — Janela de tempo configurável

O endpoint aceita um parâmetro `days` (inteiro, padrão 7) que define quantos dias à frente de hoje considerar:

1. A janela é de `hoje` até `hoje + days`;
2. Datas cuja próxima ocorrência cai dentro dessa janela são retornadas;
3. O parâmetro `days` tem mínimo 1 e máximo 1095.

## IDA-005 — Ordenação por próxima ocorrência

Os resultados são ordenados por próxima ocorrência crescente. Em caso de empate, ordena por nome do cliente crescente.

## IDA-006 — Cliente inativo não impede listagem

Uma data importante `ACTIVE` vinculada a um cliente `INACTIVE` ainda aparece na lista de datas próximas. O status do cliente não afeta a visibilidade da data.

---

# 6. API

### Novo endpoint

```
GET /api/v1/important-dates/upcoming?days=7
```

**Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `days` | `int` | `7` | Janela de dias à frente (1–365) |

**Resposta:**

```json
{
  "items": [
    {
      "id": 1,
      "customer_id": 5,
      "customer_name": "Maria Silva",
      "description": "Aniversário",
      "recurring": true,
      "next_occurrence": "2026-11-02",
      "status": "ACTIVE"
    }
  ],
  "total": 1
}
```

**Campos da resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `int` | ID da data importante |
| `customer_id` | `int` | ID do cliente |
| `customer_name` | `str` | Nome do cliente |
| `description` | `str` | Descrição da data |
| `recurring` | `bool` | Se é recorrente |
| `next_occurrence` | `date` | Próxima ocorrência calculada |
| `status` | `str` | Status da data (sempre ACTIVE) |

---

# 7. Interface

A seção "Datas Afetivas" é acessível pela navegação lateral, seguindo o padrão das outras seções.

A página exibe:

* Filtros de janela de dias: "Hoje", "7 dias", "30 dias";
* Lista de datas próximas com: próxima ocorrência (formatada em pt-BR), nome do cliente, descrição e indicador de recorrência;
* Estado vazio quando não há datas na janela selecionada.

---

# 8. Fronteiras

O M10 não inclui notificações, automação, registro de contatos, campanhas, CRM, integração com WhatsApp ou e-mail, jobs agendados, categorias de datas ou histórico de contatos realizados.

O M10 não altera o comportamento do M3 (CRUD de datas importantes por cliente).

O M10 não altera o comportamento de nenhum outro marco.

---

# 9. Test Coverage Matrix

A matriz será preenchida após a implementação dos testes.

```markdown
## Test Coverage Matrix

| AC ID | Test Name | File | Line | Status |
|-------|-----------|------|------|--------|
| (Preencher após implementação) |
```

---

*Fim da especificação do M10.*
