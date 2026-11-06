# Casa Afeto — Auditoria do Módulo de Compras

**Data:** 2026-11-05
**Status:** Rascunho — pendente de aprovação do Product Owner
**Escopo:** Análise read-only. Nenhuma alteração foi feita no código, testes, documentação, banco ou migrations.

---

## 1. Resumo Executivo

O módulo de compras do Casa Afeto possui uma base sólida no M6 (compras manuais com conversão de unidades) e uma implementação significativa no M13 (importação OCR com Gemini). No entanto, a auditoria identificou **quatro áreas críticas** que precisam de atenção antes que o módulo esteja coerente e funcional:

1. **Compra em aberto não existe.** Não há mecanismo de rascunho/persistência de compra não confirmada. O M6 registra compra diretamente no estoque e o M13 mantém dados apenas em memória volátil.
2. **Documento original é excluído após processamento OCR.** A política D-13 exclui o arquivo após o OCR, mas o requisito de produto pede preservação do documento associado à compra confirmada.
3. **Fator de conversão é silenciosamente assumido como 1.** O frontend atribui `conversion_factor = '1'` automaticamente em três pontos do OCRImportModal e no PurchasesView, sem verificar se a unidade comercial difere da unidade base.
4. **Descontos são capturados pelo OCR mas não influenciam o custo.** O schema `OCRDiscount` existe e o Gemini extrai descontos, mas nenhum desconto é aplicado ao `commercial_unit_price` ou ao `unit_cost` da ENTRY.

Além disso, a **interface implementada diverge significativamente do mockup** — o mockup mostra um layout sofisticado com sidebar, abas e painel financeiro, enquanto a implementação atual usa um modal simples com tabela plana.

---

## 2. Diagnóstico por Tema

### 2.1 Tema A — Compra em Aberto

**O que se espera (decisões de produto):**
- Uma compra em aberto deve ser persistida no banco.
- Deve permitir retomada após fechar e reabrir o sistema.
- Pode ser criada manualmente ou por importação.
- Não movimenta estoque enquanto estiver aberta.
- Sua confirmação efetiva a compra e gera as movimentações de estoque.

**O que existe:**

| Aspecto | Estado | Evidência |
|---------|--------|-----------|
| Compra manual (M6) | ❌ Sem rascunho | `purchases/service.py:26` — `create_purchase()` persiste e gera ENTRY imediatamente |
| Compra por OCR (M13) | ⚠️ Em memória volátil | `ocr/state.py:20-100` — `OCRSessionStore` é um dicionário em memória |
| Persistência de rascunho | ❌ Inexistente | Nenhuma tabela `purchase_drafts` ou campo `status` em `Purchase` |
| Retomada após restart | ❌ Perdida | `ocr/state.py` — dados perdidos se o backend reiniciar (D-12) |
| Movimentação condicional | ❌ Sempre imediata | `purchases/service.py:89-98` — ENTRY criada dentro de `create_purchase()` |

**Problemas identificados:**

1. **M6 não tem conceito de rascunho.** A especificação do M6 (§2.2) declara explicitamente "fluxo de rascunho de compra" como fora do escopo. A decisão de produto atual requer este fluxo.
2. **M13 perde dados no restart do backend.** A decisão D-12 aceita perda de dados se o servidor reiniciar, mas a decisão de produto exige persistência e retomada.
3. **Não há distinção entre compra pendente e compra confirmada.** O modelo `Purchase` não tem campo `status`.

**Estruturas a preservar:**
- `create_purchase()` em `purchases/service.py:26-104` — lógica de conversão, validação e criação atômica de ENTRY.
- `OCRSessionStore` em `ocr/state.py` — gerenciamento de sessão com lock thread-safe.

---

### 2.2 Tema B — Dados Fiscais e Documento Original

**O que se espera (decisões de produto):**
- Dados fiscais são opcionais e complementares.
- Preservar dados originais do documento, inclusive não utilizados.
- Preservar o documento original (imagem/arquivo) associado à compra, inclusive após confirmação.
- Diferenciar dados originais do OCR, dados corrigidos pelo operador e valores calculados.

**O que existe:**

| Aspecto | Estado | Evidência |
|---------|--------|-----------|
| `access_key` em Purchase | ✅ Implementado | `purchases/models.py:33-35`, migration `m13_add_access_key.py` |
| `document_discounts` no OCR | ✅ Capturado | `ocr/schemas.py:68` — lista de `OCRDiscount` na sessão |
| `discounts` por item | ✅ Capturado | `ocr/schemas.py:33` — lista de `OCRDiscount` em `OCRItem` |
| `subtotal_printed` vs `subtotal_calculated` | ✅ Diferenciado | `ocr/schemas.py:31-32` |
| Documento original preservado | ❌ Excluído | `ocr/service.py:110-113` — `_delete_file_silent()` após OCR concluído |
| Dados fiscais persistidos | ❌ Não persistidos | `Purchase` tem apenas `access_key`; não há `supplier_name`, `cnpj`, `invoice_number`, etc. |
| Diferenciação original vs corrigido | ⚠️ Parcial | `OCRItem` tem dados originais, mas `ConfirmedItem` sobreescreve sem preservar o original |

**Problemas identificados:**

1. **Documento original é excluído após OCR.** `ocr/service.py:110-113` deleta o arquivo temporário assim que o processamento conclui. O requisito exige preservação associada à compra confirmada.
2. **Dados fiscais não são persistidos.** O mockup mostra `supplier_name`, `cnpj`, `invoice_number`, `protocol`, `taxes` — nenhum destes é armazenado no modelo `Purchase`.
3. **Dados originais do OCR são perdidos na confirmação.** Quando `confirm_import()` chama `_build_create_purchase()`, os dados originais (descrição extraída, subtotal impresso, descontos) não são preservados — apenas os dados confirmados vão para `CreatePurchase`.
4. **`document_discounts` não são persistidos.** Os descontos de nível documento são capturados na sessão OCR mas não vão para o banco.

**Estruturas a preservar:**
- `access_key` com constraint UNIQUE em `purchases` — prevenção de duplicidade (D-8).
- `subtotal_printed` / `subtotal_calculated` em `OCRItem` — diferenciação de valores.
- `OCRDiscount` schema — estrutura de desconto com `nature`, `item_id`, `document_level`.

---

### 2.3 Tema C — Conversão de Unidades

**O que se espera (decisões de produto):**
- Reutilizar regras existentes do M6.
- Não duplicar lógica de conversão no OCR.
- OCR só extrai fator quando explicitamente indicado no documento.
- Fator cadastrado no produto pode ser sugerido, mas deve ser coerente.
- Quando não houver fator conhecido e as unidades forem diferentes, não assumir 1 silenciosamente.

**O que existe:**

| Aspecto | Estado | Evidência |
|---------|--------|-----------|
| Conversão em `create_purchase()` | ✅ Correta | `purchases/service.py:67-71` — `base_qty = qty × factor`, `unit_cost = price / factor` |
| `commercial_conversion_factor` no Produto | ✅ Campo existe | `products` table, migration `f1a2b3c4d5e6` |
| Uso do fator do produto | ❌ Não utilizado | Nenhum código consulta `product.commercial_conversion_factor` para sugerir |
| OCR extrai fator | ⚠️ Parcial | `ocr/schemas.py:37` — `conversion_factor` é nullable em `OCRItem` |
| Frontend assume fator = 1 | ❌ Problema | `OCRImportModal.vue:275,327,354` — atribuição automática de `'1'` |
| Frontend manual assume fator = 1 | ❌ Problema | `PurchasesView.vue:101,112` — `conversion_factor: '1'` em `beginCreate()` e `addItem()` |

**Problemas identificados:**

1. **Atribuição silenciosa de `conversion_factor = '1'` em três locais do OCRImportModal:**
   - `OCRImportModal.vue:275` — ao fazer matching de produto: `sessionItems.value[index].conversion_factor = '1'`
   - `OCRImportModal.vue:327` — ao criar produto rápido: `sessionItems.value[index].conversion_factor = '1'`
   - `OCRImportModal.vue:354` — ao inicializar lotes: `conversion_factor: item.conversion_factor || '1'`

2. **Atribuição silenciosa no formulário manual:**
   - `PurchasesView.vue:101` — `beginCreate()`: `conversion_factor: '1'`
   - `PurchasesView.vue:112` — `addItem()`: `conversion_factor: '1'`

3. **`commercial_conversion_factor` do produto não é utilizado.** O campo existe no banco (migration `f1a2b3c4d5e6`) e no tipo frontend (`types.ts:47`), mas nenhum código o consulta para sugerir o fator de conversão.

4. **Sem validação de coerência.** Quando o operador informa `commercial_unit = 'caixa'` mas deixa `conversion_factor = '1'`, o sistema aceita sem alertar que 1 caixa = 1 unidade base pode estar errado.

5. **OCR não popula `conversion_factor`.** O Gemini pode extrair `commercial_unit` mas não extrai `conversion_factor` — o campo chega como `null` e o frontend preenche com `'1'`.

**Estruturas a preservar:**
- Cálculo em `purchases/service.py:67-71` — fórmula correta de conversão.
- Validação PUR-005 em `purchases/service.py:48-52` — rejeição de quantidade fracionária para UN.
- `commercial_conversion_factor` em `products` — campo que pode servir como sugestão.

---

### 2.4 Tema D — Descontos nos Itens e na Compra

**O que se espera (decisões de produto):**
- Diferenciar preço unitário bruto, subtotal bruto, desconto do item, total líquido, desconto geral, total do documento e total calculado.
- Preservar valor de desconto originalmente extraído.
- Permitir correção pelo operador sem perder o valor original.
- Diferenciar desconto por item de desconto geral.
- Identificar como descontos influenciam o custo de entrada no estoque.

**O que existe:**

| Aspecto | Estado | Evidência |
|---------|--------|-----------|
| `discounts` em `OCRItem` | ✅ Capturado | `ocr/schemas.py:33` — lista de `OCRDiscount` |
| `document_discounts` em `OCRSession` | ✅ Capturado | `ocr/schemas.py:68` |
| `subtotal_printed` em `OCRItem` | ✅ Capturado | `ocr/schemas.py:31` |
| `subtotal_calculated` em `OCRItem` | ✅ Capturado | `ocr/schemas.py:32` |
| Desconto aplicado ao preço | ❌ Não aplicado | `ocr/service.py:441-493` — `_build_create_purchase()` ignora `discounts` |
| Desconto persistido | ❌ Não persistido | `PurchaseItem` não tem campo de desconto |
| Desconto influencia `unit_cost` | ❌ Não influencia | `purchases/service.py:69-71` — `unit_cost = price / factor`, sem desconto |
| `extracted_total` vs `launched_total` | ✅ Implementado | `ocr/service.py:496-553` — cálculo dos três totais |
| Divergência alertada | ⚠️ Parcial | `ocr/service.py:321-324` — `extracted_total` retornado, mas sem bloqueio |

**Problemas identificados:**

1. **Descontos capturados mas ignorados na confirmação.** O Gemini extrai descontos (D-18), o schema os preserva, mas `_build_create_purchase()` em `ocr/service.py:441-493` não os considera ao montar `CreatePurchase`.

2. **`PurchaseItem` não tem campo de desconto.** O modelo `purchases/models.py:42-82` não armazena desconto por item nem desconto geral da compra.

3. **`unit_cost` não reflete descontos.** A fórmula `unit_cost = commercial_unit_price / conversion_factor` em `purchases/service.py:69-71` usa o preço bruto, não o preço líquido após desconto.

4. **D-18 diz "descontos ignorados no M13".** A decisão aprovada explicitamente declara que o operador informa o preço líquido manualmente. Isso significa que a implementação atual está correta conforme D-18, mas **não atende ao requisito de produto** que pede modelagem de descontos.

5. **Reconciliação de totais incompleta.** O sistema calcula `extracted_total` e `launched_total`, mas não compara explicitamente com `document_total` para alertar o operador sobre divergências causadas por descontos.

**Estruturas a preservar:**
- `OCRDiscount` schema com `nature`, `item_id`, `document_level` — estrutura adequada.
- `subtotal_printed` / `subtotal_calculated` — diferenciação de valores.
- Cálculo de `extracted_total` / `launched_total` em `ocr/service.py:496-553`.

---

## 3. Proposta de Modelagem

### 3.1 Estruturas Existentes a Preservar

| Estrutura | Localização | Motivo |
|-----------|-------------|--------|
| `Purchase` model | `purchases/models.py:20-39` | Entidade central de compra |
| `PurchaseItem` model | `purchases/models.py:42-82` | Itens com conversão de unidades |
| `create_purchase()` | `purchases/service.py:26-104` | Lógica atômica de ENTRY + conversão |
| `create_movement()` | `inventory/service.py:134-243` | Criação de movimentação com lock e batch |
| `OCRSessionStore` | `ocr/state.py:20-100` | Gerenciamento thread-safe de sessões |
| `OCRItem` schema | `ocr/schemas.py:22-43` | Estrutura rica de dados extraídos |
| `OCRDiscount` schema | `ocr/schemas.py:12-19` | Estrutura de desconto com natureza |
| `access_key` UNIQUE | `purchases/models.py:23-24` | Prevenção de duplicidade |
| `commercial_conversion_factor` | `products` table | Fator sugerido por produto |

### 3.2 Mudanças Mínimas Recomendadas

#### 3.2.1 Compra em Aberto — Nova Tabela

```
purchase_drafts
  id (PK)
  source (VARCHAR) — 'manual' ou 'ocr'
  ocr_session_id (VARCHAR, nullable) — referência à sessão OCR, se aplicável
  purchased_at (TIMESTAMP WITH TIME ZONE, nullable)
  access_key (VARCHAR(44), nullable)
  created_at (TIMESTAMP WITH TIME ZONE)
  updated_at (TIMESTAMP WITH TIME ZONE)
  data (JSONB) — itens e dados fiscais em formato flexível

purchase_draft_items
  id (PK)
  draft_id (FK → purchase_drafts.id, CASCADE)
  product_id (FK → products.id, SET NULL)
  description (VARCHAR) — descrição original do OCR
  commercial_unit (VARCHAR, nullable)
  conversion_factor (DECIMAL, nullable)
  commercial_quantity (DECIMAL, nullable)
  commercial_unit_price (DECIMAL, nullable)
  subtotal_printed (DECIMAL, nullable)
  subtotal_calculated (DECIMAL, nullable)
  expiry_date (DATE, nullable)
  discounts (JSONB, nullable) — descontos originais
  matched (BOOLEAN) — se foi associado a produto
  excluded (BOOLEAN) — se foi excluído pelo operador
```

**Alternativa mais simples:** Adicionar `status` em `Purchase` (`'draft'`, `'confirmed'`) e não gerar ENTRY quando `status = 'draft'`. Ao confirmar, gerar ENTRY e mudar para `'confirmed'`.

**Recomendação:** A alternativa mais simples é preferível. Adicionar `status` a `Purchase` evita duplicação de tabela e mantém a rastreabilidade.

#### 3.2.2 Dados Fiscais — Extensão de Purchase

Adicionar campos opcionais a `Purchase`:

```sql
ALTER TABLE purchases ADD COLUMN supplier_name VARCHAR(255);
ALTER TABLE purchases ADD COLUMN supplier_cnpj VARCHAR(20);
ALTER TABLE purchases ADD COLUMN invoice_number VARCHAR(50);
ALTER TABLE purchases ADD COLUMN invoice_series VARCHAR(10);
ALTER TABLE purchases ADD COLUMN protocol_number VARCHAR(50);
ALTER TABLE purchases ADD COLUMN document_discounts JSONB;
ALTER TABLE purchases ADD COLUMN original_document_path VARCHAR(500);
```

#### 3.2.3 Descontos — Extensão de PurchaseItem

Adicionar campos a `PurchaseItem`:

```sql
ALTER TABLE purchase_items ADD COLUMN item_discounts JSONB;
ALTER TABLE purchase_items ADD COLUMN subtotal_printed NUMERIC;
ALTER TABLE purchase_items ADD COLUMN subtotal_calculated NUMERIC;
```

O `JSONB` permite preservar a estrutura de descontos sem definir schema rígido prematuro.

#### 3.2.4 Conversão de Unidades — Sugestão do Produto

Utilizar `commercial_conversion_factor` do produto para sugerir o fator de conversão:

- Quando o operador seleciona um produto no OCRImportModal, o frontend deve verificar se `product.commercial_conversion_factor` existe e sugerir esse valor.
- Quando `commercial_unit` difere de `base_unit` e `conversion_factor` é 1, exibir alerta visual.

---

## 4. Proposta de Experiência Visual

### 4.1 Diferenças entre Mockup e Implementação

| Elemento | Mockup | Implementação | Divergência |
|----------|--------|---------------|-------------|
| Layout geral | Sidebar + main grid | Modal simples com tabela | Alta |
| Abas | Itens, Emissão, Comprovante | Itens, Emissão, Comprovante | ✅ Alinhado |
| Header | NFC-e nº, badges, total | Título genérico | Alta |
| Sidebar financeira | Resumo, progresso, chave | Não existe | Alta |
| Status badge | "PENDENTE DE REVISÃO" | Não existe | Média |
| Tabela de itens | Produto/EAN, Qtd/Un, Valor, Subtotal, Ações | Produto, Unidade, Fator, Qtd, Preço, Vencimento | Média |
| Adicionar item | Formulário expresso com código de barras | Select de produto cadastrado | Média |
| Documento original | Preview de texto na aba Comprovante | Não implementado | Alta |
| Dados do fornecedor | Aba Emissão com campos readonly | Não implementado | Alta |
| Lotes múltiplos | Não no mockup | Implementado no frontend | Além do mockup |
| Compra manual | Não no mockup | Formulário em PurchasesView | Além do mockup |

### 4.2 Organização Sugerida

A proposta mantém a identidade visual do mockup e adapta-a para contemplar ambos os fluxos:

1. **Header unificado:** Mostra se é compra manual ou importada, com badge de status (rascunho/confirmada).
2. **Sidebar com resumo financeiro:** Total dos itens, total do documento (se houver), divergência, chave de acesso.
3. **Abas:**
   - **Itens:** Tabela editável com produto, unidade comercial, fator de conversão, quantidade, preço bruto, desconto, subtotal.
   - **Dados fiscais:** Informações do fornecedor e do documento (readonly, extraídas pelo OCR).
   - **Documento original:** Preview da imagem ou texto extraído.
4. **Ações:** "Salvar rascunho" e "Confirmar compra" (este último gera ENTRY no estoque).
5. **Alerta de conversão:** Quando `commercial_unit ≠ base_unit` e `conversion_factor = 1`, exibir badge de alerta amarelo.

---

## 5. Decisões Pendentes

As seguintes decisões precisam de aprovação do Product Owner antes da implementação:

### D-P1 — Compra em aberto: status ou tabela separada?

**Opção A (recomendada):** Adicionar `status` a `Purchase` (`'draft'`, `'confirmed'`).ENTRY só é gerada na confirmação.

**Opção B:** Criar tabela `purchase_drafts` separada. Ao confirmar, migrar para `Purchase` e gerar ENTRY.

**Impacto:** Opção A é mais simples e reutiliza `create_purchase()`. Opção B separa claramente rascunho de compra confirmada.

### D-P2 — Preservação do documento original

**Opção A (recomendada):** Armazenar caminho do arquivo em `Purchase.original_document_path` e mover o arquivo para diretório permanente na confirmação.

**Opção B:** Armazenar o arquivo como Base64/bytea no banco.

**Opção C:** Manter política atual (excluir após OCR) e aceitar que o documento não estará disponível após confirmação.

**Impacto:** Opção A requer diretório de armazenamento persistente. Opção B aumenta o tamanho do banco. Opção C simplifica mas perde o documento.

### D-P3 — Dados fiscais: quais campos persistir?

O mockup mostra: `supplier_name`, `cnpj`, `address`, `invoice_number`, `invoice_series`, `protocol`, `taxes`, `consumer`.

**Pergunta:** Quais destes campos são necessários para a operação da Casa Afeto? Todos? Alguns?

**Recomendação:** Persistir no mínimo `supplier_name`, `cnpj`, `invoice_number`, `invoice_series`. Os demais podem ser armazenados em `JSONB` para flexibilidade.

### D-P4 — Descontos: como influenciam o custo de estoque?

**Opção A (recomendada):** O `unit_cost` da ENTRY usa o preço líquido (após desconto). O desconto original é preservado em `item_discounts`.

**Opção B:** O `unit_cost` usa o preço bruto. O desconto é registrado separadamente mas não afeta o custo.

**Opção C:** Manter D-18 (operador informa preço líquido manualmente) e não implementar desconto automático.

**Impacto:** Opção A é a mais correta contabilmente. Opção C é a mais simples e já está implementada.

### D-P5 — Desconto geral da nota: como distribuir?

Quando há desconto de nível documento (não vinculado a um item específico):

**Opção A (recomendada):** Não distribuir automaticamente. Registrar o desconto geral em `Purchase` e deixar o operador ajustar os preços unitários manualmente.

**Opção B:** Distribuir proporcionalmente pelo valor de cada item.

**Impacto:** Opção A é mais simples e evita regras de rateio complexas. Opção B automatiza mas introduz arredondamentos e reconciliação.

### D-P6 — Fator de conversão: alerta quando = 1 com unidades diferentes?

**Opção A (recomendada):** Exibir alerta visual (badge amarelo) quando `commercial_unit ≠ base_unit` e `conversion_factor = 1`. Não bloquear.

**Opção B:** Bloquear confirmação e exigir fator diferente de 1 quando unidades são diferentes.

**Impacto:** Opção A alerta sem impedir. Opção B força correção mas pode ser excessiva se o operador realmente usa a mesma unidade.

---

## 6. Plano Recomendado

Etapas ordenadas por dependência e risco:

### Etapa 1 — Fundações do modelo (baixo risco)

1. Adicionar `status` a `Purchase` (`'draft'`, `'confirmed'`).
2. Adicionar campos fiscais opcionais a `Purchase`.
3. Adicionar campos de desconto a `PurchaseItem`.
4. Criar migration.

**Arquivos afetados:** `purchases/models.py`, nova migration.

### Etapa 2 — Compra em aberto no backend (risco médio)

1. Separar `create_purchase()` em duas fases: criar rascunho e confirmar.
2. ENTRY só é gerada na confirmação.
3. Persistir dados fiscais e descontos originais.

**Arquivos afetados:** `purchases/service.py`, `purchases/schemas.py`, `purchases/models.py`.

### Etapa 3 — Persistência do documento (risco baixo)

1. Mover arquivo para diretório permanente na confirmação.
2. Armazenar caminho em `Purchase.original_document_path`.
3. Ajustar D-13 para reter arquivo até confirmação/rejeição explícita.

**Arquivos afetados:** `ocr/service.py`, `ocr/state.py`.

### Etapa 4 — Conversão de unidades no frontend (risco médio)

1. Remover atribuição automática de `conversion_factor = '1'`.
2. Sugerir `commercial_conversion_factor` do produto quando disponível.
3. Adicionar alerta visual quando unidades diferem e fator = 1.
4. Validar que fator é informado quando unidades diferem.

**Arquivos afetados:** `OCRImportModal.vue`, `PurchasesView.vue`.

### Etapa 5 — Descontos (risco alto, depende de D-P4)

1. Se D-P4 = Opção A: aplicar desconto ao `commercial_unit_price` antes de calcular `unit_cost`.
2. Preservar desconto original em `item_discounts`.
3. Exibir desconto na tabela de itens.

**Arquivos afetados:** `ocr/service.py`, `purchases/service.py`, `purchases/models.py`, `OCRImportModal.vue`.

### Etapa 6 — Experiência visual (risco baixo)

1. Adaptar `OCRImportModal.vue` para seguir o layout do mockup.
2. Adicionar sidebar com resumo financeiro.
3. Adicionar aba de dados fiscais.
4. Adicionar preview do documento original.

**Arquivos afetados:** `OCRImportModal.vue`, `PurchasesView.vue`.

### Etapa 7 — Testes e validação

1. Atualizar `test_m6_purchases.py` para cobrir rascunho e confirmação.
2. Adicionar testes de confirmação OCR (`confirm_import`) — atualmente não testados.
3. Adicionar testes de conversão com alerta.
4. Adicionar testes de desconto.

**Arquivos afetados:** `test_m6_purchases.py`, `test_m13_ocr.py`.

---

## 7. Critérios de Aceitação

Condições verificáveis para considerar o módulo coerente e funcional:

### C-01 — Compra em aberto
- [ ] Uma compra pode ser criada sem gerar ENTRY no estoque.
- [ ] Uma compra em aberto é persistida no banco e sobrevivem a restart do backend.
- [ ] A confirmação de uma compra em aberto gera ENTRY e atualiza o estoque.
- [ ] Ambos os fluxos (manual e OCR) usam o mesmo modelo de compra em aberto.

### C-02 — Dados fiscais
- [ ] Os dados fiscais extraídos pelo OCR são persistidos associados à compra.
- [ ] O documento original permanece acessível após confirmação da compra.
- [ ] Os dados originais do OCR são preservados e distinguíveis dos dados corrigidos.

### C-03 — Conversão de unidades
- [ ] O fator de conversão não é assumido como 1 silenciosamente.
- [ ] Quando `commercial_unit ≠ base_unit` e fator = 1, o operador recebe alerta visual.
- [ ] O `commercial_conversion_factor` do produto é sugerido quando disponível.
- [ ] O cálculo de `unit_cost` e `base_quantity` permanece correto conforme PUR-002/PUR-004.

### C-04 — Descontos
- [ ] Os descontos extraídos pelo OCR são preservados e visíveis ao operador.
- [ ] O operador pode corrigir o preço líquido sem perder o valor original do desconto.
- [ ] O `unit_cost` da ENTRY reflete o preço efetivo (conforme decisão D-P4).
- [ ] Desconto por item é diferenciado de desconto geral da nota.

### C-05 — Coerência entre fluxos
- [ ] Compra manual e compra importada usam o mesmo modelo `Purchase`.
- [ ] A lógica de conversão é única em `create_purchase()` — sem duplicação no OCR.
- [ ] As validações PUR-001 a PUR-012 aplicam-se a ambos os fluxos.

### C-06 — Experiência visual
- [ ] A interface segue a identidade visual e organização do mockup.
- [ ] O operador pode distinguir visualmente compra manual de importada.
- [ ] O resumo financeiro exibe totais e divergências claramente.
- [ ] O documento original é visualizável na interface.

### C-07 — Testes
- [ ] Todos os 21 critérios de aceitação do M6 continuam passando.
- [ ] A confirmação OCR (`confirm_import`) é coberta por testes.
- [ ] A criação e confirmação de compra em aberto são cobertas por testes.
- [ ] A conversão de unidades com alerta é coberta por testes.

---

## 8. Observações Adicionais

### 8.1 Testes de Confirmação OCR Ausentes

O arquivo `test_m13_ocr.py` (1380 linhas) cobre upload, polling, retry, discard, parsing e matching, mas **não testa `confirm_import()`** — a função central que valida, constrói `CreatePurchase` e chama `create_purchase()`. Esta é uma lacuna significativa de cobertura.

### 8.2 `commercial_conversion_factor` Inutilizado

O campo `commercial_conversion_factor` foi adicionado à tabela `products` pela migration `f1a2b3c4d5e6` e está presente no tipo frontend (`types.ts:47`), mas nenhum código o utiliza. Foi definido no ADR-004 (`docs/architecture/decisions/ADR-004-commercial-conversion-factor.md`) como fator sugerido por produto, mas a sugestão nunca foi implementada.

### 8.3 Divergência D-18 vs Requisito de Produto

A decisão D-18 ("descontos ignorados no M13") entra em conflito com o requisito de produto que pede modelagem de descontos. Esta contradição precisa ser resolvida pelo Product Owner.

### 8.4 Estado "confirming" em OCRStatus

O schema `OCRStatus` em `ocr/schemas.py:56` define apenas `"pending"`, `"processing"`, `"completed"`, `"failed"`. O estado `"confirming"` é usado em `ocr/state.py:67` mas não está no tipo. Isso funciona porque o `OCRSession` usa type casting (`# type: ignore[assignment]`), mas pode causar confusão.

### 8.5 `purchase_item_id` em InventoryMovement

O serviço `purchases/service.py:96` passa `purchase_item_id` para `create_movement()`, que o armazena no `StockBatch` (`inventory/batch_service.py`). Esta rastreabilidade é correta e deve ser preservada.

### 8.6 Arredondamento de `unit_cost`

`purchases/service.py:69-71` arredonda `unit_cost` para 2 casas decimais com `.quantize(Decimal("0.01"))`. Quando combinado com descontos e conversão de unidades, o arredondamento pode causar divergência entre a soma dos `unit_cost × base_quantity` e o total da compra. Este é um risco concreto que deve ser considerado na Etapa 5.
