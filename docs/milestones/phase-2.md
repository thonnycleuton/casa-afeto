# Casa Afeto — Fase 2

**Versão do documento:** 0.1 (Rascunho)
**Status:** Rascunho — pendente de aprovação final
**Fase:** 2 — Evolução do Estoque e dos Clientes

---

## 1. Finalidade

A Fase 2 estende o fluxo operacional central da Fase 1 com capacidades de gestão de compras, lotes de estoque, vencimentos, reposição e datas afetivas.

O objetivo é permitir que a Casa Afeto:

* registre as origens do estoque (compras);
* gerencie estoque por lote e vencimento;
* identifique necessidades de reposição;
* mantenha relacionamento proativo com clientes via datas afetivas.

A Fase 2 segue o mesmo princípio da Fase 1:

> Construa pouco, valide, aprenda e depois construa a próxima coisa.

Cada marco deve ser implementado, testado e validado manualmente antes que o próximo marco comece.

---

## 2. Sequência de Desenvolvimento da Fase 2

A Fase 2 é dividida em marcos. A sequência proposta é:

```text
M6 — Compras e Reposição de Estoque
        ↓
M7 — Lotes de Estoque (pendente de especificação)
        ↓
M8 — Vencimentos (pendente de especificação)
        ↓
M9 — Reposição de Estoque (pendente de especificação)
        ↓
M10 — Datas Afetivas (pendente de especificação)
```

A ordem reflete as dependências naturais:

* **M6 (Compras)** é a base — sem compras, não há lotes nem vencimentos.
* **M7 (Lotes)** depende de M6 — os lotes surgem das aquisições.
* **M8 (Vencimentos)** depende de M7 — vencimentos são propriedade de lotes.
* **M9 (Reposição)** depende de M6 — identifica estoque insuficiente para compras.
* **M10 (Datas Afetivas)** é independente — pode ser desenvolvido em paralelo.

---

## 3. Estado Atual dos Marcos

| Marco | Status | Documentos |
|-------|--------|------------|
| M6 — Compras | Concluído (COMPLETED) | specification.md, acceptance-criteria.md, use-cases.md, validation.md |
| M7 — Lotes de Estoque | 📝 Rascunho | specification.md, acceptance-criteria.md, use-cases.md, validation.md |
| M8 — Vencimentos | ✗ Não planejado | — |
| M9 — Reposição de Estoque | ✗ Não planejado | — |
| M10 — Datas Afetivas | ✗ Não planejado | — |

---

## 4. Marco M7 — Lotes de Estoque

### Objetivo

Introduzir o conceito de lote de estoque, permitindo que cada aquisição de produto seja rastreada como um grupo distinto com custo unitário próprio, quantidade restante e data de entrada. O consumo de estoque segue a estratégia FIFO (First-In-First-Out).

### Documentos

```text
docs/milestones/m7-stock-batches/
├── specification.md          — Especificação detalhada (v0.1, rascunho)
├── acceptance-criteria.md    — 24 critérios de aceitação (v0.1, rascunho)
├── use-cases.md              — 6 casos de uso (v0.1, rascunho)
└── validation.md             — Plano de validação (v0.1, rascunho)
```

### Regras de Negócio

10 regras novas (LOT-001 a LOT-010).

### Decisões do Product Owner

- **D-1:** Lote automático por item de compra
- **D-2:** FIFO como estratégia de consumo
- **D-3:** Remoção do custo médio ponderado

### Dependências

- M1 — Produtos e Estoque (base)
- M6 — Compras (lotes surgem das aquisições)

### Status

- Especificação: Rascunho v0.1 — pendente de aprovação final
- Implementação: Não iniciada

---

## 5. Marco M6 — Compras (Concluído)

### Objetivo

Introduzir o registro de compras recebidas pela Casa Afeto, permitindo que o operador registre a aquisição de produtos com suas unidades comerciais, fatores de conversão e preços pagos, gerando automaticamente as movimentações de estoque correspondentes.

### Documentos

```text
docs/milestones/m6-purchases/
├── specification.md          — Especificação detalhada (v0.3, rascunho)
├── acceptance-criteria.md    — 21 critérios de aceitação (v0.1, rascunho)
├── use-cases.md              — 6 casos de uso (v0.1, rascunho)
└── validation.md             — Plano de validação (v0.1, rascunho)
```

### Regras de Negócio

12 regras novas (PUR-001 a PUR-012), preservando as regras existentes (INV-*, RES-*, PROD-*).

### Dependências

* M1 — Produtos e Estoque (base)
* M5 — Pagamentos (regras de reserva e baixa)

### Status

* Status: Concluído (COMPLETED) — Implementação, testes e frontend concluídos

---

## 6. Marcos Futuros (Rascunho)

### M8 — Vencimentos

**Objetivo:** Gerenciar datas de vencimento dos produtos e alertar sobre produtos próximos do vencimento.

**Dependência:** M7 (Lotes) — vencimentos são propriedade de lotes.

**Capacidades esperadas:**
* Registrar data de vencimento por lote.
* Listar produtos próximos do vencimento.
* Alertar sobre estoque vencido.
* Política FEFO (First Expired, First Out) como regra substituível.

---

### M9 — Reposição de Estoque

**Objetivo:** Identificar produtos com estoque insuficiente e destacar a necessidade de reposição.

**Dependência:** M6 (Compras) — precisa de contexto de aquisição.

**Capacidades esperadas:**
* Identificar produtos necessários para cestas futuras.
* Destacar produtos com estoque abaixo do necessário.
* Distinguir necessidades normais de necessidades urgentes (vendas confirmadas).

**Princípio:** Visibilidade antes de automação.

---

### M10 — Datas Afetivas

**Objetivo:** Registrar e gerenciar datas importantes dos clientes para contato proativo.

**Dependência:** M3 (Clientes) — independente dos outros marcos da Fase 2.

**Capacidades esperadas:**
* Registrar datas importantes (aniversário, ocasiões especiais).
* Listar datas próximas.
* Notificar o negócio sobre datas afetivas.

---

## 7. Gates de Início

Cada marco da Fase 2 só pode começar quando:

1. O marco anterior (se houver dependência) está COMPLETED.
2. A especificação está aprovada pelo Product Owner.
3. Os acceptance criteria estão definidos.
4. Os use cases estão documentados.
5. O plano de validação está pronto.
6. As decisões pendentes estão resolvidas.
7. O `validate_spec_casa.py` passa sem erros.

---

*Fim do documento da Fase 2.*
