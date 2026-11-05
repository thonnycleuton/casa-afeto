# M13 — Decisões Aprovadas

**Versão do documento:** 0.5
**Status:** Decisões aprovadas pelo Product Owner
**Marco:** M13 — Importação de Documentos de Compra com Gemini
**Data:** 2026-11-02
**Última atualização:** 2026-11-03

---

## Objetivo

Registrar permanentemente as decisões aprovadas para o M13 — Importação de Documentos de Compra com Gemini.

Este documento preserva as decisões tomadas antes da elaboração da especificação detalhada. Decisões posteriores poderão complementá-lo, sem alterar silenciosamente as decisões já registradas.

---

## D-1 — Processamento assíncrono

O processamento será assíncrono, com polling simples para acompanhamento do status. A implementação inicial utilizará `asyncio.to_thread()`, sem Redis, Celery ou outra infraestrutura de filas.

---

## D-2 — Aderência à arquitetura do Casa Afeto

A funcionalidade será implementada seguindo os padrões e a arquitetura existentes no Casa Afeto. Não copiar a arquitetura de outros projetos ou protótipos.

---

## D-3 — Extração fiel ao documento

O Gemini deverá extrair os dados presentes no documento, preservando informações ausentes ou ilegíveis como ausentes. Não deverá inventar valores nem completar informações por suposição.

---

## D-4 — Matching sujeito à confirmação humana

O matching entre itens extraídos e produtos cadastrados será apresentado como sugestão. A associação e as conversões propostas deverão ser revisadas e confirmadas pelo operador antes do lançamento da compra.

---

## D-5 — Cadastro rápido de produto

Durante a revisão, será possível cadastrar rapidamente um produto inexistente. O cadastro utilizará os campos mínimos necessários e as validações já existentes no sistema. O produto permanecerá pendente de complementação cadastral.

---

## D-6 — Independência e posicionamento do marco

O M13 será um marco independente, posterior ao M6. Sua numeração definitiva e seu posicionamento no roadmap dependerão de confirmação posterior.

---

## D-7 — Exclusão de itens

O operador poderá excluir explicitamente itens rejeitados ou não destinados ao estoque sem impedir o lançamento dos demais itens válidos e associados a produtos.

A interface deverá diferenciar claramente:

- Total do documento.
- Total dos itens efetivamente lançados no estoque.

---

## D-8 — Prevenção de duplicidade

O sistema utiliza a chave de acesso única da nota fiscal como identificador para prevenir a importação duplicada do mesmo documento.

A chave de acesso é extraída pelo OCR durante o processamento. Antes da confirmação da compra, o sistema consulta se a chave já está associada a uma compra registrada. Se a chave já existir, a confirmação é bloqueada.

O hash do arquivo não é utilizado como mecanismo principal de detecção. Se futuramente forem aceitos documentos sem chave de acesso, a regra será reavaliada.

---

## D-9 — Data da compra

A data identificada na nota fiscal é usada como sugestão para a data da compra (`purchased_at`). O operador pode revisar e alterar a data durante a confirmação.

Se a data estiver ausente ou ilegível no documento, o sistema não infere — solicita preenchimento manual pelo operador.

---

## D-10 — Itens parcialmente válidos

O sistema permite lançar os itens válidos mesmo quando outros itens apresentam problemas. Os itens problemáticos permanecem fora do lançamento até serem corrigidos ou explicitamente descartados pelo operador.

A distinção entre total do documento e total efetivamente lançado no estoque é preservada.

---

## D-11 — Conferência de vencimentos e lotes múltiplos

As notas fiscais dos fornecedores não apresentam vencimentos por item ou lote. O Gemini não deve inferir nem extrair vencimentos inexistentes no documento.

A conferência de vencimentos é realizada fisicamente pelo operador nas mercadorias recebidas. Durante a revisão da compra, o operador pode dividir a quantidade de um item em múltiplos lotes, onde cada lote tem quantidade e vencimento próprios.

Quando um item extraído for dividido em múltiplos lotes, a conservação das quantidades deve ser verificada em unidade-base, após aplicação dos fatores de conversão confirmados:

- As quantidades atribuídas aos lotes podem utilizar unidades comerciais diferentes, desde que sejam válidas e confirmadas.
- Cada quantidade deve ser convertida para a unidade-base do produto usando seu fator de conversão confirmado.
- A soma das quantidades convertidas deve corresponder exatamente à quantidade total confirmada do item original, também expressa em unidade-base.
- Divergências para mais ou para menos impedem a confirmação.
- A validação ocorre antes da chamada a `create_purchase()`.

Quando o vencimento não puder ser identificado, o operador pode criar lote com vencimento desconhecido (`expiry_date = NULL`), conforme as regras existentes.

As regras de lotes e FEFO estabelecidas no M6/M8 são preservadas integralmente.

---

## D-12 — Persistência dos resultados do OCR

Os resultados do OCR não são persistidos no banco de dados antes da confirmação do operador. O fluxo é mais simples: se o operador fechar a sessão antes de confirmar, os dados extraídos são perdidos e o documento precisa ser reenviado.

---

## D-13 — Política de retenção dos documentos

Os documentos enviados são excluídos do servidor após o processamento concluído — independentemente de a compra ter sido confirmada ou rejeitada. O arquivo é retido apenas durante o processamento e a revisão; após o processamento concluído, o arquivo é excluído. Não há retenção permanente nem temporária — o reprocessamento requer reenvio do documento.

---

## D-14 — Formatos aceitos

Os formatos aceitos na primeira versão são exclusivamente imagens: JPEG, PNG e WebP. A infraestrutura de upload existente já suporta esses formatos sem alterações.

---

## D-15 — Autenticação e autorização

O endpoint de OCR exige autenticação JWT e segue as mesmas regras de autorização dos endpoints de compras. Apenas usuários autenticados com permissão para registrar compras podem iniciar uma importação.

---

## D-16 — Campos extraídos e estrutura definitiva

O Gemini deve extrair: nome do produto, quantidade, unidade comercial, preço unitário e subtotal do item. O `commercial_unit` e `conversion_factor` são extraídos quando presentes no documento; quando ausentes, não são inferidos — o operador preenche manualmente. Descontos, subtotais parciais e data do documento são extraídos quando legíveis. O total impresso no documento pelo fornecedor é extraído quando legível.

---

## D-17 — Tolerância para divergências financeiras

A conferência financeira compara o total informado no documento com a soma dos valores de todos os itens extraídos, independentemente de exclusão ou seleção para lançamento no estoque. Quando houver divergência entre esses dois valores, o sistema alerta o operador sobre a divergência, mas não bloqueia a confirmação e não faz ajuste automático dos valores. A divergência é registrada como informação para auditoria.

---

## D-18 — Tratamento de descontos

Os descontos são ignorados no M13. O operador informa o preço líquido manualmente quando o documento contém descontos. A distribuição proporcional de descontos é registrada como melhoria futura — ver `future-improvements.md`.

---

## D-19 — Matching e critérios de sugestão

O matching usa três critérios, em ordem de prioridade:

1. **Correspondência exata normalizada:** o nome extraído é normalizado (minúsculas, remoção de acentos e espaços extras) e comparado com o nome do produto normalizado.
2. **Correspondência parcial:** busca de substrings do nome extraído nos nomes dos produtos cadastrados.
3. **Fuzzy matching:** similaridade de texto para sugerir os produtos mais próximos.

A sugestão é sempre apresentada ao operador para confirmação (D-4). Nenhum matching é aplicado automaticamente sem revisão humana.

---

## D-20 — Regras completas do cadastro rápido

Os campos mínimos para o cadastro rápido são: nome do produto (obrigatório) e unidade base (obrigatório). O preço de referência é opcional no cadastro rápido. O produto criado permanece pendente de complementação cadastral.

---

## D-21 — Modelo e versão do Gemini

O modelo e versão do Gemini são configuráveis via variável de ambiente, permitindo ajustes sem alterar o código. A escolha do modelo será validada com documentos reais da Casa Afeto antes da implantação em produção. Os logs de extração registrarão o modelo usado para cada processamento, facilitando a comparação de resultados entre modelos.

---

## D-22 — Tratamento de falhas e repetição

Se o processamento do OCR falhar, o operador é notificado e pode tentar novamente. Não há reprocessamento automático — a repetição é manual. O arquivo do documento é retido no servidor até o processamento concluído, permitindo que o operador tente novamente sem reenviar o arquivo. Após o processamento concluído (com sucesso ou falha), o arquivo é excluído conforme D-13.

---

## Decisões pendentes

Decisões posteriores (D-12 em diante) poderão ser adicionadas a este documento conforme forem aprovadas.

Todas as decisões necessárias para o M13 foram aprovadas e registradas (D-1 a D-22). Não há decisões pendentes.

---

## Notas

- Este documento não é um ADR (Architecture Decision Record). As decisões registradas abrangem tanto decisões de produto quanto decisões técnicas de nível de marco.
- A especificação detalhada, os casos de uso, os critérios de aceitação e o plano de validação do M13 serão elaborados em documentos separados, com base nestas decisões aprovadas.
- As melhorias futuras não incluídas no escopo do M13 estão registradas em `future-improvements.md`.
- Todas as 22 decisões (D-1 a D-22) foram aprovadas pelo Product Owner. Não há decisões pendentes para o M13.
