# M4 — Especificação de Vendas

**Versão do documento:** 0.2
**Status:** DRAFT — formalização documental; implementação não iniciada e condicionada ao fechamento da correção pontual de preço no M2 e à resolução das decisões pendentes de negócio
**Marco:** M4 — Vendas (Sales)
**Fase:** 1 — Operações Centrais (Core Operations)

---

## 1. Objetivo

M4 formaliza o ciclo operacional da venda da Casa Afeto, conectando clientes e cestas sem implementar pagamentos. O marco define como uma venda é criada, mantida em `RASCUNHO`, autorizada para entrar em `CONFIRMADA` pelo fluxo financeiro de M5 e conduzida operacionalmente até `ENTREGUE` ou `CANCELADA`.

Esta especificação registra o comportamento aprovado para M4. As decisões aprovadas pelo Product Owner prevalecem sobre descrições antigas em outros documentos.

## 2. Escopo

M4 inclui:

* criar venda vinculada a cliente ativo;
* salvar e editar venda em `RASCUNHO`;
* adicionar uma ou mais cestas a uma venda, inclusive várias baseadas no mesmo modelo de origem;
* copiar a composição e o preço vigente da cesta-origem no momento da adição à venda;
* manter composição, destinatário, endereço, data e horário de entrega independentes para cada cesta da venda;
* recalcular o total da venda a partir dos preços registrados das cestas;
* permitir alteração de composição conforme o estado operacional da venda;
* permitir ajuste manual de preço somente em `RASCUNHO`;
* iniciar a preparação por ação explícita do usuário;
* marcar cada cesta individualmente como preparada;
* reabrir venda `PRONTA` com justificativa e auditoria;
* registrar entrega individual de cada cesta;
* concluir automaticamente a venda como `ENTREGUE` quando todas as cestas forem entregues;
* cancelar a venda nas condições aprovadas;
* preservar histórico operacional e de alterações de composição.

M4 não inclui:

* registrar pagamentos;
* calcular total pago ou saldo pago;
* aplicar ou duplicar a regra financeira de 50%;
* criar confirmação financeira provisória;
* deduzir, devolver, reservar ou ajustar estoque automaticamente;
* renegociação excepcional de preço após `CONFIRMADA`;
* reembolso, devolução física de itens ou tratamento financeiro do cancelamento;
* assinatura, fotografia ou comprovante de entrega;
* definição de esquema de banco, tabelas, endpoints ou contratos técnicos de API.

## 3. Dependências

M4 depende de decisões e capacidades já estabelecidas:

* **M1 — Produtos e Estoque:** produtos, disponibilidade informativa e regras de integridade de estoque continuam válidos, mas M4 não executa movimentações automáticas de estoque.
* **M2 — Cestas e Templates de Cesta:** a venda reutiliza o Template de Cesta (cesta-modelo) como origem de composição e preço. A composição da cesta na venda é uma cópia independente do Template, e o Template precisa ter preço de venda persistido para poder ser adicionado à venda. A Cesta concreta do M2 não é usada como origem de venda.
* **M3 — Clientes e Datas Importantes:** uma nova venda só pode ser salva quando vinculada a cliente `ACTIVE`. Se o cliente se tornar `INACTIVE` depois da criação, o vínculo existente permanece válido.

## 4. Estrutura conceitual da venda

### 4.1 Venda

Uma venda é a entidade operacional que representa o acordo comercial com um cliente.

Dados conceituais de negócio da venda:

* cliente vinculado;
* estado operacional;
* conjunto de cestas da venda;
* total da venda;
* histórico operacional aplicável.

Uma venda pode conter várias cestas, inclusive várias baseadas no mesmo modelo/origem. Para fins de negócio, a venda existe para consolidar essas cestas sob um único ciclo operacional, sem unificar automaticamente seus dados individuais de entrega.

### 4.2 Cesta da venda

Cada cesta adicionada à venda passa a ter contexto próprio dentro da venda.

Cada cesta da venda possui, de forma independente:

* composição;
* destinatário;
* endereço de entrega;
* data de entrega;
* horário de entrega;
* preço acordado registrado;
* condição operacional de preparação;
* histórico de alterações e de entrega aplicável.

Ao adicionar uma cesta à venda a partir de um Template:

1. a composição do Template é copiada naquele momento;
2. o preço vigente do Template é copiado naquele momento;
3. a cesta na venda torna-se independente do Template para fins de composição e operação.

Se o Template não tiver preço de venda definido, a inclusão da cesta na venda deve ser bloqueada até que o preço seja informado no Template.

Alterações posteriores na cesta da venda não modificam o Template. Alterações posteriores no Template também não modificam a cesta já adicionada à venda.

A cesta da venda pode ser personalizada: adicionar itens, remover itens, alterar quantidades — sem afetar o Template.

## 5. Composição, preço e total

### 5.1 Composição copiada e independente

A composição registrada na venda representa aquilo que está sendo operado naquela venda específica. Ela não é uma referência viva ao modelo de origem.

### 5.2 Preço por cesta

Cada cesta da venda mantém um preço acordado próprio.

Regras:

1. o preço vigente da origem é copiado quando a cesta é adicionada à venda;
2. o preço de cada cesta pode ser ajustado manualmente somente enquanto a venda estiver em `RASCUNHO`;
3. a partir de `CONFIRMADA`, o preço acordado fica bloqueado no fluxo normal do M4;
4. alterações de composição não recalculam automaticamente o preço acordado;
5. renegociações excepcionais após `CONFIRMADA` não fazem parte do fluxo normal do M4;
6. mudanças futuras no preço da cesta-origem não alteram o preço já registrado no item da venda (snapshot histórico).

### 5.3 Total da venda

O total da venda é a soma dos preços registrados de todas as cestas que a compõem.

O total deve ser recalculado quando os preços registrados das cestas mudarem. Alterar a composição sem alterar o preço não muda automaticamente o total.

## 6. Cliente e regras de rascunho

### 6.1 Cliente para nova venda

Uma nova venda só pode ser salva quando vinculada a um cliente ativo.

Criar novas vendas para clientes inativos não é permitido.

### 6.2 Cliente após criação

Se o cliente se tornar inativo depois que a venda já existir, o vínculo daquela venda permanece preservado. Essa preservação não autoriza a criação de novas vendas para clientes inativos.

### 6.3 Venda em `RASCUNHO`

`RASCUNHO` é o estado inicial da venda no M4.

Regras:

1. a venda em `RASCUNHO` pode ter dados de entrega incompletos;
2. o fluxo normal do M4 permite editar composição e preço em `RASCUNHO`;
3. `RASCUNHO` não representa confirmação financeira nem autorização de preparo;
4. M4 não deduz estoque pelo simples fato de uma venda existir em `RASCUNHO`.

## 7. Estados oficiais da venda e transições

Os estados oficiais de M4 são:

* `RASCUNHO`
* `CONFIRMADA`
* `EM PREPARAÇÃO`
* `PRONTA`
* `ENTREGUE`
* `CANCELADA`

Fluxo operacional normal:

```text
RASCUNHO
   ↓  (autorização financeira pertence ao M5)
CONFIRMADA
   ↓  (ação explícita do usuário)
EM PREPARAÇÃO
   ↓  (todas as cestas preparadas)
PRONTA
   ↓  (todas as cestas entregues)
ENTREGUE
```

Fluxos excepcionais aprovados:

```text
RASCUNHO / CONFIRMADA / EM PREPARAÇÃO / PRONTA
                                ↓
                           CANCELADA

PRONTA
  ↓  (reabertura explícita, auditável, com justificativa)
EM PREPARAÇÃO
```

Regras gerais:

1. não existem transições que permitam pular etapas do fluxo normal;
2. a transição `RASCUNHO → CONFIRMADA` faz parte do contrato de estados, mas sua autorização financeira pertence ao M5;
3. a transição `CONFIRMADA → EM PREPARAÇÃO` exige ação explícita do usuário;
4. a venda só se torna `PRONTA` quando todas as cestas estiverem preparadas;
5. a venda só se torna `ENTREGUE` quando todas as cestas estiverem entregues;
6. `ENTREGUE` e `CANCELADA` são estados terminais para o fluxo comercial normal do M4.

## 8. Fronteira entre M4 e M5

A fronteira entre M4 e M5 deve permanecer inequívoca.

### 8.1 Responsabilidade do M4

M4 define:

* a estrutura da venda;
* os estados operacionais da venda;
* as restrições e permissões por estado;
* os dados operacionais das cestas da venda;
* o comportamento de preparação, reabertura, entrega e cancelamento.

### 8.2 Responsabilidade do M5

M5 define e executa:

* o registro de pagamentos;
* a apuração do total pago;
* a verificação do limiar mínimo de 50% para autorizar a confirmação;
* a autorização financeira da transição `RASCUNHO → CONFIRMADA`.

A confirmação exige, ao mesmo tempo:

* o atendimento do limiar financeiro definido para M5; e
* a validação de que todas as cestas da venda possuem destinatário, endereço, data e horário de entrega preenchidos.

### 8.3 Restrições para evitar duplicação de regras

M4 não deve:

* registrar pagamentos;
* calcular valores pagos;
* implementar lógica paralela de confirmação financeira;
* sugerir que existe uma segunda regra independente para a transição `RASCUNHO → CONFIRMADA`;
* presumir deduções, devoluções ou ajustes automáticos de estoque decorrentes de composição, preparação, entrega ou cancelamento.

## 9. Alterações de composição por estado

### 9.1 Em `RASCUNHO`

A composição pode ser alterada livremente no fluxo normal. Essas alterações não recalculam automaticamente o preço acordado.

### 9.2 Em `CONFIRMADA`

É permitido adicionar itens, remover itens e alterar quantidades nas cestas da venda.

Essas alterações:

* não recalculam automaticamente o preço acordado;
* não alteram automaticamente o estado da venda;
* não presumem qualquer ajuste automático de estoque.

### 9.3 Em `EM PREPARAÇÃO`

As mesmas alterações de composição continuam permitidas, mas exigem confirmação explícita antes de salvar, com aviso de que itens podem já ter sido separados ou preparados.

Se a composição de uma cesta for alterada durante `EM PREPARAÇÃO`, a marcação anterior de preparação dessa cesta é invalidada e ela volta a ficar pendente de preparação.

Cestas não alteradas preservam sua marcação de preparação concluída.

### 9.4 Em `PRONTA`

Alterações diretas de composição ficam bloqueadas no fluxo normal.

Para voltar a alterar a composição, a venda precisa ser reaberta explicitamente e de forma auditável, retornando a `EM PREPARAÇÃO`.

### 9.5 Em `ENTREGUE` e `CANCELADA`

Vendas `ENTREGUE` ou `CANCELADA` não aceitam alterações comerciais de composição no fluxo normal.

## 10. Preparação por cesta

Cada cesta pode ser marcada individualmente como preparada.

A preparação é uma condição operacional, não uma entrega e não uma movimentação automática de estoque.

Regras:

1. cada cesta da venda deve possuir um estado ou registro operacional que permita verificar se sua preparação foi concluída;
2. a venda só passa a `PRONTA` quando todas as cestas estiverem marcadas como preparadas;
3. a marcação de uma cesta como preparada não entrega a cesta;
4. a marcação de uma cesta como preparada não executa movimentação automática de estoque.

## 11. Reabertura de venda `PRONTA`

Reabrir uma venda `PRONTA` exige:

* ação explícita do usuário;
* justificativa obrigatória;
* identificação textual obrigatória do operador responsável (conforme seção 14.4);
* registro de data/hora da operação.

A reabertura retorna a venda para `EM PREPARAÇÃO`.

Regras adicionais:

1. a reabertura, por si só, não altera preços acordados;
2. a reabertura, por si só, não cancela a venda;
3. a reabertura, por si só, não executa ajustes automáticos de estoque;
4. cestas cuja composição for alterada após a reabertura precisam ser marcadas como preparadas novamente;
5. cestas não alteradas preservam sua preparação concluída;
6. a venda só volta a `PRONTA` quando todas as cestas estiverem novamente consideradas preparadas.

## 12. Entregas individuais

Cada cesta é marcada como entregue por ação explícita do usuário.

A data e o horário agendados não constituem prova de entrega.

Cada registro de entrega deve preservar, no mínimo:

* a cesta entregue;
* o identificador textual do operador responsável pelo registro (conforme seção 14.4);
* a data/hora do registro.

Quando todas as cestas da venda estiverem entregues, o status da venda muda automaticamente para `ENTREGUE`.

M4 não inclui assinatura, fotografia ou comprovante de entrega.

## 13. Cancelamento

O cancelamento é permitido nos estados:

* `RASCUNHO`
* `CONFIRMADA`
* `EM PREPARAÇÃO`
* `PRONTA`

Condições:

1. nenhuma cesta da venda pode ter sido entregue;
2. cestas já preparadas não impedem o cancelamento;
3. se qualquer cesta já tiver sido entregue, o cancelamento pelo fluxo normal é bloqueado, mesmo que outras cestas permaneçam pendentes;
4. uma venda `ENTREGUE` não pode ser cancelada pelo fluxo normal.

Ao cancelar:

* a venda muda para `CANCELADA`;
* a venda, as cestas e seus históricos são preservados;
* o cancelamento não presume reembolso, devolução física de itens nem ajuste automático de estoque.

## 14. Auditoria e histórico

M4 deve preservar histórico operacional relevante para rastreabilidade de negócio.

### 14.1 Histórico de composição

Toda alteração de composição deve ter histórico não apagável pelo fluxo normal, registrando:

* itens e quantidades anteriores;
* itens e quantidades novos;
* identificador textual do operador responsável (obrigatório);
* data/hora da alteração.

### 14.2 Histórico de reabertura

A reabertura de venda `PRONTA` deve preservar:

* justificativa obrigatória;
* identificador textual do operador responsável (obrigatório);
* data/hora da reabertura.

### 14.3 Histórico de entrega

O histórico de entrega por cesta é preservado pelo fluxo normal e não é substituído pela data/horário agendados, registrando:

* cesta entregue;
* identificador textual do operador responsável (obrigatório);
* data/hora do registro de entrega.

### 14.4 Mecanismo provisório de identificação do responsável operacional

Nas operações que exigem auditoria operacional em M4 (alterações de composição, reabertura de venda pronta e registro de entrega individual):

1. **Entrada textual:** o operador informará seu nome ou identificador por meio de campo textual na interface.
2. **Persistência associada:** a informação informada é persistida junto ao registro ou evento auditado com sua data/hora.
3. **Validação de obrigatoriedade:** a ausência de identificador (campo vazio ou preenchido exclusivamente com espaços em branco) deve ser rejeitada pela validação de entrada, impedindo a conclusão da operação auditada.
4. **Ausência de autenticação:** o sistema não possui autenticação, gerenciamento de usuários, login ou controle de sessão nesta fase. Não se presume que autenticação exista.
5. **Declaração operacional:** o identificador textual é estritamente uma declaração operacional fornecida na interface, e não uma identidade autenticada ou prova irrefutável de quem efetivamente realizou a ação.
6. **Delimitação de escopo:** a criação de módulo de usuários, login, controle de acesso e autenticação segura permanece fora do escopo atual e exigirá decisão e especificação próprias no futuro.

## 15. Decisões pendentes que permanecem em aberto

As seguintes decisões permanecem intencionalmente abertas e bloqueiam ou condicionam aspectos da implementação:

* **Momento e marco da movimentação de estoque associada às vendas:** M4 não executa dedução ou movimentação de estoque. A definição de quando e em qual marco o estoque será baixado requer decisão explícita futura do Product Owner. Esta responsabilidade não pode ser atribuída por inferência ao M5 ou a qualquer outro milestone.
* **Fórmula definitiva de custo e eventual cálculo de preço sugerido:** continuam pendentes para fases futuras; o M4 adota estritamente preço manual acordado por cesta com snapshot imutável.
* **Autenticação e controle de acesso:** permanecem fora do escopo do M4; o mecanismo aprovado é puramente declaratório textual.

## 16. Explicitamente fora do escopo

Além dos itens já excluídos acima, permanecem fora de M4:

* módulos de usuário, autenticação, permissões, roles ou sessões;
* implementação de pagamentos e comprovantes;
* confirmação financeira fora do fluxo M5;
* descontos, promoções e regras de precificação avançada;
* renegociação excepcional pós-confirmação;
* devoluções, reembolsos e compensações financeiras;
* reserva, dedução, devolução ou correção automática de estoque;
* venda de produtos individuais fora do modelo centrado em cestas;
* assinatura, foto ou outros comprovantes de entrega;
* automações de notificação, comunicação ou logística.

## 17. Referências do marco

Este documento é a referência primária do comportamento funcional de M4.

Rastreabilidade complementar:

* Casos de uso: `docs/milestones/m4-sales/use-cases.md`
* Critérios de aceitação: `docs/milestones/m4-sales/acceptance-criteria.md`
* Plano de validação: `docs/milestones/m4-sales/validation.md`
* Resumo executivo: `docs/milestones/m4-sales/executive-summary.md`
* Plano de validação: `docs/milestones/m4-sales/validation.md`

Regras e contexto relacionados:

* `docs/domain/business-contract.md`
* `docs/milestones/m2-baskets/specification.md`
* `docs/milestones/m3-customers/specification.md`
* `docs/milestones/phase-1.md`
* `docs/product/roadmap.md`
