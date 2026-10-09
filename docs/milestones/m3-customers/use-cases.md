# M3 — Casos de Uso: Clientes e Datas Importantes

**Status:** COMPLETED — implementação e validação concluídas

## UC-M3-01 — Criar cliente

1. Na lista, a pessoa usuária inicia um novo cadastro.
2. Informa nome e telefone, podendo informar e-mail e observações.
3. Ao salvar, o sistema normaliza os dados, define status `ACTIVE` e abre o detalhe.
4. Telefone duplicado não bloqueia a operação e apresenta o aviso `DUPLICATE_PHONE`.

## UC-M3-02 — Pesquisar e listar clientes

1. A pessoa usuária informa um único termo, escolhe status e solicita a busca.
2. O sistema procura nome parcial sem distinção de caixa/acentos ou telefone parcial normalizado.
3. Resultados são ordenados por nome crescente e apresentados em páginas.
4. Sem status explícito, são listados clientes `ACTIVE`; `ALL` inclui ambos os status.
5. Resultado vazio e busca sem resultados são apresentados claramente.

## UC-M3-03 — Consultar, editar e alterar status do cliente

1. A pessoa usuária abre um Cliente a partir da lista.
2. Pode consultar e editar dados, inclusive quando o Cliente está `INACTIVE`.
3. Pode inativar ou reativar mediante confirmação.
4. Alterar dados não altera status; alterar status não altera dados nem datas.
5. Ao editar para telefone de outro Cliente, a operação continua e informa duplicidade.

## UC-M3-04 — Gerenciar datas importantes

1. No detalhe de qualquer Cliente, a pessoa usuária lista as datas cadastradas e pode adicionar uma.
2. Para recorrência, informa descrição, dia e mês; `29/02` é permitido sem ano.
3. Para não recorrência, informa a data completa; datas passadas e futuras são aceitas.
4. Pode editar ou ativar/inativar cada data mediante confirmação para mudança de status.
5. Duplicidade é permitida. Status da data não altera status do Cliente e vice-versa.
6. Cliente `INACTIVE` continua aceitando consulta, edição e novas datas.
