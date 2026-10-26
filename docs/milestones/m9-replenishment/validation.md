# M9 — Plano de Validação

**Versão do documento:** 0.2 (Aprovado)
**Status:** Aprovado — validado pelo Product Owner
**Marco:** M9 — Reposição de Estoque

---

## 1. Cenários de Validação Manual

### Cenário 1 — Lista de reposição com produtos OK

**Passos:**
1. Criar 2 produtos com estoque suficiente;
2. Criar 1 template de cesta com esses produtos;
3. Acessar a seção "Reposição";
4. Verificar que ambos os produtos aparecem com status OK.

**Resultado esperado:** Ambos os produtos têm status OK (badge verde).

---

### Cenário 2 — Produto com estoque BAIXO

**Passos:**
1. Criar 1 produto com estoque 2;
2. Criar 1 template de cesta com esse produto na quantidade 5;
3. Acessar a seção "Reposição";
4. Verificar que o produto aparece com status BAIXO.

**Resultado esperado:** O produto tem status BAIXO (badge amarelo), shortage = 3.

---

### Cenário 3 — Produto com estoque CRÍTICO

**Passos:**
1. Criar 1 produto com estoque 1;
2. Criar 1 venda CONFIRMADA com esse produto na quantidade 3;
3. Acessar a seção "Reposição";
4. Verificar que o produto aparece com status CRÍTICO.

**Resultado esperado:** O produto tem status CRÍTICO (badge vermelho), shortage = 2.

---

### Cenário 4 — Filtro por status CRÍTICO

**Passos:**
1. Ter produtos com status OK, BAIXO e CRÍTICO;
2. Clicar no filtro "CRÍTICO";
3. Verificar que apenas os produtos CRÍTICO aparecem.

**Resultado esperado:** Apenas produtos CRÍTICO são exibidos.

---

### Cenário 5 — Venda cancelada não afeta reposição

**Passos:**
1. Criar 1 venda CONFIRMADA com 1 produto;
2. Verificar que o produto aparece como CRÍTICO ou BAIXO;
3. Cancelar a venda;
4. Recarregar a seção "Reposição";
5. Verificar que o produto mudou para OK ou BAIXO.

**Resultado esperado:** A venda cancelada não contribui mais para a necessidade urgente.

---

### Cenário 6 — Template inativo não afeta reposição

**Passos:**
1. Criar 1 template ativo com 1 produto;
2. Verificar que o produto aparece na lista de reposição;
3. Desativar o template;
4. Recarregar a seção "Reposição";
5. Verificar que a necessidade estimada do produto diminuiu.

**Resultado esperado:** O template inativo não contribui para a necessidade estimada.

---

## 2. Checklist Técnico

### Backend

- [ ] Endpoint `GET /api/v1/inventory/replenishment` retorna lista correta
- [ ] Estoque calculado a partir dos lotes ativos (LOT-008)
- [ ] Necessidade estimada calculada a partir dos templates ativos
- [ ] Necessidade urgente calculada a partir das vendas CONFIRMADA/EM_PREPARAÇÃO/PRONTA
- [ ] Status OK/BAIXO/CRÍTICO classificado corretamente
- [ ] Filtro por status funciona
- [ ] Filtro por produto funciona
- [ ] Shortage calculado corretamente (mínimo 0)
- [ ] Venda CANCELADA não gera necessidade
- [ ] Venda ENTREGUE não gera necessidade
- [ ] Template inativo não gera necessidade
- [ ] Produto sem necessidade é classificado como OK
- [ ] 163 testes existentes continuam passando (sem regressões)
- [ ] Novos testes M9 passam

### Frontend

- [ ] Seção "Reposição" na navegação lateral
- [ ] Tabela com colunas: Produto, Estoque, Necessidade Estimada, Necessidade Urgente, Falta, Status
- [ ] Badges coloridos: verde (OK), amarelo (BAIXO), vermelho (CRÍTICO)
- [ ] Filtros por status funcionam
- [ ] Estado vazio exibido quando todos os produtos estão OK
- [ ] `vue-tsc --noEmit` sem erros novos

### Documentação

- [ ] Regras REP-001 a REP-010 adicionadas ao `business-contract.md`
- [ ] `phase-2.md` atualizado com M9
- [ ] `roadmap.md` atualizado com M9
- [ ] `validate_spec_casa.py` passa na spec do M9

---

## 3. Critérios de Conclusão

O M9 está concluído quando:

1. Todos os 15 ACs de backend estão implementados e testados;
2. Todos os 5 ACs de frontend estão implementados;
3. Os 6 cenários manuais passam;
4. O checklist técnico está 100% marcado;
5. A documentação está aprovada;
6. `validate_spec_casa.py` passa sem erros;
7. A suite completa de testes passa sem regressões.

---

*Fim do plano de validação do M9.*
