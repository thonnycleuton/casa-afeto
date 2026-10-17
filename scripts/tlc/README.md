# Casa Afeto — TLC Validation Scripts

Scripts de validação determinística adaptados do [TLC-Spec-Driven](https://github.com/tech-leads-club/agent-skills) para o Casa Afeto.

Estes scripts tornam os gates de qualidade **automáticos** — o agente não pode "esquecer" validar porque o script falha com exit code não-zero.

---

## Scripts

### validate_spec.py (TLC Original)

Valida especificações no formato `.specs/` do TLC-Spec-Driven. **Não use diretamente** para os milestones do Casa Afeto — use `validate_spec_casa.py` abaixo.

### validate_spec_casa.py ⭐ (Recomendado)

Valida especificações no **formato Casa Afeto** (`docs/milestones/<milestone>/specification.md`).

**O que verifica:**
- Seções obrigatórias: Objetivo, Escopo, Fora do Escopo
- Seções recomendadas: Dependências, Decisões Pendentes
- Critérios de aceitação testáveis (palavras-chave: deve, rejeita, aceita, etc.)
- Formato Given/When/Then nos critérios
- Decisões pendentes não resolvidas
- IDs de regras de negócio (PAY-001, RES-001, etc.)

**Uso:**
```bash
# Validar spec do M5
python3 scripts/tlc/validate_spec_casa.py docs/milestones/m5-payments/

# Validar spec específico
python3 scripts/tlc/validate_spec_casa.py docs/milestones/m5-payments/specification.md

# Modo strict (warnings também falham)
python3 scripts/tlc/validate_spec_casa.py --strict docs/milestones/m5-payments/
```

**Quando usar:** Antes de confirmar uma spec com o Product Owner.

---

### validate_tasks.py

Valida que o plano de tasks tem granularidade adequada e consistência nas dependências.

**O que verifica:**
- Cada task tem descrição clara
- Dependências são consistentes (sem ciclos)
- Tasks têm testes associados

**Uso:**
```bash
python3 scripts/tlc/validate_tasks.py docs/milestones/m5-payments/tasks.md
```

**Quando usar:** Antes de começar a implementação de um milestone.

---

### check_commit.py

Valida que mensagens de commit seguem o formato Conventional Commits.

**O que verifica:**
- Tipo do commit (feat, fix, docs, refactor, test, chore)
- Scope opcional
- Descrição clara

**Uso:**
```bash
# Validar último commit
python3 scripts/tlc/check_commit.py

# Validar commits desde um tag
python3 scripts/tlc/check_commit.py --since v1.0.0
```

**Quando usar:** Em cada commit durante a implementação.

---

### validate_state.py

Valida que uma feature está realmente completa.

**O que verifica:**
- validation.md existe
- Veredicto é PASS
- Evidências apontam para file:line reais

**Uso:**
```bash
python3 scripts/tlc/validate_state.py docs/milestones/m5-payments/
```

**Quando usar:** Ao final da implementação de um milestone.

---

### lessons.py

Gerencia o Lessons Layer — aprendizados a partir de falhas de validação.

**Comandos:**
```bash
# Adicionar uma lição
python3 scripts/tlc/lessons.py add \
  --feature "M5-Pagamentos" \
  --signal surviving_mutant \
  --source "scripts/tlc/discrimination_sensor.py:108" \
  --text "Docstrings multi-linha devem ser ignoradas no discrimination sensor" \
  --scope "M5-Pagamentos"

# Listar lições confirmadas
python3 scripts/tlc/lessons.py list --status confirmed

# Listar lições por escopo
python3 scripts/tlc/lessons.py list --scope "M5"

# Ver status geral
python3 scripts/tlc/lessons.py status
```

**Quando usar:** Após cada falha de validação, para registrar o aprendizado.

---

### discrimination_sensor.py

Mutation testing — injeta falhas intencionais no código para verificar se os testes realmente detectam regressões.

**O que faz:**
- Inverte condições booleanas (== para !=, > para <=)
- Altera valores de retorno (True/False, None)
- Troca operadores lógicos (and/or, not)
- Executa os testes após cada mutação
- Reporta quais mutações foram detectadas (killed) e quais passaram despercebidas (survived)

**Uso:**
```bash
# Testar um arquivo específico
python3 scripts/tlc/discrimination_sensor.py backend/app/payments/service.py \
  --test-cmd "cd backend && python -m pytest tests/test_payments.py -x"

# Testar um diretório
python3 scripts/tlc/discrimination_sensor.py backend/app/payments/ \
  --test-cmd "cd backend && python -m pytest tests/test_payments.py -x"

# Dry run — mostra mutações sem aplicar
python3 scripts/tlc/discrimination_sensor.py backend/app/payments/service.py \
  --test-cmd "cd backend && python -m pytest tests/test_payments.py -x" --dry-run

# Limitar número de mutações
python3 scripts/tlc/discrimination_sensor.py backend/app/payments/ \
  --test-cmd "cd backend && python -m pytest tests/test_payments.py -x" -m 10
```

**Quando usar:** Para features críticas (pagamentos, estoque, auth) após escrever os testes.

**Exit codes:**
- `0` — Todas as mutações foram detectadas pelos testes
- `1` — Algumas mutações sobreviveram (testes fracos)
- `2` — Erro (arquivo não encontrado, syntax error, etc.)

---

## Integração com AGENTS.md

Os scripts são referenciados no `AGENTS.md` nas seções:

- **Seção 12 (Tests):** Test Adequacy Review com evidence-or-zero rule
- **Seção 13 (Validation):** Gates determinísticos antes de declarar tarefa completa
- **Seção 17 (Technical Principles):** Discrimination Sensor para features críticas

O agente deve executar os scripts nos momentos apropriados do workflow, não apenas confiar na memória para validar.

---

## Lessons Layer

O arquivo `lessons.json` armazena os aprendizados do projeto. É carregado automaticamente pelo `lessons.py` e deve ser consultado antes de começar um novo milestone.

Formato de cada lição:
```json
{
  "id": "LESSON-001",
  "scope": "M5-Pagamentos",
  "text": "Descrição da lição",
  "context": "Como foi descoberta",
  "status": "confirmed",
  "corroboration_count": 1,
  "created_at": "2026-10-17"
}
```

Status:
- `candidate` — Lição recém-criada, precisa de confirmação
- `confirmed` — Lição confirmada por múltiplas ocorrências
- `quarantined` — Lição em dúvida, pode ser removida

---

## Test Coverage Matrix

Para cada novo milestone, o agente deve gerar uma matriz de cobertura de testes antes de implementar.

Formato sugerido (adicionar ao `acceptance-criteria.md` ou arquivo separado):

```markdown
## Test Coverage Matrix

| AC ID | Teste | Arquivo | Linha | Status |
|-------|-------|---------|-------|--------|
| AC-M5-001 | test_payment_linked_to_sale | tests/test_payments.py | 42 | ✓ |
| AC-M5-002 | test_payment_value_must_be_positive | tests/test_payments.py | 58 | ✓ |
| AC-M5-003 | test_payment_method_valid | tests/test_payments.py | 75 | ✓ |
```

Cada AC deve ter um teste mapeado com `arquivo:linha` exata. ACs sem teste são marcados como `✗` e devem ser cobertos antes de fechar o milestone.

---

## Test Adequacy Review

Após cada tarefa, execute os 4 checks:

**Check A — Cobertura suficiente:** Cada AC mapeado para `file:line` + expressão de asserção.

**Check B — Não-shallow litmus:** Rejeita testes triviais que apenas verificam getters/setters.

**Check C — Necessidade:** Cada teste mapeado para um requisito real.

**Check D — Conformidade:** Os testes seguem as guidelines do projeto.

A **evidence-or-zero rule** exige que cada critério coberto cite `arquivo:linha` exata. Sem evidência, o AC não está coberto.
