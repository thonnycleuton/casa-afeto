# Casa Afeto — Especificação Funcional do Módulo de Compras

**Versão:** 1.3 — Consolidação de pendências e reconciliação OCR

---

## 1. Objetivo

Centralizar o registro das compras de produtos utilizados na montagem das cestas, permitindo inserção manual ou importação de documentos fiscais por OCR.

Os dois caminhos devem produzir o mesmo registro de compra.

---

## 2. Formas de registro

### 2.1. Compra manual

- Permitir adicionar produtos manualmente.
- Informar quantidades, unidades e preços.
- Informar dados fiscais, quando disponíveis.
- Permitir anexar a imagem do documento original.
- Os dados fiscais não são obrigatórios.

### 2.2. Importação por documento (OCR)

- Receber a imagem do documento.
- Extrair automaticamente os dados disponíveis.
- Sugerir correspondência entre os produtos identificados e os produtos cadastrados.
- Permitir cadastro rápido de produtos inexistentes.
- Permitir revisar e corrigir todas as informações extraídas.
- Não confirmar automaticamente produtos, unidades ou conversões sugeridas pelo OCR.

---

## 3. Dados da compra

### Identificação e dados fiscais

Os dados fiscais abaixo são extraídos do documento quando disponíveis. Todos são opcionais — a ausência de um ou mais campos fiscais não impede o registro da compra.

- **Data da compra** — extraída do documento quando legível; usada como sugestão para `purchased_at`. O operador pode revisar e alterar.
- **Nome do fornecedor** — extraído quando disponível.
- **CNPJ** — extraído quando disponível.
- **Número do documento** — extraído quando disponível.
- **Chave de acesso** — extraída quando disponível; deve conter 44 dígitos numéricos. O operador pode editar o valor extraído durante a revisão.
- **Imagem original do documento** — associada à compra e preservada permanentemente.

### Itens

- Produto.
- Quantidade comprada.
- Unidade comercial.
- Conversão para unidade-base de estoque, quando aplicável.
- Preço unitário.
- Subtotal.
- Descontos identificados.
- Data de validade, quando aplicável.

### Totais

- Total informado no documento.
- Total dos itens extraídos.
- Total efetivamente lançado na compra.

Os descontos identificados devem ser preservados como informação, sem aplicação automática aos custos dos produtos.

---

## 4. Status da compra

A compra possui dois estados:

- **Rascunho:** compra persistida no banco de dados, editável, sem movimentações de estoque.
- **Confirmada:** compra efetivada, com movimentações de entrada registradas no estoque.

Não existem estados "Editada" ou "Cancelada" nesta versão.

---

## 5. Persistência dos rascunhos

- Compras em aberto (rascunhos) devem ser persistidas no banco de dados.
- Devem sobreviver a reinicializações do backend.
- Devem permitir retomada e edição posterior.
- A persistência da compra em rascunho é diferenciada da sessão temporária de processamento OCR, que armazena dados voláteis durante a extração.

---

## 6. Confirmação da compra

Antes da confirmação, a compra deve permitir revisão dos dados e dos itens.

Ao confirmar:

- Registrar definitivamente a compra.
- Registrar seus itens.
- Gerar as movimentações de entrada no estoque.
- Registrar os lotes e respectivas validades, quando aplicável.
- Preservar os dados fiscais e o documento original.
- Garantir a consistência entre a compra registrada e as movimentações de estoque.

Itens rejeitados ou que não devem integrar o estoque podem ser excluídos do lançamento, sem alterar o total originalmente informado no documento.

---

## 7. Edição de compras

A regra de edição depende do status da compra.

### 7.1. Compras em Rascunho

Permitir edição completa:

- Dados fiscais e descritivos.
- Adição e remoção de itens.
- Alteração de quantidades.
- Alteração de preços.
- Alteração das demais informações dos itens.

### 7.2. Compras Confirmadas

A confirmação da compra representa a efetivação definitiva dos seus itens e das respectivas movimentações de estoque.

Permitir edição somente de:

- Dados fiscais.
- Informações descritivas que não afetem o estoque.

Bloquear:

- Adição de itens.
- Remoção de itens.
- Alteração de quantidades.
- Alteração de preços dos itens.

Não implementar mecanismos de correção de itens confirmados, estornos ou movimentações compensatórias neste escopo.

---

## 8. Conversão de unidades

- Utilizar o fator de conversão cadastrado no produto como sugestão inicial.
- Permitir conferência e correção pelo operador.
- Exibir alerta visual quando unidade comercial e unidade-base forem diferentes e o fator informado for 1.
- O alerta não deve bloquear a operação.
- Não presumir automaticamente que fatores diferentes de 1 são obrigatórios.

---

## 9. Arquivo temporário OCR e documento permanente

Esta seção distingue dois conceitos que não devem ser confundidos: o arquivo temporário usado durante o processamento OCR e o documento original preservado permanentemente associado à compra.

### 9.1. Arquivo temporário OCR

O arquivo temporário é utilizado exclusivamente pelo processamento do Gemini durante a extração de dados:

- É mantido no servidor após falha no processamento para permitir retentativa manual sem novo upload.
- Pode ser descartado quando o operador descarta a sessão falha.
- Após reinicialização do backend, as sessões OCR em memória são perdidas e os arquivos órfãos são removidos pelo mecanismo de limpeza existente, respeitando a regra de idade superior a uma hora.
- Deixa de ser necessário após processamento bem-sucedido do OCR.

### 9.2. Documento original da compra

O documento original é a imagem ou digitalização do documento fiscal enviado pelo operador:

- Deve ser preservado permanentemente após ser associado a uma compra.
- Deve permanecer disponível no detalhamento da compra, inclusive após confirmação.
- Não pode ser excluído pelo descarte de uma sessão OCR.
- Sua preservação não pode depender da existência da sessão OCR.
- A exclusão de uma sessão OCR não pode excluir um documento já associado a uma compra.

---

## 10. Descontos

Distinguir:

- Descontos individuais dos itens.
- Descontos gerais do documento.

Regras:

- Ambos devem ser preservados como informações, sem distribuição ou aplicação automática aos custos dos produtos.
- Nenhum desconto deve ser distribuído automaticamente entre os produtos.
- Nenhum desconto deve ser aplicado automaticamente ao custo dos produtos.
- A forma técnica de persistência (campos separados, estrutura JSON, tabela associada) será definida durante a especificação técnica.

---

## 11. Política OCR — retenção e descarte

Esta seção consolida o comportamento de retenção e descarte de arquivos OCR, utilizando D-22 como referência para retentativa e descarte após falha.

Quando D-12 ou D-13 contiverem decisões incompatíveis com D-22, a precedência é de D-22 para retentativa e descarte. Esta divergência é registrada aqui sem alterar retroativamente os documentos originais de decisão.

### 11.1. Falha no processamento

- Manter o arquivo temporário no servidor para permitir retentativa manual.
- O operador é notificado da falha e pode tentar novamente sem reenviar o arquivo.

### 11.2. Retentativa

- Utilizar o mesmo arquivo temporário, sem novo upload.
- Não há reprocessamento automático — a repetição é manual.

### 11.3. Descarte pelo operador

- Remover a sessão OCR e seu arquivo temporário.
- O documento original associado a uma compra não é afetado.

### 11.4. Sucesso do OCR

- O arquivo temporário deixa de ser necessário após o processamento bem-sucedido.
- O documento original é preservado permanentemente conforme a Seção 9.2.

### 11.5. Reinicialização do backend

- As sessões OCR em memória são perdidas.
- Os arquivos órfãos com mais de uma hora são removidos pelo mecanismo de limpeza existente.

### 11.6. Restrições

- Não criar TTL, scheduler, Redis, Celery ou mecanismo adicional de processamento para gerenciar o ciclo de vida dos arquivos OCR.

---

## 12. Armazenamento permanente

O documento original da compra deve ter armazenamento permanente e associação com a compra registrada.

Regras funcionais:

- O documento deve permanecer acessível pelo detalhamento da compra após confirmação.
- A preservação do documento não depende do ciclo de vida da sessão OCR.
- O documento não pode ser excluído por operações de limpeza de sessões temporárias.

Detalhes técnicos — incluindo a escolha entre sistema de arquivos e banco de dados, diretórios, nomes, metadados e mecanismos de acesso — serão definidos durante a especificação técnica.

---

## 13. Histórico

A listagem de compras deve permitir consultar:

- Data.
- Fornecedor, quando disponível.
- Número do documento, quando disponível.
- Quantidade de itens.
- Valor total.
- Situação da compra.

O detalhamento deve apresentar os itens, os dados fiscais disponíveis e a imagem original do documento.

---

## 14. Fora do escopo atual

- Cadastro e gerenciamento de fornecedores.
- Fluxo de aprovação de compras.
- Estornos complexos.
- Histórico detalhado de versões.
- Auditoria avançada de alterações.
- Integração automática com fornecedores.
- Processamento automático de documentos sem revisão humana.

---

## 15. Pendências

As seguintes decisões ainda não foram definidas e serão resolvidas durante a especificação técnica:

- **Formato técnico de persistência dos descontos.** Como os descontos individuais e gerais serão armazenados (campos separados, estrutura JSON, tabela associada) não foi definido.
- **Escolha técnica de armazenamento permanente.** Se o documento original será armazenado no sistema de arquivos ou no banco de dados, assim como diretórios, nomes, metadados e mecanismos de acesso, será definido durante a especificação técnica.

---

## 16. Diretriz de implementação

Reutilizar a estrutura de compras e movimentações de estoque já implementada em M6 e o processo de importação OCR de M13.

A compra manual e a compra importada devem convergir para o mesmo processo de confirmação.

Não duplicar regras de negócio nem criar estruturas adicionais sem necessidade funcional comprovada.

**Princípio geral:** o OCR facilita o preenchimento; a confirmação humana registra a compra; o módulo de compras é responsável pela consistência do estoque.

---

## 17. Histórico de versões

| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0 | — | Especificação inicial do módulo de Compras |
| 1.1 | — | Consolidação funcional com decisões aprovadas (status, persistência de rascunhos, conversão de unidades, preservação de documentos, descontos) |
| 1.2 | 2026-11-05 | Atualização após auditoria técnica de M6/M13: nova regra de edição de compras confirmadas (seção 7 substituída), pendências explicitadas (seção 13) |
| 1.3 | 2026-11-05 | Consolidação de pendências: dados fiscais definidos (seção 3), descontos consolidados (seção 10), distinção entre arquivo temporário e documento permanente (seção 9), política OCR reconciliada com D-22 (seção 11), armazenamento permanente definido funcionalmente (seção 12) |
