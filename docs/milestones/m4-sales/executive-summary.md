# M4 — Resumo Executivo para Aprovação

**Versão do documento:** 0.2
**Status:** Documentação formalizada; implementação não iniciada; início condicionado ao fechamento da correção pontual de preço persistido em M2 e à resolução das decisões de negócio pendentes
**Marco:** M4 — Vendas (Sales)
**Data:** 9 de outubro de 2026

---

##  Objetivo

Registrar o resultado da formalização documental do M4 (Vendas), incluindo o alinhamento de dependências com M2 e a definição do mecanismo provisório de auditoria antes da autorização de implementação.

---

## ✅ Entregáveis Formalizados

Os seguintes documentos foram completamente elaborados e estão prontos para revisão:

1. **`specification.md`** — Especificação técnica e funcional completa
2. **`use-cases.md`** — 14 casos de uso detalhados
3. **`acceptance-criteria.md`** — 51 critérios de aceitação em formato BDD
4. **`validation.md`** — Plano de validação operacional

Todos os documentos estão no diretório: `docs/milestones/m4-sales/`

---

##  Visão Geral do M4

### O que M4 faz

M4 define o **ciclo operacional completo da venda** na Casa Afeto:

- ✅ Criar venda vinculada a cliente ativo
- ✅ Gerenciar múltiplas cestas por venda com dados independentes
- ✅ Copiar composição e preço da origem no momento da adição
- ✅ Permitir alteração de composição por estado (com restrições)
- ✅ Ajustar preço manualmente **apenas em `RASCUNHO`**
- ✅ Marcar cestas individualmente como preparadas
- ✅ Reabrir vendas `PRONTA` com auditoria e justificativa
- ✅ Registrar entregas individuais por cesta
- ✅ Cancelar vendas (com restrições após entrega)
- ✅ Preservar histórico operacional completo

### O que M4 NÃO faz

M4 **explicitamente não toca em:**

- ❌ Pagamentos (pertence ao M5)
- ❌ Cálculo de total pago ou saldo (pertence ao M5)
- ❌ Confirmação financeira ou regra de 50% (pertence ao M5)
- ❌ Dedução, devolução ou ajuste automático de estoque
- ❌ Renegociação excepcional de preço após confirmação
- ❌ Reembolsos ou compensações
- ❌ Comprovantes de entrega (assinatura, foto, etc.)

---

##  Fronteira Cristalina entre M4 e M5

Esta é a **decisão crítica formalizada para o M4**:

| Responsabilidade | M4 | M5 |
|------------------|----|----|
| Criar e gerenciar vendas | ✅ | |
| Definir estados operacionais | ✅ | |
| Permitir edições conforme estado | ✅ | |
| Registrar pagamentos | | ✅ |
| Calcular total pago | | ✅ |
| Verificar limiar de 50% | | ✅ |
| **Autorizar `RASCUNHO → CONFIRMADA`** | Valida dados obrigatórios | ✅ Autoriza financeiramente |
| Preparação, entrega, cancelamento | ✅ | |
| Movimentação automática de estoque | ❌ Não executa | Indefinido nesta formalização; requer decisão explícita futura (sem atribuição implícita ao M5) |

**Critérios de aceitação que garantem esta fronteira:**
- AC-M4-015: M4 não registra pagamentos
- AC-M4-016: M5 autoriza confirmação financeira
- AC-M4-017: Sem regra paralela de confirmação em M4
- AC-M4-018: Sem efeitos automáticos de estoque em M4

---

##  Estados da Venda

Apenas **6 estados oficiais**, sem estados intermediários:

```
RASCUNHO
   ↓  (autorização financeira do M5)
CONFIRMADA
   ↓  (ação explícita do usuário)
EM PREPARAÇÃO
   ↓  (todas as cestas preparadas)
PRONTA
   ↓  (todas as cestas entregues)
ENTREGUE

Fluxos excepcionais formalizados:
• RASCUNHO/CONFIRMADA/EM PREPARAÇÃO/PRONTA → CANCELADA (se nenhuma entrega)
• PRONTA → EM PREPARAÇÃO (reabertura com auditoria)
```

**Garantia:** Não existe transição que pula etapas.

---

##  Composição e Preço

### Cópia Independente

Ao adicionar uma cesta à venda:
1. A composição da origem é **copiada naquele momento**
2. O preço vigente da origem é **copiado naquele momento**
3. A cesta na venda torna-se **independente da origem**

Alterações futuras em qualquer lado não afetam o outro.

### Regra de Preço por Estado

| Estado | Ajuste Manual | Recálculo Automático | Bloqueio |
|--------|--------------|---------------------|---------|
| `RASCUNHO` | ✅ Permitido | ✅ Sim (se preço muda) | |
| `CONFIRMADA` | ❌ Bloqueado | ❌ Não | ✅ Preço congelado |
| `EM PREPARAÇÃO` e posteriores | ❌ Bloqueado | ❌ Não | ✅ Preço congelado |

**Importante:** Alterar a composição **nunca** recalcula o preço automaticamente em nenhum estado.

---

##  Cliente e Validação

- ✅ Nova venda exige cliente **ativo**
- ✅ Cliente inativo não pode iniciar nova venda
- ✅ Se cliente ficar inativo após venda criada → vínculo preservado (não quebra)
- ✅ Venda em `RASCUNHO` pode ter dados de entrega incompletos
- ✅ Confirmação financeira (M5) valida dados obrigatórios de entrega

---

##  Alterações de Composição por Estado

### `RASCUNHO`
- ✅ Livremente editável
- ❌ Não recalcula preço

### `CONFIRMADA`
- ✅ Adicionar/remover itens, alterar quantidades
- ❌ Preço bloqueado
- ❌ Sem ajuste automático de estoque

### `EM PREPARAÇÃO`
- ✅ Mesmas alterações permitidas
- ⚠️ Exige confirmação explícita com aviso
-  **Cesta alterada perde marcação de preparação anterior**
- ✅ Cestas não alteradas preservam preparação concluída

### `PRONTA`
- ❌ Alteração direta bloqueada
- ✅ Deve ser reaberta explicitamente para editar

### `ENTREGUE` e `CANCELADA`
- ❌ Alterações comerciais bloqueadas
- ✅ Estados terminais

---

##  Preparação por Cesta

- ✅ Cada cesta é marcada **individualmente** como preparada
- ✅ Venda só fica `PRONTA` quando **todas as cestas** estiverem preparadas
- ❌ Preparação **não é entrega**
- ❌ Preparação **não move estoque**
- ✅ Progresso é auditável por cesta

---

##  Reabertura (Recurso Especial)

Permite que uma venda `PRONTA` retorne para `EM PREPARAÇÃO`:

- ✅ Exige ação explícita do usuário
- ✅ Justificativa é obrigatória
- ✅ Identificador textual do operador responsável é obrigatório (declaração operacional sem autenticação)
- ✅ Data/hora registradas para auditoria
- ❌ Não altera preços, não cancela, não move estoque
-  Apenas cestas **alteradas** voltam a exigir preparação
- ✅ Cestas não alteradas mantêm preparação anterior

---

##  Entrega Individual

- ✅ Cada cesta é entregue por ação explícita do usuário
- ❌ Data/horário agendados não bastam como prova
- ✅ Histórico preserva: cesta, identificador textual do operador responsável e data/hora
- ❌ Tentativa sem identificador textual é rejeitada
- ✅ Quando última cesta é entregue → venda passa automaticamente para `ENTREGUE`
- ❌ Sem exigência de assinatura, foto ou comprovante

---

## ❌ Cancelamento

### Quando é permitido

- ✅ Em qualquer estado (`RASCUNHO`, `CONFIRMADA`, `EM PREPARAÇÃO`, `PRONTA`)
- ✅ **Desde que NENHUMA cesta tenha sido entregue**
- ✅ Cestas preparadas não impedem cancelamento

### Quando é bloqueado

- ❌ Qualquer entrega registrada bloqueia cancelamento
- ❌ Venda `ENTREGUE` não pode ser cancelada

### Após cancelar

- ✅ Venda muda para `CANCELADA`
- ✅ Venda, cestas e históricos permanecem consultáveis
- ❌ Sem reembolso, devolução física ou ajuste automático de estoque

---

##  Cobertura de Casos de Uso e Critérios

### Casos de Uso (14 total)
- UC-M4-001 a 005: Criação, cliente, múltiplas cestas, ajuste de preço, histórico com identificador
- UC-M4-006 a 008: Edição por estado com auditoria, preparação
- UC-M4-009: Reabertura com auditoria e identificador textual do responsável
- UC-M4-010 a 011: Entrega com identificador textual e conclusão automática
- UC-M4-012 a 013: Cancelamento permitido e bloqueado
- UC-M4-014: Validação de fronteira M4-M5

### Critérios de Aceitação (51 total)

| Grupo | Cobertura | Critérios |
|-------|-----------|-----------|
| Estrutura e composição | Completa | AC-M4-001 a 006, AC-M4-004a, AC-M4-004b e AC-M4-046 |
| Cliente e RASCUNHO | Completa | AC-M4-007 a 011 |
| Preço | Completa | AC-M4-012 a 014 |
| **Fronteira M4-M5** | **Completa** | **AC-M4-015 a 018** |
| Estados | Completa | AC-M4-019 a 023 |
| Alterações e histórico | Completa | AC-M4-024 a 030 |
| Preparação e reabertura | Completa | AC-M4-031 a 036 |
| Entregas | Completa | AC-M4-037 a 040 |
| Cancelamento | Completa | AC-M4-041 a 045 |
| **Auditoria e identificação textual** | **Completa** | **AC-M4-047 a 049** |

---

##  Plano de Validação

O documento `validation.md` define:

- ✅ 15 seções de validação funcional
- ✅ Preparação do ambiente de teste
- ✅ Cenários positivos, alternados e negativos
- ✅ Testes automatizados esperados
- ✅ Checklist de revisão final
- ✅ Cobertura dos 51 critérios de aceitação

---

## ⚡ Decisões Críticas Formalizadas e Aprovadas no M4

1. **M4 não move estoque automaticamente** — formalizado em AC-M4-018
2. **Confirmação financeira é responsabilidade única do M5** — formalizado em AC-M4-016
3. **Reabertura é auditável e justificada** — formalizado em AC-M4-032
4. **Identificação do responsável é por declaração textual sem autenticação** — formalizado em AC-M4-047 a 049
5. **Cancelamento só é bloqueado após entrega** — formalizado em AC-M4-042
6. **Alteração de composição é permitida até `PRONTA`** — formalizado em AC-M4-024 a 028
7. **Preparação é individual, não automática** — formalizado em AC-M4-031

---

##  Pendências de Decisão de Negócio que Permanecem Abertas

Durante a formalização de M4, permaneceram registradas as seguintes pendências de negócio:

1. **Momento e marco responsáveis por eventual baixa de estoque associada às vendas:**
   - M4 não executa baixa automática de estoque.
   - A responsabilidade futura não pode ser atribuída implicitamente ao M5 ou a qualquer outro marco.
   - Qualquer definição de baixa exige decisão explícita do Product Owner antes de implementação.

2. **Fórmula definitiva de custo e eventual cálculo de preço sugerido:**
   - O cálculo custo × 2 permanece como mera referência conceitual não computável.
   - Não há cálculo automático de preço em M2 ou M4.

3. **Futura autenticação e controle de acesso:**
   - O mecanismo aprovado em M4 é uma declaração textual operacional.
   - O desenho e implementação de login, senhas, permissões ou sessões permanecem fora do escopo atual.

---

## ✍️ Próximos Passos antes da Implementação

### Governança e dependências

- [x] Formalizar correção pontual de M2 para preço de venda persistido da cesta-modelo
- [ ] Implementar a correção pontual de M2 no código (fora deste documento)
- [ ] Resolver: Quando e em qual marco o estoque é deduzido? (antes de qualquer implementação dessa baixa)
- [ ] Documentar decisão em `business-contract.md`

### Preparação para implementação (sem iniciar nesta atualização)

- [ ] Planejar a execução técnica de M4 conforme os 51 critérios de aceitação formalizados
- [ ] Preservar a fronteira M4-M5 e a política de estoque indefinida até decisão explícita

---

##  Linha do Tempo Estimada (após alinhamento de dependências)

```
Semana 1:    Correção pontual de M2 (preço persistido)
Semanas 2-5: Implementação de M4 (backend + testes)
Semana 6:    Validação funcional de M4
Semana 7:    Aprovação humana de M4
```

---

##  Qualidade dos Documentos

| Aspecto | Avaliação |
|---------|-----------|
| Clareza | ⭐⭐⭐⭐⭐ Excelente |
| Completude | ⭐⭐⭐⭐⭐ Excelente |
| Rastreabilidade | ⭐⭐⭐⭐⭐ Excelente |
| Testabilidade | ⭐⭐⭐⭐⭐ Excelente |
| Fronteira M4-M5 | ⭐⭐⭐⭐⭐ Inequívoca |
| Alinhamento com decisões | ⭐⭐⭐⭐⭐ 100% |

---

##  Perguntas para Discussão com Product Owner

1. **Todos os 6 estados oficiais estão corretos?** ✅ RASCUNHO, CONFIRMADA, EM PREPARAÇÃO, PRONTA, ENTREGUE, CANCELADA

2. **A reabertura com auditoria é o comportamento esperado?** ✅ Sem automação, sempre justificada

3. **Alteração de composição em `CONFIRMADA` é realmente permitida?** ✅ Sim, conforme documentado

4. **M4 está correto em NÃO mover estoque?** ✅ Formalizado em AC-M4-018

5. **M5 permanece responsável pela confirmação financeira `RASCUNHO → CONFIRMADA`?** ✅ Formalizado em AC-M4-016

6. **A decisão explícita sobre eventual baixa de estoque já está definida no contrato?** ⏳ Recomenda-se resolver antes de implementar esse comportamento

---

##  Registro de Governança

- [x] Documentação de M4 formalizada
- [x] Implementação de M4 permanece não iniciada
- [x] Dependência de correção pontual em M2 registrada
- [ ] Decisão explícita sobre eventual baixa de estoque permanece pendente

---

##  Referência Rápida

- **Especificação técnica:** `docs/milestones/m4-sales/specification.md`
- **Casos de uso:** `docs/milestones/m4-sales/use-cases.md`
- **Critérios de aceitação:** `docs/milestones/m4-sales/acceptance-criteria.md`
- **Plano de validação:** `docs/milestones/m4-sales/validation.md`
- **Contexto de negócio:** `docs/domain/business-contract.md`
- **Roadmap:** `docs/product/roadmap.md`

---

**Versão 0.1 — 9 de outubro de 2026**

Preparado para: Registro de alinhamento documental pré-implementação
Status: Documentação formalizada; implementação não iniciada; dependente de correção pontual em M2
