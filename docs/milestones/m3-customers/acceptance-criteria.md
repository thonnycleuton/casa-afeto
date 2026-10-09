# M3 — Critérios de Aceitação

**Status:** Critérios atendidos; M3 COMPLETED

## Clientes

* **AC-M3-001 — Criação:** nome e telefone são obrigatórios; nome, telefone, e-mail e observações são normalizados; e-mail informado deve ser válido; status inicial é `ACTIVE`; POST com `status` é rejeitado.
* **AC-M3-002 — Edição:** dados podem ser alterados em qualquer status; campos opcionais podem ser limpos; edição não altera status.
* **AC-M3-003 — Duplicidade:** telefone repetido permite sucesso e retorna o warning `DUPLICATE_PHONE`; edição exclui o próprio Cliente da comparação.
* **AC-M3-004 — Busca:** termo único procura nome parcial, case-insensitive e accent-insensitive, ou telefone parcial normalizado.
* **AC-M3-005 — Listagem:** status padrão `ACTIVE`; filtros `ACTIVE`, `INACTIVE` e `ALL`; paginação; nome ascendente; combinações de filtros e resultados vazios.
* **AC-M3-006 — Status:** ativar/inativar afeta somente o Cliente; Cliente inativo continua consultável e editável.

## Datas importantes

* **AC-M3-007 — Recorrência:** recorrente armazena somente dia e mês; `29/02` é preservado; combinações inválidas são rejeitadas.
* **AC-M3-008 — Ocorrência única:** não recorrente armazena data completa, incluindo datas passadas e futuras.
* **AC-M3-009 — Gestão:** duplicidade permitida; datas podem ser editadas e ativadas/inativadas independentemente do status do Cliente.
* **AC-M3-010 — Cliente inativo:** aceita consulta, edição e criação/gestão de datas sem reativação automática.

## API e fronteiras

* **AC-M3-011 — Integridade:** Cliente/data inexistente resulta em erro; data de outro Cliente não é acessível pela rota do Cliente atual; não há operação DELETE.
* **AC-M3-012 — Escopo:** não são implementados vendas, pagamentos, destinatário global, notificações, integrações ou CRM.
* **AC-M3-013 — Feedback:** frontend apresenta loading, erro, sucesso, listas vazias e busca sem resultados; nunca comunica sucesso quando uma chamada falha.
