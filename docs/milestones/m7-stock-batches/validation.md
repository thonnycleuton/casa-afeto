# M7 — Plano de Validação

**Versão do documento:** 0.1 (RASCUNHO)
**Marco:** M7 — Lotes de Estoque
**Fase:** 2 — Evolução do Estoque e dos Clientes

---

## 1. Validação Automatizada

### Testes de Backend

Executar após a implementação:

```bash
cd backend && python -m pytest tests/test_m7_stock_batches.py -v
```

Cobertura esperada: 24 testes mapeados aos 24 critérios de aceitação.

### Testes de Frontend

Verificar que o modal de estoque exibe os lotes corretamente:

```bash
cd frontend && npx vue-tsc --noEmit
```

### Validação do formato da especificação

```bash
python3 scripts/tlc/validate_spec_casa.py docs/milestones/m7-stock-batches/specification.md
```

---

## 2. Validação Manual

### Cenário 1: Criar compra e verificar lotes

1. Cadastrar um produto ativo (ex: "Arroz 5kg", UN).
2. Registrar uma compra com 1 item: 2 caixas de 24 unidades a R$ 120,00/caixa.
3. Abrir o modal de estoque do produto.
4. **Esperado:** 1 lote ativo com 48 unidades, `unit_cost = 5,00`, origem = compra.

### Cenário 2: Entrada manual gera lote

1. No modal de estoque, registrar entrada manual: 10 unidades a R$ 6,00.
2. **Esperado:** Novo lote com 10 unidades, `unit_cost = 6,00`, origem = manual.

### Cenário 3: Consumo FIFO

1. Com os lotes do Cenário 1 (48 un) e Cenário 2 (10 un), criar uma venda com cesta contendo 50 unidades de Arroz.
2. Confirmar e iniciar preparação (baixa física).
3. **Esperado:** Lote da compra fica com 0 (EXHAUSTED), lote manual fica com 8.

### Cenário 4: Estoque insuficiente

1. Tentar saída de 100 unidades quando só há 8 disponíveis.
2. **Esperado:** Saída rejeitada com erro de estoque insuficiente.

### Cenário 5: Custo médio removido

1. Consultar o produto via API: `GET /api/v1/products/{id}`.
2. **Esperado:** Resposta não contém `average_cost`.

### Cenário 6: Rastreabilidade

1. Clicar no lote criado pela compra.
2. **Esperado:** Detalhe mostra a compra de origem com data, item e valores.

---

## 3. Checklist de Validação

- [ ] Todos os 24 testes de backend passam
- [ ] `vue-tsc --noEmit` sem erros novos
- [ ] `validate_spec_casa.py` passa
- [ ] Cenário 1: lote criado pela compra ✓
- [ ] Cenário 2: lote criado por entrada manual ✓
- [ ] Cenário 3: consumo FIFO funciona ✓
- [ ] Cenário 4: estoque insuficiente rejeitado ✓
- [ ] Cenário 5: custo médio removido da API ✓
- [ ] Cenário 6: rastreabilidade lote → compra ✓
- [ ] Modal de estoque exibe lotes corretamente ✓
- [ ] Custo médio não aparece no frontend ✓
- [ ] Migração de dados existentes (se houver) ✓

---

## 4. Critérios de Conclusão

O M7 está completo quando:

1. Todos os 24 critérios de aceitação têm testes automatizados passando.
2. A validação manual é concluída sem falhas.
3. O Product Owner aprova o comportamento dos lotes.
4. A documentação está atualizada (business-contract, roadmap, phase-2).
5. Não há regressões nos testes existentes (M1–M6).

---

*Fim do plano de validação do M7.*
