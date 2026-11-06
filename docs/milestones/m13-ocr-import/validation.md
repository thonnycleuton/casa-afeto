# M13 — Plano de Validação

**Versão do documento:** 0.1 (Rascunho)
**Status:** Rascunho — pendente de aprovação final
**Marco:** M13 — Importação de Documentos de Compra com Gemini
**Data:** 2026-11-06

---

## 1. Objetivo da validação

Validar que a implementação do M13 satisfaz as regras funcionais aprovadas (D-1 a D-22) e a especificação detalhada em `specification.md` e `specification-v1.3.md`.

Esta validação cobre:

- Upload de documento de compra (JPEG, PNG, WebP) e processamento assíncrono via Gemini.
- Extração fiel ao documento: itens, quantidades, unidades, preços, subtotais, data, total do documento e chave de acesso.
- Sugestão de matching entre itens extraídos e produtos cadastrados (exato, parcial, fuzzy).
- Revisão e confirmação pelo operador: associações, conversões, cadastros rápidos, exclusões.
- Divisão de itens em múltiplos lotes com vencimento durante a revisão.
- Sugestão de fator de conversão a partir do cadastro do produto, com alerta visual quando fator 1 e unidades diferem.
- Confirmação da compra reutilizando o fluxo do M6 (create_purchase).
- Persistência de rascunhos (DRAFT) e confirmação (CONFIRMED).
- Prevenção de duplicidade via chave de acesso (44 dígitos, UNIQUE).
- Três totais: total do documento, total dos itens extraídos, total dos itens lançados.
- Descontos por item e descontos gerais do documento (preservados sem aplicação automática).
- Ciclo de vida do documento: arquivo temporário durante processamento, documento permanente após confirmação.
- Interface de revisão adaptada ao mockup aprovado: abas "ITENS DA NOTA", "DADOS DA EMISSÃO" e "COMPROVANTE DIGITALIZADO".
- Compra manual com sugestão automática do fator de conversão do produto.

---

## 2. Preparação do ambiente

1. Garantir que o banco de dados está populado com os dados de M1–M12.
2. Garantir que as migrations do M13 foram aplicadas:
   - Coluna `access_key` em `purchases` (UNIQUE, nullable).
   - Coluna `item_discounts` (JSONB) em `purchase_items`.
   - Tabela `purchase_document_discounts`.
   - Coluna `document_path` em `purchases` (nullable).
   - Coluna `supplier_name` em `purchases` (nullable).
   - Coluna `cnpj` em `purchases` (nullable).
   - Coluna `invoice_number` em `purchases` (nullable).
   - Coluna `document_discounts` em `purchases` (nullable, removida em favor da tabela dedicada).
3. Configurar a variável de ambiente `GEMINI_API_KEY` com uma chave válida.
4. Configurar a variável de ambiente `GEMINI_MODEL` (padrão: `gemini-2.0-flash`).
5. Verificar que o diretório `uploads/ocr/` existe e é gravável.
6. Verificar que o diretório `uploads/purchases/` existe e é gravável.
7. Ter documentos de compra (notas fiscais) em formato JPEG, PNG ou WebP para testes manuais.

---

## 3. Validação Automatizada

### 3.1 Testes de Backend

Executar após a implementação:

```bash
cd backend && python -m pytest tests/test_m13_ocr.py tests/test_m13_confirmation.py tests/test_m13_confirmation_draft.py tests/test_m13_discounts.py tests/test_m13_access_key.py tests/test_m13_confirm_schemas.py tests/test_m13_status_totals.py tests/test_m13_draft.py -v
```

Cobertura esperada: ~230 testes mapeados aos critérios de aceitação.

### 3.2 Testes de Regressão M6

Garantir que o comportamento de compras do M6 não foi alterado:

```bash
cd backend && python -m pytest tests/test_m6_purchases.py -v
```

Cobertura esperada: 21 testes passando.

### 3.3 Validação do formato da especificação

```bash
python3 scripts/tlc/validate_spec_casa.py docs/milestones/m13-ocr-import/specification.md
```

### 3.4 Type checking do frontend

```bash
cd frontend && npx vue-tsc --noEmit
```

---

## 4. Validação Manual

### Cenário 1: Upload e processamento OCR

**Objetivo:** Verificar o fluxo completo de upload, processamento assíncrono e apresentação dos dados extraídos.

**Passos:**
1. Autenticar no sistema.
2. Acessar a seção de Compras e iniciar uma importação por documento.
3. Enviar uma imagem de nota fiscal (JPEG, PNG ou WebP).
4. Verificar que o sistema retorna imediatamente um ID de sessão.
5. Acompanhar o status via polling: `processing` → `completed`.
6. Verificar que os dados extraídos são apresentados na aba "ITENS DA NOTA".
7. Verificar que a data extraída é sugerida como `purchased_at`.
8. Verificar que o total do documento é exibido quando extraído.

**Resultado esperado:** Documento processado, itens extraídos visíveis para revisão, status `completed`.

---

### Cenário 2: Matching de produtos

**Objetivo:** Verificar que o sistema sugere associações entre itens extraídos e produtos cadastrados.

**Passos:**
1. Cadastrar produtos conhecidos (ex: "Arroz 5kg", "Feijão 1kg").
2. Enviar um documento contendo esses produtos.
3. Após o processamento, verificar que o sistema sugere o matching.
4. Verificar que a sugestão inclui `commercial_conversion_factor` e `base_unit` do produto.
5. Confirmar a associação de um item com o produto sugerido.
6. Verificar que o fator de conversão sugerido é o cadastrado no produto.

**Resultado esperado:** Sugestões de matching apresentadas, fator de conversão sugerido corretamente, associação confirmada pelo operador.

---

### Cenário 3: Cadastro rápido de produto

**Objetivo:** Verificar que o operador pode cadastrar um produto inexistente durante a revisão.

**Passos:**
1. Enviar um documento contendo um produto não cadastrado.
2. Na revisão, identificar o item sem correspondência.
3. Usar o cadastro rápido para criar o produto com nome e unidade base.
4. Verificar que o item é associado ao novo produto.
5. Verificar que o fator de conversão não é forçado para "1" se já havia um valor.

**Resultado esperado:** Produto criado com campos mínimos, item associado, fator preservado.

---

### Cenário 4: Exclusão de itens

**Objetivo:** Verificar que o operador pode excluir itens sem impedir o lançamento dos demais.

**Passos:**
1. Enviar um documento com 5 itens.
2. Na revisão, excluir 2 itens que não devem ser lançados.
3. Verificar que os itens excluídos são marcados visualmente.
4. Verificar que o `extracted_total` inclui os itens excluídos.
5. Verificar que o `launched_total` exclui os itens excluídos.
6. Confirmar a compra.
7. Verificar que apenas 3 itens são lançados no estoque.

**Resultado esperado:** Itens excluídos não lançados, totais diferenciados corretamente.

---

### Cenário 5: Divisão em lotes múltiplos

**Objetivo:** Verificar que o operador pode dividir um item em múltiplos lotes com vencimentos diferentes.

**Passos:**
1. Enviar um documento com um item de quantidade 24 (ex: 2 caixas de 12 unidades).
2. Na revisão, dividir o item em 2 lotes:
   - Lote 1: 12 unidades, vencimento 2026-12-01
   - Lote 2: 12 unidades, vencimento 2027-01-15
3. Verificar que a soma das quantidades dos lotes iguala a quantidade original.
4. Confirmar a compra.
5. Abrir o modal de estoque do produto.
6. Verificar que 2 lotes foram criados com as quantidades e vencimentos corretos.

**Resultado esperado:** Dois lotes criados, quantidades conservadas, vencimentos corretos.

---

### Cenário 6: Divergência de quantidades nos lotes

**Objetivo:** Verificar que a confirmação é rejeitada quando as quantidades dos lotes não conservam a quantidade original.

**Passos:**
1. Enviar um documento com um item de quantidade 24.
2. Na revisão, dividir o item em 2 lotes:
   - Lote 1: 10 unidades
   - Lote 2: 10 unidades (soma = 20, não 24)
3. Tentar confirmar a compra.

**Resultado esperado:** Confirmação rejeitada com erro indicando divergência de quantidades.

---

### Cenário 7: Conversão de unidades — sugestão do produto

**Objetivo:** Verificar que o fator de conversão cadastrado no produto é sugerido ao associar um item.

**Passos:**
1. Cadastrar um produto com `commercial_conversion_factor = 12` (ex: "Biscoito", caixa com 12 unidades).
2. Enviar um documento contendo esse produto.
3. Na revisão, associar o item extraído ao produto cadastrado.
4. Verificar que o campo "Fator" na tabela de itens exibe "12" como sugestão.
5. Verificar que o operador pode ajustar o fator.

**Resultado esperado:** Fator sugerido a partir do cadastro do produto, editável pelo operador.

---

### Cenário 8: Alerta visual — fator 1 com unidades diferentes

**Objetivo:** Verificar que o alerta aparece quando o fator é 1 mas a unidade comercial difere da unidade base.

**Passos:**
1. Cadastrar um produto com `base_unit = UN` e `commercial_conversion_factor = 24`.
2. Enviar um documento onde o item é extraído com `commercial_unit = "caixa"` e `conversion_factor = 1`.
3. Na revisão, verificar que o ícone de alerta (⚠) aparece na coluna "Fator".
4. Verificar que o alerta é informativo e não bloqueia a confirmação.
5. Confirmar a compra com fator 1.

**Resultado esperado:** Alerta visual exibido, compra confirmada com fator 1, ENTRY criada com `quantity = 1` (1 unidade-base).

---

### Cenário 9: Compra manual com sugestão de fator

**Objetivo:** Verificar que o formulário manual de compra sugere o fator de conversão do produto.

**Passos:**
1. Acessar a seção de Compras e iniciar uma compra manual.
2. Selecionar um produto com `commercial_conversion_factor = 12`.
3. Verificar que o campo "Fator" é preenchido automaticamente com "12".
4. Verificar que o operador pode ajustar o fator.
5. Verificar que o alerta visual aparece se o fator for alterado para "1" e a unidade comercial for diferente da unidade base.

**Resultado esperado:** Fator sugerido automaticamente, editável, alerta quando aplicável.

---

### Cenário 10: Confirmação da compra

**Objetivo:** Verificar que a confirmação cria a compra, os itens e as movimentações de estoque corretamente.

**Passos:**
1. Completar a revisão de uma importação OCR com 3 itens.
2. Preencher a chave de acesso (44 dígitos).
3. Confirmar a compra.
4. Verificar que a compra é registrada com status CONFIRMED.
5. Verificar que os itens são criados com os dados confirmados.
6. Verificar que as ENTRY são geradas no estoque.
7. Verificar que os lotes são criados com `purchase_id` e `purchase_item_id`.
8. Verificar que o custo unitário é calculado corretamente: `unit_cost = commercial_unit_price / conversion_factor`.

**Resultado esperado:** Compra confirmada, itens registrados, ENTRY e lotes criados, custo unitário correto.

---

### Cenário 11: Prevenção de duplicidade via chave de acesso

**Objetivo:** Verificar que a importação duplicada do mesmo documento é bloqueada.

**Passos:**
1. Importar um documento com chave de acesso "123...456" (44 dígitos).
2. Confirmar a compra.
3. Enviar o mesmo documento novamente.
4. Tentar confirmar a segunda importação com a mesma chave de acesso.

**Resultado esperado:** Segunda confirmação rejeitada com erro de duplicidade (HTTP 409).

---

### Cenário 12: Chave de acesso inválida

**Objetivo:** Verificar que a confirmação exige uma chave de acesso válida (44 dígitos).

**Passos:**
1. Importar um documento.
2. Na revisão, alterar a chave de acesso para um valor com 40 dígitos.
3. Tentar confirmar a compra.

**Resultado esperado:** Confirmação rejeitada com erro indicando chave de acesso inválida.

---

### Cenário 13: Rascunho (DRAFT) e edição

**Objetivo:** Verificar que a compra pode ser salva como rascunho e editada posteriormente.

**Passos:**
1. Importar um documento e revisar os itens.
2. Salvar como rascunho (DRAFT).
3. Verificar que a compra é persistida no banco de dados.
4. Verificar que nenhuma ENTRY é gerada no estoque.
5. Retomar o rascunho e editar um item (alterar quantidade).
6. Confirmar o rascunho.
7. Verificar que a compra é confirmada com os dados editados.

**Resultado esperado:** Rascunho salvo sem ENTRY, editável, confirmação gera ENTRY corretamente.

---

### Cenário 14: Edição de compra confirmada

**Objetivo:** Verificar que a edição de compra confirmada é restrita.

**Passos:**
1. Confirmar uma compra com 3 itens.
2. Tentar editar a compra confirmada:
   - Permitir: alterar dados fiscais (fornecedor, CNPJ, número do documento).
   - Bloquear: adicionar itens.
   - Bloquear: remover itens.
   - Bloquear: alterar quantidades.
   - Bloquear: alterar preços.

**Resultado esperado:** Dados fiscais editáveis, itens e quantidades bloqueados (HTTP 409).

---

### Cenário 15: Descontos por item e gerais

**Objetivo:** Verificar que os descontos são preservados sem alterar o custo dos produtos.

**Passos:**
1. Enviar um documento com descontos identificados pelo OCR.
2. Na revisão, verificar que os descontos por item são exibidos.
3. Verificar que os descontos gerais do documento são exibidos.
4. Confirmar a compra.
5. Verificar que os descontos são persistidos.
6. Verificar que o `unit_cost` dos lotes não é afetado pelos descontos.

**Resultado esperado:** Descontos preservados como informação, custo unitário não alterado.

---

### Cenário 16: Ciclo de vida do documento

**Objetivo:** Verificar o ciclo de vida do arquivo temporário e do documento permanente.

**Passos:**
1. Enviar um documento para OCR.
2. Verificar que o arquivo é salvo em `uploads/ocr/` como temporário.
3. Confirmar a compra.
4. Verificar que o arquivo é copiado para `uploads/purchases/` como permanente.
5. Verificar que o arquivo temporário é excluído após a confirmação.
6. Verificar que o documento permanente permanece acessível pelo detalhamento da compra.

**Resultado esperado:** Arquivo temporário excluído após confirmação, documento permanente preservado.

---

### Cenário 17: Falha no processamento OCR

**Objetivo:** Verificar o comportamento quando o processamento do Gemini falha.

**Passos:**
1. Simular uma falha no processamento OCR (ex: enviar um documento ilegível).
2. Verificar que o status da sessão é `failed`.
3. Verificar que o operador é notificado da falha.
4. Verificar que o arquivo temporário é preservado para retentativa.
5. Tentar novamente o processamento.

**Resultado esperado:** Falha notificada, arquivo preservado, retentativa possível.

---

### Cenário 18: Aba "DADOS DA EMISSÃO"

**Objetivo:** Verificar que a aba exibe os dados fiscais extraídos.

**Passos:**
1. Importar um documento com dados fiscais legíveis.
2. Na revisão, acessar a aba "DADOS DA EMISSÃO".
3. Verificar que a data de compra é exibida.
4. Verificar que a chave de acesso é exibida.
5. Verificar que o total do documento é exibido.
6. Verificar que campos ausentes são exibidos como "—".

**Resultado esperado:** Dados fiscais exibidos, campos ausentes tratados graciosamente.

---

### Cenário 19: Aba "COMPROVANTE DIGITALIZADO"

**Objetivo:** Verificar que a aba exibe o documento original.

**Passos:**
1. Importar um documento.
2. Na revisão, acessar a aba "COMPROVANTE DIGITALIZADO".
3. Verificar que a imagem do documento original é exibida.
4. Verificar que o endpoint `GET /ocr/{session_id}/preview` retorna a imagem.

**Resultado esperado:** Documento original visível para conferência do operador.

---

### Cenário 20: Coluna editável de fator de conversão

**Objetivo:** Verificar que o operador pode editar o fator de conversão diretamente na tabela.

**Passos:**
1. Importar um documento com um item.
2. Na revisão, na aba "ITENS DA NOTA", localizar a coluna "Fator".
3. Alterar o fator de "12" para "24".
4. Verificar que o subtotal é recalculado.
5. Verificar que o `launched_total` é atualizado.

**Resultado esperado:** Fator editável na tabela, totais recalculados em tempo real.

---

### Cenário 21: Conferência financeira — divergência

**Objetivo:** Verificar que a divergência entre o total do documento e o total extraído é alertada sem bloquear.

**Passos:**
1. Enviar um documento onde o total impresso difere da soma dos subtotais dos itens.
2. Na revisão, verificar que o sistema exibe os três totais:
   - Total do documento
   - Total dos itens extraídos
   - Total dos itens lançados
3. Verificar que um alerta de divergência é exibido.
4. Verificar que a confirmação não é bloqueada.

**Resultado esperado:** Divergência alertada, confirmação permitida.

---

### Cenário 22: Autenticação JWT nos endpoints OCR

**Objetivo:** Verificar que os endpoints OCR exigem autenticação.

**Passos:**
1. Tentar acessar `POST /ocr/upload` sem token JWT.
2. Tentar acessar `GET /ocr/{session_id}/status` sem token JWT.
3. Tentar acessar `POST /ocr/{session_id}/confirm` sem token JWT.

**Resultado esperado:** HTTP 401 em todas as requisições não autenticadas.

---

### Cenário 23: Formatos aceitos

**Objetivo:** Verificar que apenas JPEG, PNG e WebP são aceitos.

**Passos:**
1. Tentar enviar um arquivo PDF.
2. Tentar enviar um arquivo JPEG.
3. Tentar enviar um arquivo PNG.

**Resultado esperado:** PDF rejeitado, JPEG e PNG aceitos.

---

## 5. Checklist de Validação Técnica

| Item | Status |
|------|--------|
| ### Backend | |
| Endpoint `POST /ocr/upload` — upload de documento | ☐ |
| Endpoint `GET /ocr/{session_id}/status` — polling de status | ☐ |
| Endpoint `GET /ocr/{session_id}/match` — sugestões de matching | ☐ |
| Endpoint `POST /ocr/{session_id}/confirm` — confirmação da importação | ☐ |
| Endpoint `GET /ocr/{session_id}/preview` — preview do documento | ☐ |
| Endpoint `DELETE /ocr/{session_id}` — descarte de sessão | ☐ |
| Endpoint `POST /ocr/{session_id}/retry` — retentativa de processamento | ☐ |
| Endpoint `POST /ocr/{session_id}/quick-product` — cadastro rápido | ☐ |
| Processamento assíncrono com `asyncio.create_task()` | ☐ |
| OCR executado em thread separada (`asyncio.to_thread()`) | ☐ |
| Estado em memória (D-12) — sem persistência pré-confirmação | ☐ |
| `MatchSuggestion.to_dict()` inclui `commercial_conversion_factor` e `base_unit` | ☐ |
| Confirmação preserva o `conversion_factor` informado pelo operador | ☐ |
| Fator 1 com unidades diferentes aceito pelo backend | ☐ |
| Validação de `access_key` — 44 dígitos numéricos | ☐ |
| Constraint UNIQUE em `access_key` no banco de dados | ☐ |
| Tratamento de `IntegrityError` por nome da constraint | ☐ |
| Falhas antes do commit — rollback e restauração para `completed` | ☐ |
| Falhas depois do commit — nunca restaurar para `completed` | ☐ |
| Validação de cobertura total — todos os itens representados | ☐ |
| Sem sobreposição entre `confirmed_items` e `excluded_item_ids` | ☐ |
| Cálculo de `commercial_unit_price` nos lotes: `item.price × (lot.factor / item.factor)` | ☐ |
| Conservação de quantidades em unidade-base para lotes múltiplos | ☐ |
| Descontos por item persistidos em `item_discounts` (JSONB) | ☐ |
| Descontos gerais persistidos em `purchase_document_discounts` | ☐ |
| Descontos não alteram `unit_cost` dos lotes | ☐ |
| Arquivo temporário em `uploads/ocr/` | ☐ |
| Documento permanente em `uploads/purchases/` após confirmação | ☐ |
| Arquivo temporário excluído após confirmação bem-sucedida | ☐ |
| Arquivo preservado em caso de falha na confirmação | ☐ |
| ### Frontend | |
| `matchProduct()` não sobrescreve `conversion_factor` para "1" | ☐ |
| `matchProduct()` sugere `commercial_conversion_factor` do produto | ☐ |
| `submitQuickProduct()` preserva `conversion_factor` existente | ☐ |
| Coluna "Un." editável na tabela de itens | ☐ |
| Coluna "Fator" editável na tabela de itens | ☐ |
| Alerta visual (⚠) quando fator 1 e unidades diferem | ☐ |
| Aba "ITENS DA NOTA" funcional | ☐ |
| Aba "DADOS DA EMISSÃO" funcional | ☐ |
| Aba "COMPROVANTE DIGITALIZADO" funcional | ☐ |
| Preview do documento via endpoint `/preview` | ☐ |
| Campos ausentes exibidos como "—" nas abas | ☐ |
| `PurchasesView.vue` sugere fator do produto ao selecionar | ☐ |
| `PurchasesView.vue` exibe alerta de conversão | ☐ |
| Totais diferenciados: documento, extraídos, lançados | ☐ |
| Status DRAFT e CONFIRMED exibidos corretamente | ☐ |
| `vue-tsc --noEmit` sem erros | ☐ |
| ### Testes | |
| Testes M13 passam (~230 testes) | ☐ |
| Testes M6 passam (21 testes, sem regressão) | ☐ |
| `validate_spec_casa.py` passa | ☐ |

---

## 6. Critérios de Conclusão

O M13 é considerado validado quando:

- [ ] Todos os cenários de validação manual são concluídos sem falhas.
- [ ] Todos os testes automatizados de backend passam.
- [ ] Os testes de regressão M6 passam sem falhas.
- [ ] `vue-tsc --noEmit` executa sem erros.
- [ ] `validate_spec_casa.py` valida a especificação sem erros.
- [ ] O checklist de validação técnica está 100% marcado.
- [ ] Nenhuma regra de negócio preservada (INV-*, PUR-*, LOT-*, EXP-*) foi violada.
- [ ] O Product Owner aprova o comportamento da importação OCR e da interface de revisão.
- [ ] A documentação está atualizada (roadmap, phase sequence, business-contract se aplicável).

---

## 7. Notas

- Este plano de validação cobre tanto a importação OCR quanto a adaptação da interface de compras manual.
- A branch `ocr-gemini` não é referência para este plano.
- O M13 reutiliza o serviço `create_purchase()` do M6 — a validação de regras PUR, INV, LOT e EXP é feita pelos testes existentes do M6, M7 e M8.
- O discrimination sensor deve ser executado nos módulos críticos (matching, confirmação, descontos) para verificar a qualidade dos testes.
- A validação com documentos reais da Casa Afeto deve ser realizada antes da implantação em produção (D-21).

---

*Fim do plano de validação do M13.*
