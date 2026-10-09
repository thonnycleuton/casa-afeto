# M3 — Especificação Consolidada: Clientes e Datas Importantes

**Versão:** 1.0
**Status:** COMPLETED — implementação e validação concluídas
**Fase:** 1 — Operações Centrais

Esta especificação consolida as decisões aprovadas para M3. Ela substitui a preparação documental anterior e não inclui vendas, pagamentos nem funcionalidades de CRM.

## 1. Objetivo e escopo

M3 entrega gestão de clientes e de datas importantes associadas individualmente a cada cliente:

* listar, buscar, paginar, consultar, criar, editar, inativar e reativar clientes;
* criar, listar, editar, inativar e reativar datas importantes;
* oferecer interface web e API REST para essas operações.

Não existe exclusão física. O endereço não pertence ao Cliente. Datas importantes não geram lembretes, notificações, campanhas nem integrações.

## 2. Cliente

Campos: `name`, `phone`, `email`, `notes` e `status`. Nome e telefone são obrigatórios; e-mail e observações são opcionais. Nome, e-mail e observações são aparados de espaços externos; telefone é armazenado somente com dígitos. Nome vazio após aparar e telefone sem dígitos são inválidos. E-mail informado precisa ter formato válido.

Status permitido: `ACTIVE` ou `INACTIVE`. Criação sempre define `ACTIVE`; o campo `status` enviado no POST deve ser rejeitado. A alteração de status afeta somente o Cliente. Clientes inativos continuam consultáveis, editáveis e podem receber datas; essas operações não reativam o Cliente.

Telefones duplicados são permitidos. Criar ou editar continua sendo sucesso, acompanhado do aviso estruturado `{"code":"DUPLICATE_PHONE"}` quando outro Cliente tem o mesmo telefone normalizado. Na edição, o próprio registro não participa da comparação.

## 3. Busca e listagem

O endpoint de listagem usa um campo de pesquisa que procura nome parcial (sem distinguir maiúsculas/minúsculas ou acentos) ou telefone parcial após normalização. Status pode ser `ACTIVE`, `INACTIVE` ou `ALL`; sem filtro, o padrão é `ACTIVE`. Resultados são ordenados por nome crescente e paginados.

## 4. Datas importantes

Uma data contém descrição, tipo/recorrência, valor temporal e status, e pertence a um Cliente.

* Recorrente: armazena somente `day` e `month`; não armazena nem pede ano. `29/02` permanece `day=29, month=2`. Combinações de dia/mês inexistentes são rejeitadas.
* Não recorrente: armazena ocorrência completa `YYYY-MM-DD`. Datas passadas, presentes e futuras são válidas.
* Duplicidade de datas é permitida.

Status permitido: `ACTIVE` ou `INACTIVE`. A criação define `ACTIVE`; alterações de status afetam somente a data. Status da data e status do Cliente são independentes. Cliente inativo aceita as mesmas operações de consulta, edição e gestão de datas.

## 5. API

```text
GET    /api/v1/customers
POST   /api/v1/customers
GET    /api/v1/customers/{id}
PUT    /api/v1/customers/{id}
PATCH  /api/v1/customers/{id}/status
GET    /api/v1/customers/{id}/important-dates
POST   /api/v1/customers/{id}/important-dates
PUT    /api/v1/customers/{id}/important-dates/{date_id}
PATCH  /api/v1/customers/{id}/important-dates/{date_id}/status
```

Não implementar `DELETE`. Registro inexistente retorna erro de recurso não encontrado; data vinculada a outro Cliente não pode ser consultada ou alterada pela rota daquele Cliente.

## 6. Interface

A lista contém busca única por nome/telefone, filtro de status e paginação. Criação segue lista → novo Cliente → salvar → detalhe. Edição salva e permanece no detalhe. Datas são gerenciadas no detalhe do Cliente; formulários recorrentes pedem dia e mês, e não recorrentes pedem data completa.

Inativação e reativação de Cliente ou data exigem confirmação. A interface apresenta estados de carregamento, erro, sucesso, lista vazia e busca sem resultados; falha da API nunca é apresentada como sucesso.

## 7. Fronteiras

M3 não inclui vendas, pagamentos, preço, cancelamento, entregas, destinatários globais, WhatsApp, integrações, notificações, jobs, campanhas, CRM, histórico comercial ou métricas comerciais. M3 não altera o comportamento de M1 ou M2.
