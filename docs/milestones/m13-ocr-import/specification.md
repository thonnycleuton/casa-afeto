# M13 — Especificação de Importação de Documentos de Compra com Gemini

**Versão do documento:** 1.5
**Status:** Rascunho — revisado, pendente de aprovação do Product Owner
**Marco:** M13 — Importação de Documentos de Compra com Gemini
**Data:** 2026-11-03

---

## 1. Objetivo e Problema

### 1.1 Problema

Atualmente, o operador registra compras manualmente: para cada item de uma nota fiscal, informa individualmente o produto, a unidade comercial, o fator de conversão, a quantidade e o preço. Quando o documento contém muitos itens, o processo é lento, propenso a erros de digitação e consome tempo que poderia ser dedicado a outras atividades.

### 1.2 Benefício esperado

A importação por documento permite que o operador envie uma foto ou digitalização do documento de compra e o sistema extraia automaticamente os itens, quantidades e preços. O operador revisa e confirma os dados extraídos antes do lançamento, reduzindo o tempo de registro e minimizando erros de digitação.

### 1.3 Dependência funcional

O M13 depende do fluxo de compras existente implementado no M6, dos lotes de estoque implementados no M7 e dos vencimentos implementados no M8. A confirmação da importação utiliza o mesmo serviço de criação de compra (`create_purchase`) e as mesmas regras de estoque, conversão e movimentação já estabelecidas.

---

## 2. Escopo

### 2.1 Dentro do escopo

O M13 inclui:

* Envio de documento de compra para processamento por OCR;
* Extração automática de itens, quantidades e preços pelo Gemini;
* Apresentação dos dados extraídos para revisão pelo operador;
* Sugestão de matching entre itens extraídos e produtos cadastrados;
* Revisão e confirmação das associações e conversões pelo operador;
* Cadastro rápido de produto durante a revisão (campos mínimos);
* Exclusão de itens não destinados ao estoque;
* Diferenciação entre o total informado no documento, o total dos itens extraídos (base da conferência financeira) e o total dos itens efetivamente lançados no estoque;
* Confirmação da compra utilizando o fluxo existente do M6;
* Processamento assíncrono com polling para acompanhamento do status;
* Divisão de itens em múltiplos lotes com vencimento durante a revisão.

### 2.2 Explicitamente fora do escopo

O seguinte **não** deve ser implementado como parte do M13:

* Cadastro de fornecedores;
* Notas fiscais eletrônicas ou integração com governo;
* Processamento de documentos de venda;
* Importação automática sem revisão humana;
* Infraestrutura de filas (Redis, Celery);
* Regras de cálculo ou aplicação automática de descontos, frete e impostos, bem como reconciliação ou ajuste financeiro automático;
* Alterações nas regras de estoque existentes.

### 2.3 Pendente de decisão

Os seguintes tópicos podem fazer parte do M13, mas sua inclusão depende de decisões ainda pendentes:

Nenhum tópico pendente. Todas as decisões necessárias para o M13 foram aprovadas (D-1 a D-22).

---

## 3. Dependências

O M13 depende de:

* `docs/milestones/m13-ocr-import/decisions.md` — decisões aprovadas D-1 a D-22;
* `docs/domain/business-contract.md` — regras de negócio;
* `docs/milestones/m6-purchases/specification.md` — fluxo de compras e regras PUR-001 a PUR-012;
* `docs/milestones/m7-stock-batches/specification.md` — lotes de estoque e regras LOT-001 a LOT-010;
* `docs/milestones/m8-expiry/specification.md` — vencimentos em itens de compra;
* `docs/architecture/decisions/ADR-001-inventory-concurrency.md` — concorrência de estoque;
* `docs/architecture/decisions/ADR-002-m5-architecture.md` — decisões técnicas do M5;
* `docs/architecture/technical-foundation.md` — fundamentos técnicos.

O M13 depende da implementação do M6 (compras), M7 (lotes de estoque) e M8 (vencimentos).

---

## 4. Fluxo Funcional Proposto

O fluxo de importação segue estas etapas funcionais:

```
1. Operador inicia uma importação
       ↓
2. Documento é enviado para processamento
       ↓
3. Sistema processa o documento assincronamente (D-1)
       ↓
4. Operador acompanha o status do processamento via polling (D-1)
       ↓
5. Dados extraídos são apresentados para revisão (D-3)
       ↓
6. Itens são associados a produtos por sugestões de matching (D-4)
       ↓
7. Operador revisa associações e conversões propostas (D-4)
       ↓
8. Operador pode cadastrar rapidamente produto inexistente (D-5)
       ↓
9. Operador pode excluir itens não destinados ao estoque (D-7)
       ↓
9b. Operador pode dividir itens em múltiplos lotes com vencimento próprio (D-11)
       ↓
10. Sistema apresenta três totais:
    - Total informado no documento pelo fornecedor (quando disponível)
    - Total dos itens extraídos: soma dos valores dos itens identificados pelo OCR (quando disponíveis)
    - Total dos itens efetivamente lançados no estoque (D-7)
        ↓
11. Operador confirma que todas as mercadorias incluídas no lançamento foram recebidas fisicamente (PUR-001). Essa confirmação é obrigatória para prosseguir.
        ↓
12. Operador confirma a operação
        ↓
13. A compra é registrada pelo fluxo existente do M6:
    - Criação de Purchase + PurchaseItem
    - Geração de ENTRY com lote (batch), mantendo a invariante de saldo físico (INV-001, LOT-008)
    - Vencimento registrado quando há informação confirmada e aplicável (EXP-001)
    - As validações e operações executadas por `create_purchase()` são listadas em §7.1; outras regras PUR, INV, LOT e EXP são preservadas pelo sistema — ver §10.2
```

### 4.1 Separação de responsabilidades

O fluxo distingue claramente quatro fases com responsabilidades diferentes:

| Fase | Responsável | Decisão de referência |
|---|---|---|
| **Extração** | Gemini (automático) | D-3 |
| **Sugestão de matching** | Sistema (automático) | D-4 |
| **Revisão e decisão** | Operador humano | D-4, D-5, D-7 |
| **Confirmação e lançamento** | Sistema (reutiliza M6) | D-2 |

Nenhuma fase substitui a responsabilidade da fase seguinte. A extração não decide o matching. O matching não substitui a revisão. A revisão não é automática.

---

## 5. Regras Funcionais Aprovadas

As regras funcionais do M13 derivam diretamente das decisões aprovadas registradas em `docs/milestones/m13-ocr-import/decisions.md`.

### 5.1 Processamento assíncrono (D-1)

O processamento do documento é assíncrono. Após o envio, o sistema retorna imediatamente um identificador para acompanhamento do status. O operador ou a interface acompanham o progresso por polling simples até a conclusão ou falha do processamento.

A implementação utiliza `asyncio.create_task()` (ou mecanismo equivalente) para agendar a execução do processamento em segundo plano, sem aguardá-la. O trabalho de OCR em si é executado em thread separada via `asyncio.to_thread()`, de modo que o loop de eventos principal não seja bloqueado pela chamada síncrona à API do Gemini. Não é usada infraestrutura de filas (Redis, Celery).

**Estado em memória (D-12):** Os resultados extraídos permanecem temporariamente em memória no backend. Se o estado não estiver mais disponível no servidor — por reinicialização do backend —, os dados extraídos são perdidos e será necessário reenviar o documento e realizar novo processamento. Fechar o navegador, isoladamente, não provoca perda enquanto o estado permanecer disponível no servidor.

**Retenção dos documentos (D-13, D-22):** O arquivo do documento permanece disponível no servidor enquanto uma tentativa de processamento estiver em andamento. Após o processamento concluído — com sucesso ou falha —, o arquivo é excluído. Não confundir processamento concluído com confirmação ou rejeição da compra. Se o arquivo já tiver sido excluído, uma nova tentativa exige que o operador envie novamente o documento. O operador pode tentar novamente ou enviar outro documento, sem repetição automática.

### 5.2 Aderência à arquitetura existente (D-2)

A funcionalidade segue os padrões e a arquitetura do Casa Afeto. O fluxo de lançamento reutiliza o serviço de compras existente e não duplica a lógica de criação de compra, geração de ENTRY ou atualização de estoque.

D-2 determina aderência aos padrões do Casa Afeto, mas não estabelece proibição absoluta de adaptações no serviço existente. Qualquer necessidade de adaptação será identificada e justificada antes de ser proposta — ver §7.2.

### 5.3 Extração fiel ao documento (D-3)

O Gemini extrai os dados presentes no documento. Se uma informação é ausente ou ilegível, ela é preservada como ausente — não é inventada, completada por suposição ou inferida de outros itens.

Os dados ausentes são sinalizados ao operador durante a revisão para que ele possa preenchê-los manualmente.

### 5.4 Matching sujeito à confirmação humana (D-4)

O sistema sugere associações entre itens extraídos e produtos cadastrados com base em três critérios de matching (D-19): correspondência exata de nome normalizado como critério primário, correspondência parcial (substring) como critério secundário, e fuzzy matching como critério terciário. As sugestões são apresentadas ao operador, que revisa e confirma cada associação antes do lançamento.

As conversões propostas (unidade comercial, fator de conversão) também são apresentadas como sugestões e requerem confirmação explícita do operador.

### 5.5 Cadastro rápido de produto (D-5)

Durante a revisão, se um item extraído não corresponde a nenhum produto cadastrado, o operador pode cadastrar rapidamente um novo produto.

O cadastro rápido respeitará as validações existentes no sistema — as mesmas aplicadas ao cadastro normal de produtos. O produto criado permanece pendente de complementação cadastral — ou seja, campos opcionais podem ser preenchidos posteriormente pelo operador.

Os campos mínimos obrigatórios para o cadastro rápido são: nome do produto (obrigatório) e unidade base (obrigatório). O preço de referência é opcional no cadastro rápido (D-20).

### 5.6 Exclusão de itens (D-7)

O operador pode excluir explicitamente itens extraídos que não devem ser lançados no estoque — por exemplo, itens que não são produtos da Casa Afeto, itens de serviço, ou itens que o operador decidiu não registrar.

A exclusão de um item não impede o lançamento dos demais itens válidos. A interface diferencia claramente:

* **Total do documento:** valor total informado no documento pelo fornecedor, quando disponível. Não se assume que corresponde à soma dos itens extraídos;
* **Total dos itens extraídos (`extracted_total`):** soma dos subtotais de todos os itens identificados pelo OCR, incluindo os itens excluídos pelo operador. Este é a base da conferência financeira (D-17). Itens sem subtotal (preço ou quantidade ausente) não contribuem para este total;
* **Total dos itens lançados (`launched_total`):** soma apenas dos subtotais dos itens efetivamente confirmados para estoque.

O backend retorna explicitamente três valores na resposta de status da importação:

- `extracted_total`: soma dos subtotais de todos os itens originais extraídos (inclusive excluídos);
- `launched_total`: soma dos subtotais apenas dos itens confirmados para lançamento;
- `items_without_subtotal_count`: quantidade de itens originais que não possuem subtotal (preço ou quantidade ausente ou ilegível).

O `extracted_total` considera todos os itens originais, inclusive os excluídos, pois serve como base para a conferência financeira contra o total informado no documento.

### 5.7 Conferência de vencimentos e lotes múltiplos (D-11)

As notas fiscais dos fornecedores não apresentam vencimentos por item ou lote. Portanto, o Gemini não deve inferir nem extrair vencimentos inexistentes no documento.

A conferência de vencimentos é realizada fisicamente pelo operador nas mercadorias recebidas. Durante a revisão da compra, o operador pode dividir a quantidade de um item em múltiplos lotes, onde cada lote tem quantidade e vencimento próprios.

Quando um item extraído for dividido em múltiplos lotes, a conservação das quantidades deve ser verificada em unidade-base, após aplicação dos fatores de conversão confirmados:

- As quantidades atribuídas aos lotes podem utilizar unidades comerciais diferentes, desde que sejam válidas e confirmadas.
- Cada quantidade deve ser convertida para a unidade-base do produto usando seu fator de conversão confirmado.
- A soma das quantidades convertidas deve corresponder exatamente à quantidade total confirmada do item original, também expressa em unidade-base.
- Divergências para mais ou para menos impedem a confirmação.
- A validação ocorre antes da chamada a `create_purchase()`.

Quando o vencimento não puder ser identificado, o operador pode criar lote com vencimento desconhecido (`expiry_date = NULL`), conforme as regras existentes (EXP-001).

As regras de lotes e FEFO estabelecidas no M6/M8 são preservadas integralmente.

---

## 6. Dados Extraídos

### 6.1 Categorias de informação

O documento de compra pode conter as seguintes categorias de informação. A tabela distingue o que é relevante para o registro de compra do que ainda depende de decisão sobre extração:

| Categoria | Descrição | Relevante para compra? | O Gemini deve tentar extrair? | Obrigatório para criar compra? | Ausente: preenchimento manual? |
|---|---|---|---|---|---|
| **Descrição do item** | Nome ou descrição do produto no documento | Sim | Sim | Não — usada para matching | Sim — o operador corrige ou associa manualmente |
| **Quantidade** | Quantidade do item no documento | Sim | Sim | Sim — campo obrigatório do contrato | Sim — o operador informa se o OCR falhar |
| **Unidade** | Unidade de medida do item (se presente) | Sim | Sim — extraído quando presente no documento | Sim — campo obrigatório do contrato | Sim — o operador informa se ausente; não é inferido |
| **Preço unitário** | Preço por unidade do item | Sim | Sim | Sim — campo obrigatório do contrato | Sim — o operador informa se o OCR falhar |
| **Subtotal do item** | Valor total do item (quantidade × preço) | Sim | Sim — extraído quando presente no documento | Não — derivado de quantidade × preço | Não aplicável |
| **Data do documento** | Data da compra ou emissão do documento | Sim — usada como sugestão para purchased_at (D-9) | Sim — extraída quando legível | Não | Sim — o operador preenche se ausente (D-9) |
| **Total do documento** | Valor total da compra informado pelo fornecedor | Sim — usado para conferência de divergências (D-17) | Sim — extraído quando legível | Não | — |
| **Vencimento** | Data de vencimento do produto | Não — as notas não apresentam vencimento por item | Não | Não — campo opcional | Sim — o operador confere fisicamente e informa por lote |

**Distinção importante:** A obrigatoriedade de um campo para o contrato de criação de compras (`CreatePurchase`) não implica automaticamente que o Gemini deve extraí-lo. O Gemini tenta extrair os campos listados como "Sim" na coluna "O Gemini deve tentar extrair?". Quando a extração falhar ou o campo for pendente de decisão, o operador preenche ou confirma o valor manualmente durante a revisão — os campos obrigatórios do contrato são validados no momento da confirmação, não no momento da extração.

O subtotal do item possui duas formas: o subtotal impresso no documento (extraído quando legível) e o subtotal calculado (derivado de quantidade × preço unitário quando ambos estão disponíveis). Se houver divergência entre o subtotal impresso e o subtotal calculado, a diferença é apresentada ao operador para conferência, sem correção ou ajuste automático.

### 6.2 Campos e regras de extração definidos

Os seguintes campos e suas regras de extração foram definidos pelas decisões aprovadas (D-16 a D-18):

* **Unidade comercial e fator de conversão:** extraídos quando presentes no documento; quando ausentes, não são inferidos — o operador preenche manualmente.
* **Descontos:** O Gemini identifica e apresenta descontos quando presentes e legíveis no documento. Nenhum desconto é aplicado ou rateado automaticamente — o operador informa manualmente o preço líquido. A distribuição proporcional de descontos é melhoria futura, fora do escopo (D-18).
* **Subtotais:** O Gemini extrai o subtotal impresso no documento quando legível. Quando o subtotal impresso não está disponível, o subtotal é calculado a partir de quantidade e preço unitário quando ambos estão presentes. Se houver divergência entre o subtotal impresso e o subtotal calculado, a diferença é apresentada ao operador para conferência, sem correção ou ajuste automático.
* **Data do documento:** extraída quando legível, usada como sugestão para `purchased_at` (D-9).
* **Total do documento:** extraído quando legível, usado para conferência de divergências (D-17).

Estes itens foram resolvidos e registrados como D-16 a D-18.

### 6.3 Estrutura dos dados extraídos

Os campos e regras de extração foram definidos pelas decisões aprovadas (D-16 a D-18) e estão documentados em §6.1 e §6.2. Eventuais refinamentos técnicos do schema — como tratamento de casos extremos de formatação ou normalização de valores — podem ocorrer durante a implementação, sem reabrir as decisões aprovadas.

---

## 7. Integração com Compras e Estoque

### 7.1 Reutilização do fluxo existente

A confirmação da importação reutiliza o fluxo de compras existente do M6. Especificamente:

* A função `create_purchase()` em `purchases/service.py` é chamada com os dados confirmados pelo operador;
* Os contratos e regras de negócio do serviço existente são preservados;
* As validações executadas durante a criação da compra incluem: produto ativo (PUR-006/INV-008), preço não negativo (PUR-003), fator de conversão positivo (PUR-002), quantidade válida em unidade-base (PUR-005), cálculo do unit_cost (PUR-004), atomicidade transacional (PUR-011) e concorrência via SELECT FOR UPDATE com ordem por `product_id` (PUR-012);
* A chave de acesso da nota fiscal (`access_key`) será persistida no modelo definitivo `Purchase` com restrição de unicidade no banco de dados, para prevenir a importação duplicada do mesmo documento (D-8). A ausência de chave de acesso impede a confirmação da compra importada, pois as notas fiscais abrangidas pelo escopo atual possuem obrigatoriamente chave de acesso. Se futuramente forem aceitos documentos sem chave de acesso, essa obrigatoriedade será reavaliada — ver `future-improvements.md`. A restrição de unicidade é garantida pela constraint UNIQUE no banco de dados; a consulta antes do commit (`SELECT ... WHERE access_key = :key`) detecta duplicidade apenas quando a chave já existe — não bloqueia uma chave ainda inexistente em confirmações concorrentes.
* Validação da `access_key`: a chave deve conter exatamente 44 dígitos numéricos. O operador pode editar o valor extraído pelo OCR durante a revisão. A confirmação da compra exige que a `access_key` esteja preenchida e válida (44 dígitos).
* Tratamento de `IntegrityError`: ao detectar uma violação de constraint UNIQUE, o endpoint deve identificar a constraint específica por seu nome ou identificador (não por substring na mensagem de erro) e retornar a resposta adequada ao operador. Para erros inesperados que não sejam violação de constraint, o endpoint retorna HTTP 500 com mensagem genérica e registra os detalhes apenas no log.
* Separação de falhas antes e depois do commit: antes do commit, qualquer falha durante a confirmação aciona rollback e restaura o estado da importação para `completed` (ou equivalente), permitindo nova tentativa de confirmação. Depois de um commit bem-sucedido, nunca restaurar o estado para `completed`, mesmo que a limpeza subsequente da sessão falhe — a compra já foi registrada e restaurar `completed` permitiria confirmação duplicada. O estado terminal (ou mecanismo equivalente) deve impedir confirmação duplicada após commit.
* As regras de criação de lote (LOT-001, LOT-006) e de vencimento herdado (EXP-002) são executadas automaticamente por `create_purchase()`;
* Outras regras PUR, INV, LOT e EXP são preservadas pelo sistema, mas não são acionadas diretamente durante a criação da compra — ver §10.2.

### 7.2 Adaptações potenciais

D-2 determina aderência à arquitetura existente, mas não proíbe adaptações justificadas. A implementação deverá primeiro investigar se a integração pela camada de chamada — estruturar os dados no formato `CreatePurchase` e invocar `create_purchase()` — é suficiente para atender a todos os requisitos da importação.

Se uma adaptação no serviço existente for realmente necessária, ela deverá apresentar justificativa técnica e impacto sobre os contratos existentes para avaliação e aprovação antes de ser implementada. A adaptação não é uma decisão funcional pendente — é uma questão técnica a ser resolvida durante a implementação, com base na análise concreta dos requisitos.

### 7.3 Mapeamento para CreatePurchase

Os dados confirmados pelo operador são estruturados no formato `CreatePurchase` esperado pelo serviço de compras existente:

| Campo do CreatePurchase | Origem |
|---|---|
| `product_id` | Produto matched ou produto criado pelo cadastro rápido |
| `commercial_unit` | Unidade confirmada pelo operador |
| `conversion_factor` | Fator de conversão confirmado pelo operador |
| `commercial_quantity` | Quantidade confirmada pelo operador |
| `commercial_unit_price` | Preço unitário confirmado pelo operador |
| `expiry_date` | Vencimento confirmado pelo operador (se aplicável) |

**Nota sobre lotes múltiplos (D-11):** Um item extraído pode gerar múltiplos `CreatePurchaseItem` quando o operador divide sua quantidade em lotes distintos durante a revisão. Cada `CreatePurchaseItem` resultante terá o mesmo `product_id`, mas `commercial_quantity`, `commercial_unit`, `conversion_factor` e `expiry_date` independentes. A conservação das quantidades é verificada em unidade-base: cada `commercial_quantity` é convertida para unidade-base usando seu `conversion_factor` confirmado, e a soma das quantidades em unidade-base deve corresponder exatamente à quantidade total confirmada do item original, também expressa em unidade-base — divergência impede a confirmação. O contrato existente de `create_purchase()` já suporta múltiplos itens para o mesmo produto, processando-os em ordem crescente de `product_id` e gerando um lote (StockBatch) independente para cada item.

**Dados da compra:** Além dos campos de `CreatePurchaseItem`, a compra confirmada inclui:

* `purchased_at`: data sugerida a partir do documento e revisada pelo operador, conforme D-9.
* `access_key`: chave extraída durante o processamento e persistida junto à compra confirmada, conforme D-8. A chave pertence à compra, não aos itens individuais.

**Nota sobre chave de acesso (D-8):** A chave de acesso extraída pelo OCR é mantida temporariamente durante o processamento assíncrono e somente persistida junto à compra confirmada, no momento do commit da transação. A consulta prévia identifica chaves já registradas. A constraint `UNIQUE` no banco de dados é a proteção definitiva contra duplicidade em confirmações concorrentes. A implementação deve tratar uma violação dessa constraint sem permitir o registro duplicado da compra. Não afirmar que um `SELECT` sobre uma chave inexistente bloqueia outra transação de inserir a mesma chave.

**ConfirmImportRequest:** O endpoint de confirmação recebe um `ConfirmImportRequest` contendo:

- `confirmed_items`: lista dos itens confirmados pelo operador, com `product_id`, `commercial_unit`, `conversion_factor`, `commercial_quantity`, `expiry_date` e os lotes resultantes (quando divididos). Cada item confirmado deve referenciar exatamente um item original extraído.
- `excluded_item_ids`: lista dos IDs dos itens originais excluídos pelo operador.

Validação obrigatória: todos os itens originais extraídos devem estar representados exatamente uma vez entre `confirmed_items` e `excluded_item_ids`. Não é permitido que um item original apareça em ambas as listas (sobreposição) nem que fique fora de ambas (omissão). Duplicidade dentro de uma mesma lista também é rejeitada.

**Cálculo de `commercial_unit_price` nos lotes:** O cliente não determina independentemente o `commercial_unit_price` de cada lote. O backend calcula esse valor pela fórmula `item.price × (lot.factor / item.factor)`, onde `item.price` é o preço unitário do item original extraído, `lot.factor` é o fator de conversão do lote e `item.factor` é o fator de conversão do item original. O preço unitário de cada lote é, portanto, derivado deterministicamente pelo backend a partir do preço do item e dos fatores de conversão.

A integração primária é feita pela camada de chamada — a importação estrutura os dados no formato esperado por `create_purchase()` e invoca a função existente. Alterações no serviço serão consideradas apenas se justificadas durante a implementação.

### 7.4 Itens excluídos não são lançados

Conforme D-7, os itens excluídos pelo operador durante a revisão não são incluídos na chamada a `create_purchase()`. Apenas os itens confirmados são lançados.

Se todos os itens forem excluídos, a compra não é registrada.

---

## 8. Decisões Anteriormente Pendentes — Todas Resolvidas

Todas as decisões pendentes originais (§8.1 a §8.11) foram aprovadas pelo Product Owner e registradas como D-12 a D-22 em `decisions.md`. Não há decisões pendentes para o M13.

### 8.1 Persistência dos resultados do OCR (Resolvido → D-12)

Os resultados extraídos permanecem temporariamente em memória no backend. Se o estado não estiver mais disponível no servidor — por reinicialização do backend —, os dados extraídos são perdidos e será necessário reenviar o documento e realizar novo processamento. Fechar o navegador, isoladamente, não provoca perda enquanto o estado permanecer disponível no servidor.

### 8.2 Política de retenção dos documentos (Resolvido → D-13)

O arquivo do documento permanece disponível no servidor enquanto uma tentativa de processamento estiver em andamento. Após o processamento concluído — com sucesso ou falha —, o arquivo é excluído. Não garantir nova tentativa sem reenvio após uma falha cujo processamento já tenha sido concluído. Se o arquivo já tiver sido excluído, uma nova tentativa exige que o operador envie novamente o documento. Não confundir processamento concluído com confirmação ou rejeição da compra.

### 8.3 Formatos aceitos (Resolvido → D-14)

Os formatos aceitos na primeira versão são exclusivamente imagens: JPEG, PNG e WebP. A infraestrutura de upload existente já suporta esses formatos sem alterações.

### 8.4 Autenticação e autorização (Resolvido → D-15)

O endpoint de OCR exige autenticação JWT e segue as mesmas regras de autorização dos endpoints de compras. Apenas usuários autenticados com permissão para registrar compras podem iniciar uma importação.

### 8.5 Campos extraídos e estrutura definitiva (Resolvido → D-16)

O Gemini deve extrair: nome do produto, quantidade, unidade comercial, preço unitário e subtotal do item. O `commercial_unit` e `conversion_factor` são extraídos quando presentes no documento; quando ausentes, não são inferidos — o operador preenche manualmente. O Gemini identifica e apresenta descontos quando presentes e legíveis, mas nenhum desconto é aplicado automaticamente — o operador informa o preço líquido manualmente. O subtotal do item é extraído quando impresso no documento; quando não disponível, é calculado a partir de quantidade e preço unitário para conferência. Data do documento e total do documento são extraídos quando legíveis.

### 8.6 Tolerância para divergências financeiras (Resolvido → D-17)

A conferência financeira compara o total informado no documento com o `extracted_total` (soma dos subtotais de todos os itens extraídos, inclusive excluídos). Quando houver divergência entre esses dois valores, o sistema alerta o operador sobre a divergência, mas não bloqueia a confirmação e não faz ajuste automático dos valores. O backend retorna três indicadores: `extracted_total` (base da conferência), `launched_total` (total efetivamente lançado) e `items_without_subtotal_count` (itens sem subtotal). A divergência é registrada nos logs da importação para referência posterior — esse registro não implica criação de mecanismo persistente de auditoria ou histórico de importações, preservando D-12 (resultados em memória) e D-17.

### 8.7 Tratamento de descontos (Resolvido → D-18)

O Gemini identifica e apresenta descontos quando presentes e legíveis no documento. Nenhum desconto é aplicado ou rateado automaticamente — o operador informa manualmente o preço líquido. A distribuição proporcional de descontos é melhoria futura, fora do escopo — ver `future-improvements.md`.

### 8.8 Matching e critérios de sugestão (Resolvido → D-19)

O matching usa três critérios, em ordem de prioridade:

1. **Correspondência exata normalizada:** o nome extraído é normalizado (minúsculas, remoção de acentos e espaços extras) e comparado com o nome do produto normalizado. Se houver correspondência exata, o sistema apresenta uma sugestão de produto.
2. **Correspondência parcial:** se não houver correspondência exata, o sistema busca substrings do nome extraído nos nomes dos produtos cadastrados e apresenta as sugestões encontradas.
3. **Fuzzy matching:** se não houver correspondência parcial, o sistema usa similaridade de texto (fuzzy matching) para apresentar os produtos mais próximos como sugestão.

O sistema apresenta uma sugestão de produto, que precisa ser confirmada pelo operador (D-4). Nenhuma associação é feita automaticamente sem revisão humana.

### 8.9 Regras completas do cadastro rápido (Resolvido → D-20)

Os campos mínimos para o cadastro rápido são: nome do produto (obrigatório) e unidade base (obrigatório). O preço de referência é opcional no cadastro rápido. O produto criado permanece pendente de complementação cadastral.

### 8.10 Modelo e versão do Gemini (Resolvido → D-21)

O modelo e versão do Gemini são configuráveis via variável de ambiente, permitindo ajustes sem alterar o código. A escolha do modelo será validada com documentos reais da Casa Afeto antes da implantação em produção. Os logs de extração registrarão o modelo usado para cada processamento, facilitando a comparação de resultados entre modelos.

### 8.11 Tratamento de falhas e repetição (Resolvido → D-22)

Se o processamento do OCR falhar, o operador é notificado. Não há reprocessamento automático — a repetição é manual e exige que o operador envie novamente o documento. O arquivo do documento é retido no servidor enquanto uma tentativa de processamento estiver em andamento. Após o processamento concluído — com sucesso ou falha —, o arquivo é excluído conforme D-13. Uma nova tentativa após falha concluída exige que o operador envie novamente o documento.

### 8.12 Prevenção de duplicidade (Resolvido → D-8)

O sistema utiliza a chave de acesso única da nota fiscal como identificador para prevenir duplicidade.

O OCR extrai a chave de acesso durante o processamento do documento. Antes da confirmação da compra, o sistema consulta se a chave já está associada a uma compra registrada. Se a chave já existir, a confirmação é bloqueada.

O hash do arquivo não é utilizado como mecanismo principal de detecção. Se futuramente forem aceitos documentos sem chave de acesso, a regra será reavaliada — ver `future-improvements.md`.

### 8.13 Data da compra (Resolvido → D-9)

A data identificada na nota fiscal é usada como sugestão para `purchased_at`. O operador pode revisar e alterar a data durante a confirmação.

Se a data estiver ausente ou ilegível no documento, o sistema não infere — solicita preenchimento manual pelo operador.

### 8.14 Itens parcialmente válidos (Resolvido → D-10)

O sistema permite lançar os itens válidos mesmo quando outros itens apresentam problemas. Os itens problemáticos permanecem fora do lançamento até serem corrigidos ou explicitamente descartados pelo operador.

A distinção entre total do documento e total efetivamente lançado no estoque é preservada (D-7).

**Exemplo:**
* Dez itens extraídos.
* Sete itens válidos e associados → lançados.
* Dois itens explicitamente excluídos → não lançados.
* Um item sem informação obrigatória legível → permanece pendente, não lançado.

---

## 9. Exceções e Situações que Exigem Revisão

O M13 deve lidar com as seguintes situações, apresentando-as claramente ao operador durante a revisão:

### 9.1 Informação ausente ou ilegível

Conforme D-3, o Gemini preserva informações ausentes como ausentes. Durante a revisão, os campos ausentes são sinalizados ao operador para preenchimento manual.

Os campos obrigatórios do contrato existente (`CreatePurchase` em `purchases/schemas.py`) devem ser validados para cada item que será lançado. Se um campo obrigatório permanece ausente após a revisão, a confirmação desse item é rejeitada.

A validação individual de cada item segue a decisão D-10 (§8.14): os itens válidos podem ser confirmados e lançados enquanto outros permanecem pendentes ou são explicitamente descartados.

### 9.2 Produto sem correspondência

Se um item extraído não corresponde a nenhum produto cadastrado, o operador pode:

* Cadastrar rapidamente o produto (D-5);
* Excluir o item (D-7);
* Associar manualmente a um produto existente.

A associação manual exige confirmação explícita do operador e validação de que o produto selecionado pode receber estoque (produto ativo, conforme PUR-006 e INV-008).

### 9.3 Sugestão de matching incorreta

O operador pode rejeitar a sugestão de matching e:

* Associar o item a outro produto;
* Cadastrar um novo produto (D-5);
* Excluir o item (D-7).

### 9.4 Conversão não confirmada

Se o operador não confirma a conversão proposta (unidade comercial, fator de conversão), ele pode:

* Informar manualmente a unidade e o fator;
* Confirmar a unidade-base do produto com fator 1, quando a unidade-base representar corretamente a quantidade adquirida.

O fator 1 não é um valor padrão automático — a unidade e o fator precisam ser revisados e confirmados explicitamente pelo operador.

### 9.5 Item excluído

Conforme D-7, o operador pode excluir itens. Os itens excluídos:

* Não são lançados na compra;
* Não alteram o total informado pelo fornecedor;
* Quando seus valores estiverem disponíveis, continuam considerados no total dos itens extraídos, mas não no total dos itens lançados;
* Não impedem o lançamento dos demais itens.

### 9.6 Falha no processamento

Se o processamento do OCR falhar:

* O operador é notificado da falha;
* O operador pode tentar novamente enviando o documento (D-22);
* Após o processamento concluído — com sucesso ou falha —, o arquivo é excluído conforme D-13;
* Uma nova tentativa após falha concluída exige que o operador envie novamente o documento;
* O vencimento não é inferido pelo Gemini (D-11); se o operador não puder identificar o vencimento fisicamente, o lote é criado com `expiry_date = NULL` (EXP-001).

### 9.7 Documento com informações inconsistentes

Se o documento contém informações inconsistentes (ex: total diferente da soma dos itens, quantidades negativas), o sistema:

* Extrai os dados conforme presentes no documento (D-3);
* Sinaliza as inconsistências ao operador durante a revisão;
* Não corrige automaticamente as inconsistências;
* A sinalização não autoriza contornar as validações do contrato de compras — quantidades, preços ou outros valores inválidos continuam sendo rejeitados pela validação existente.

---

## 10. Regras Preservadas

O M13 **deve preservar** integralmente as regras de estoque, compras, lotes e vencimentos existentes. Nenhuma regra é alterada, enfraquecida ou contornada pela importação.

### 10.1 Regras diretamente aplicáveis à importação

As regras seguintes são acionadas diretamente pelo fluxo de `create_purchase()` reutilizado pela importação. Para cada regra, o conteúdo é extraído fielmente do documento original e a justificativa descreve como o M13 a aciona:

| Regra | Referência | Conteúdo da regra | Justificativa para o M13 |
|---|---|---|---|
| **INV-001** | `business-contract.md` §38 | As alterações de estoque são representadas por meio de movimentações de estoque. | Comportamento de geração de movimentação: `create_purchase()` gera `InventoryMovement` do tipo ENTRY para cada item. Não é uma validação, mas o mecanismo pelo qual o estoque é atualizado. |
| **INV-008** | `business-contract.md` §38 | Um produto inativo não pode receber nenhuma Entrada ou Ajuste de estoque. | `create_purchase()` valida `product.active` antes de criar a compra (linha 37–40 do service). |
| **PUR-001** | M6 spec §5.2 | Uma compra registrada representa mercadoria já recebida fisicamente pela Casa Afeto. | A confirmação da importação registra compra recebida, seguindo o mesmo padrão. A atomicidade transacional é tratada por PUR-011. |
| **PUR-002** | M6 spec §5.2 | Cada item informa unidade comercial, fator de conversão (> 0) e quantidade (> 0). | `CreatePurchase` schema valida fator > 0 e quantidade > 0. |
| **PUR-003** | M6 spec §5.2 | Preço obrigatório, >= 0. Valores negativos rejeitados. | `CreatePurchase` schema valida `commercial_unit_price >= 0`. |
| **PUR-004** | M6 spec §5.2 | `unit_cost = commercial_unit_price / fator_de_conversão`, arredondado para duas casas. | `create_purchase()` calcula unit_cost (linha 69–71 do service). |
| **PUR-005** | M6 spec §5.2 | Para `base_unit = UN`, `quantidade_base` deve ser inteiro. | `create_purchase()` valida fracionário em UN (linha 48–52 do service). |
| **PUR-006** | M6 spec §5.2 | Um item de compra só pode referenciar um produto ativo. | `create_purchase()` valida `product.active` (linha 37–40 do service). |
| **PUR-011** | M6 spec §5.2 | Criação da compra e geração de ENTRY em uma única transação. Se falhar, tudo é revertido. | `create_purchase()` faz flush; o endpoint faz commit — transação atômica. |
| **PUR-012** | M6 spec §5.2 | SELECT FOR UPDATE com ordem crescente de `product_id` para evitar deadlocks. | `create_purchase()` ordena itens por `product_id` (linha 62 do service). |
| **LOT-001** | M7 spec §5, `business-contract.md` §12 | Cada item de compra gera automaticamente um lote com quantidade em unidade-base e unit_cost. | `create_movement()` cria `StockBatch` automaticamente para ENTRY vinculada a compra. |
| **LOT-008** | M7 spec §5, `business-contract.md` §12 | O saldo físico do produto é a soma das `quantity_remaining` de todos os lotes com status ACTIVE. | `create_batch()` cria o lote com `quantity_remaining = quantity`, participando diretamente da manutenção da invariante de saldo físico. A importação, ao gerar ENTRY via `create_purchase()`, aciona `create_batch()` que mantém essa invariante. |
| **LOT-006** | M7 spec §5, `business-contract.md` §12 | Cada lote vinculado a compra preserva `purchase_id` e `purchase_item_id`. | `create_purchase()` passa `purchase_id` e `purchase_item_id` para `create_movement()` (linha 95–96 do service). |
| **EXP-001** | M8 spec §2, `business-contract.md` §13 | `expiry_date` é opcional. Lotes sem vencimento representam produtos não perecíveis. | `expiry_date` em `CreatePurchase` é nullable; o lote herda NULL quando não informado. |
| **EXP-002** | M8 spec §2, `business-contract.md` §13 | Quando um item de compra inclui `expiry_date`, o lote criado herda essa data. | `create_purchase()` passa `expiry_date` para `create_movement()` (linha 97 do service). |

### 10.2 Regras preservadas, mas não acionadas diretamente pela importação

As regras seguintes são preservadas pelo sistema e continuam válidas, mas tratam de operações posteriores à criação da compra, de outros fluxos ou de comportamentos que a importação não executa. Para cada regra, o conteúdo é extraído fielmente do documento original:

| Regra | Referência | Conteúdo da regra | Motivo da classificação |
|---|---|---|---|
| **INV-002** | `business-contract.md` §38 | Correções de estoque devem preservar o histórico original de movimentações. | A regra trata de **correções** que não reescrevem ENTRY existentes. A importação cria novas ENTRY — não corrige as existentes. A regra é preservada, mas não é acionada pelo fluxo de criação. |
| **INV-003** | `business-contract.md` §38 | Um produto com estoque insuficiente pode ser selecionado para uma cesta ou venda. | Contexto de vendas (seleção de produto para cesta), não de compras. |
| **INV-004** | `business-contract.md` §38 | A reserva de estoque e a baixa física associadas às vendas seguem a política formal. | Contexto de vendas (reserva e baixa), não de compras. |
| **INV-005** | `business-contract.md` §38 | Alterações na composição de uma venda após a reserva seguem regras de diferença. | Contexto de vendas (alteração de cestas), não de compras. |
| **INV-006** | `business-contract.md` §38 | O sistema não deve criar uma movimentação que faça o saldo físico se tornar negativo. | A regra é acionada por `create_movement()` para **OUTPUT** e **ADJUSTMENT negativo**. Uma ENTRY adiciona estoque — nunca causa saldo negativo. A regra é preservada como invariante geral, mas não é acionada durante a criação de ENTRY. |
| **INV-007** | `business-contract.md` §38 | No início da preparação de uma venda, o sistema executa a baixa física. | Contexto de vendas (preparação), não de compras. |
| **PUR-007** | M6 spec §5.2 | O registro de uma compra não modifica o `reference_price` do produto. | `create_purchase()` não toca em `reference_price`. A regra é uma restrição preservada sobre o comportamento do serviço, não uma validação executada durante a criação. |
| **PUR-008** | M6 spec §5.2 | Compras recebidas não podem ser excluídas nem revertidas silenciosamente. | A regra trata de **exclusão após a criação**. A importação cria a compra — a restrição de exclusão aplica-se posteriormente. |
| **PUR-009** | M6 spec §5.2 | Se uma compra foi registrada com erro, a correção é feita por uma nova compra complementar. | A regra trata de **correção de compra errada**, não de criação normal. Aplica-se se a importação contiver erro, mas não é acionada durante a criação. |
| **PUR-010** | M6 spec §5.2 | O sistema deve permitir consultar compras filtradas por período. | A regra trata de **consulta posterior** às compras. As compras importadas aparecem nas consultas, mas a regra não é acionada durante a criação. |
| **LOT-002** | M7 spec §5, `business-contract.md` §12 | Cada ENTRY manual (não vinculada a compra) gera um lote com `purchase_id = NULL`. | Aplicável apenas a entradas manuais. A importação gera compra, não entrada manual. |
| **LOT-003** | M7 spec §5, `business-contract.md` §12 | Ao registrar saída de estoque, consumir do lote mais antigo primeiro (FIFO). | Contexto de saída de estoque, não de entrada. Substituído por FEFO no M8. |
| **LOT-004** | M7 spec §5, `business-contract.md` §12 | Quando `quantity_remaining` chega a zero, o lote muda para status EXHAUSTED. | Ocorre ao **consumir** lotes, não ao criá-los. |
| **LOT-005** | M7 spec §5, `business-contract.md` §12 | Um lote de estoque não pode ser excluído. | Restrição preservada sobre o lote após a criação, não acionada durante a criação. |
| **LOT-007** | M7 spec §5, `business-contract.md` §12 | O `unit_cost` do lote não é alterado após a criação. | A regra trata da **imutabilidade após a criação**. A importação define o custo ao criar o lote — a imutabilidade aplica-se posteriormente. |
| **LOT-009** | M7 spec §5, `business-contract.md` §12 | O cálculo de custo médio ponderado é removido. | Decisão arquitetural do M7, preservada, mas não acionada pela importação. |
| **LOT-010** | M7 spec §5, `business-contract.md` §12 | Operações que modificam lotes seguem SELECT FOR UPDATE com ordenação por `product_id`. | Preservado; a concorrência de entrada é coberta por PUR-012. |
| **EXP-003** | M8 spec §2, `business-contract.md` §13 | A data de vencimento de um lote não pode ser alterada após a criação. | Restrição preservada sobre o lote **após a criação**, não acionada durante a criação. |
| **EXP-004** | M8 spec §2, `business-contract.md` §13 | O consumo de estoque usa FEFO (First Expired, First Out) como política padrão, substituindo o FIFO. | Contexto de saída de estoque, não de entrada. |
| **EXP-005** | M8 spec §2, `business-contract.md` §13 | Um lote vencido continua ativo e pode ser consumido pelo FEFO. O sistema não bloqueia automaticamente o consumo. | Contexto de alerta e consumo, não de criação. |
| **EXP-006** | M8 spec §2, `business-contract.md` §13 | Um lote é considerado "próximo do vencimento" quando `expiry_date - hoje <= threshold_dias`. | Contexto de alerta, não de criação. |
| **EXP-007** | M8 spec §2, `business-contract.md` §13 | Um lote é considerado "vencido" quando `expiry_date < hoje`. Destacado com urgência maior. | Contexto de alerta, não de criação. |
| **EXP-008** | M8 spec §2, `business-contract.md` §13 | O sistema expõe uma API para listar todos os lotes ativos com vencimento próximo ou vencido. | Contexto de consulta/alerta, não de criação. |
| **EXP-009** | M8 spec §2, `business-contract.md` §13 | O modal de estoque destaca lotes com badges visuais: vencido (vermelho), próximo do vencimento (amarelo). | Contexto de alerta visual, não de criação. |
| **EXP-010** | M8 spec §2, `business-contract.md` §13 | Ao registrar uma entrada manual de estoque, o operador pode informar a data de vencimento. Se não informada, o lote é criado com `expiry_date = NULL`. | Contexto de entrada manual, não de compra. A importação gera compra, não entrada manual. |

---

## 11. Notas

* Esta especificação é a versão 1.4 (revisada) e está pendente de aprovação do Product Owner.
* A numeração M13 é provisória e depende de confirmação no roadmap — ver D-6.
* As decisões aprovadas D-1 a D-22 estão registradas em `docs/milestones/m13-ocr-import/decisions.md`.
* Não há decisões pendentes: todas as decisões necessárias para o M13 foram aprovadas.
* A integração com o serviço de compras é feita por reutilização; adaptações serão justificadas se necessárias.
* A branch `ocr-gemini` não foi consultada como referência para esta especificação.

---

## 12. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 0.1 | 2026-11-02 | Especificação inicial criada. |
| 0.2 | 2026-11-02 | Revisão corretiva: escopo separado (fora do escopo vs. pendente), três totais distintos, D-2 não proíbe adaptações, cadastro rápido com validações explícitas, fator 1 não é padrão automático, D-1 esclarecido, vencimento opcional na etapa 12, associação manual com confirmação, campos obrigatórios pelo contrato existente, referências INV/PUR/LOT/EXP conferidas e corrigidas, decisão pendente 8.14 adicionada (itens parcialmente válidos). |
| 0.3 | 2026-11-02 | Revisão corretiva: três totais uniformizados (total do documento, total dos itens extraídos sem estimar valores ausentes, total dos itens lançados); itens excluídos não alteram total do fornecedor; regras INV, PUR, LOT e EXP classificadas individualmente com base nos documentos originais (INV-002 movida para aplicável, PUR-007 a PUR-010 adicionadas, LOT-002 classificado como contextual, LOT-003 a LOT-010 listados individualmente, EXP-003 a EXP-010 listados individualmente); validação de itens parcialmente válidos esclarecida; extração do total do fornecedor incluída como questão pendente; inconsistências no documento não contornam validações; numeração M13 indicada como provisória. |
| 0.4 | 2026-11-02 | Revisão corretiva: regras INV, PUR, LOT e EXP reclassificadas com base no conteúdo real de cada regra e no fluxo efetivo de `create_purchase()` — INV-002, INV-006, PUR-007 a PUR-010 e LOT-007 movidas para "preservadas, mas não acionadas diretamente" com justificativas específicas; §7.1 reescrito para distinguir validações executadas de regras preservadas; M7 spec adicionado a §3 dependências; §6.1 reescrito com tabela que distingue informação relevante, extração obrigatória e pendência de decisão; subtotal do item esclarecido como derivável; §2.3 simplificado (adaptações removidas de pendente); §7.2 reescrito para tratar adaptações como questão técnica, não funcional. |
| 0.5 | 2026-11-02 | Revisão corretiva: EXP-010 corrigido (conteúdo duplicado de EXP-003 substituído pelo texto original do M8); EXP-003 também corrigido ("Vencimento imutável" em vez de "entrada manual"); PUR-001 separado de PUR-011 (atomicidade transacional pertence a PUR-011); LOT-008 movido para "diretamente aplicáveis" pois `create_batch()` mantém a invariante de saldo físico; §6.1 reescrito com 6 colunas distinguindo extração do Gemini, obrigatoriedade do contrato e preenchimento manual; §5.2 referência corrigida de §7.3 para §7.2; §4 etapa 12 e §7.1 harmonizados (INV-001 identificado como comportamento de geração, não validação). |
| 0.6 | 2026-11-02 | Revisão corretiva pontual: PUR-001 (recebimento físico) — adicionada etapa 11 no fluxo funcional confirmando que as mercadorias foram recebidas fisicamente antes da confirmação da importação; §6.1 — corrigido "5 colunas" para "6 colunas" no histórico da v0.5; corrigido erro de digitação "extrê-lo" para "extraí-lo".
| 0.7 | 2026-11-03 | Ajuste pontual: etapa 11 do fluxo funcional esclarecida para abranger apenas as mercadorias incluídas no lançamento e explicitar a obrigatoriedade da confirmação de recebimento físico.
| 0.8 | 2026-11-03 | Consolidação das decisões: §8.12 (prevenção de duplicidade via chave de acesso → D-8), §8.13 (data da compra pela nota → D-9), §8.14 (itens parcialmente válidos → D-10) resolvidos e registrados; nova §5.7 (conferência de vencimentos e lotes múltiplos → D-11) adicionada; §6.1 atualizado (vencimento não extraído pelo Gemini); §4 atualizado (etapa 9b, divisão em lotes); §11 atualizado (10 decisões pendentes restantes).
| 0.9 | 2026-11-03 | Correções finais: §2.3 — removida referência à prevenção de duplicidade como pendente (D-8 já resolveu); §7.1 — adicionada documentação da chave de acesso (`access_key`) com restrição de unicidade e obrigatoriedade para notas fiscais no escopo atual; §7.3 — adicionada nota sobre múltiplos `CreatePurchaseItem` para lotes distintos (D-11) e nota sobre chave de acesso mantida temporariamente; §8 — todas as 11 decisões pendentes (§8.1 a §8.11) aprovadas e registradas como D-12 a D-22; §9.6 — atualizado para D-22; §11 — zero decisões pendentes, D-1 a D-22 registradas.
| 1.0 | 2026-11-03 | Auditoria e correção final de consistência: §2.3 — removidas referências a retenção e formatos como pendentes (D-13, D-14 já resolveram); §3 — referenciado D-1 a D-22; §5.1 — harmonizado com D-12 e D-13; §5.4 — três critérios de matching (D-19); §5.5 — campos mínimos do cadastro rápido (D-20); §6.1 — tabela atualizada conforme D-16 (unidade, subtotal, data, total); §6.2 — campos resolvidos, não mais pendentes; §6.3 — schema definido por D-16 a D-18; §7.1 — access_key unicidade revisada (SELECT não bloqueia chave inexistente); §8.1 — perda de estado por reinicialização do backend, não fechamento do navegador; §8.2 — arquivo excluído após processamento concluído, não após confirmação; §8.3 — formatos JPEG, PNG, WebP (sem PDF); §8.4 — JWT e mesmas regras de autorização dos endpoints de compras; §8.5 — sem inferência de unidade ou fator ausentes; §8.6 — divergência registrada nos logs, sem mecanismos de auditoria persistente; §8.8 — matching completo (exato normalizado, parcial, fuzzy); §8.10 — modelo configurável, logs e validação com documentos reais; §8.11 — falhas com retenção do arquivo até processamento concluído; §9.6 — harmonizado com D-11 e D-13; §11 — versão 1.0.
| 1.1 | 2026-11-03 | Revisão corretiva final: §5.1 — estado em memória (D-12) e retenção (D-13, D-22) harmonizados; §8.1 — estado em memória harmonizado; §8.2 — retenção harmonizada; §6.2 — título corrigido para "Campos e regras de extração definidos", subtotais diferenciados (impresso vs. calculado); §6.3 — título corrigido para "Estrutura dos dados extraídos"; §6.1 — subtotais diferenciados; §7.3 — adicionados dados da compra (purchased_at, access_key) e nota sobre constraint UNIQUE; §7.5 → §7.4 (numeração corrigida); §8.8 — matching reformulado para evitar sugestão de associação automática; §8.11 — falhas harmonizadas com D-13 e D-22; §9.6 — falhas harmonizadas com D-13 e D-22; §11 — versão 1.1.
| 1.2 | 2026-11-03 | Correções pontuais finais: §5.1 e §8.1 — removida referência ao encerramento da sessão do operador como causa de perda de estado (D-12); §8.11 — corrigida contradição sobre retentativa sem reenvio, toda retentativa exige reenvio do documento (D-13, D-22); §1.1 — escopo restrito a notas fiscais com chave de acesso, sem sugerir suporte a recibos; §6.2 e §8.5 — descontos harmonizados com D-18: Gemini identifica, operador informa preço líquido, sem rateio automático; §8.7 — descontos harmonizados com D-18; §9.6 — harmonizado com §8.11; §5.7 — corrigido "permite" para "pode"; §11 — versão 1.2.
| 1.3 | 2026-11-03 | Revisão final: complemento da D-11 — soma das quantidades dos lotes deve igualar a quantidade original do item, divergência impede confirmação, validação antes de `create_purchase()` (§5.7, §7.3); complemento da D-17 — conferência financeira compara total do documento com total dos itens extraídos (base da conferência), três indicadores distintos, alerta sem bloqueio (§5.6, §8.6); §1.3 — M7 incluído na relação de marcos; §5.5 — removida frase duplicada sobre cadastro rápido; §8.5 — subtotais esclarecidos (impressos vs. calculados); §11 — versão 1.3.
| 1.4 | 2026-11-03 | Correções pontuais: §2.1 — três totais (total do documento, total dos itens extraídos como base da conferência, total dos itens lançados); §2.2 — reconciliação financeira substituída por "reconciliação ou ajuste financeiro automático"; §5.7 — conservação de quantidades esclarecida em unidade-base após fatores de conversão confirmados; §7.3 — mesma regra de unidade-base aplicada ao mapeamento CreatePurchaseItem; §8.6 — logs da importação não implicam persistência de auditoria (preservando D-12 e D-17); D-11 em decisions.md atualizada com esclarecimento de unidade-base; §11 — versão 1.4. |
| 1.5 | 2026-11-03 | Correções finais antes de aprovação: §5.1 — contradição sobre processamento assíncrono eliminada (asyncio.create_task para agendamento, asyncio.to_thread para execução do OCR); §7.1 — validação da access_key definida (44 dígitos numéricos, editável, obrigatória na confirmação); §7.1 — IntegrityError identifica constraint UNIQUE por nome, HTTP 500 genérico para erros inesperados; §7.1 — falhas antes e depois do commit separadas (rollback e restauração para completed antes do commit; nunca restaurar após commit); §7.3 — ConfirmImportRequest definido com confirmed_items e excluded_item_ids, validação de cobertura total sem duplicidade ou sobreposição; §7.3 — cálculo de commercial_unit_price transferido para backend (item.price × lot.factor / item.factor); §5.6 — três totais definidos explicitamente (extracted_total, launched_total, items_without_subtotal_count), extracted_total inclui itens excluídos; §8.6 — harmonizado com os três totais; §11 — versão 1.5.
