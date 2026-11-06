# Casa Afeto — Especificação Funcional do Módulo de Compras

**Versão:** 1.2 — Atualização após auditoria técnica de M6/M13

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
- Data da compra.
- Fornecedor, quando disponível.
- CNPJ, quando disponível.
- Número do documento.
- Chave de acesso, quando disponível.
- Imagem original do documento.

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

## 9. Preservação do documento original

- O documento original deve ser preservado após a confirmação da compra.
- Deve permanecer associado à compra e acessível pelo seu detalhamento.
- A exclusão de uma sessão OCR não pode excluir um documento já associado a uma compra.
- O armazenamento técnico (sistema de arquivos ou banco de dados) será definido durante a especificação técnica.

---

## 10. Descontos

Distinguir:

- Descontos individuais dos itens.
- Descontos gerais do documento.

Ambos devem ser preservados como informações, sem distribuição ou aplicação automática aos custos dos produtos.

---

## 11. Histórico

A listagem de compras deve permitir consultar:

- Data.
- Fornecedor, quando disponível.
- Número do documento, quando disponível.
- Quantidade de itens.
- Valor total.
- Situação da compra.

O detalhamento deve apresentar os itens, os dados fiscais disponíveis e a imagem original do documento.

---

## 12. Fora do escopo atual

- Cadastro e gerenciamento de fornecedores.
- Fluxo de aprovação de compras.
- Estornos complexos.
- Histórico detalhado de versões.
- Auditoria avançada de alterações.
- Integração automática com fornecedores.
- Processamento automático de documentos sem revisão humana.

---

## 13. Pendências

As seguintes decisões ainda não foram definidas e requerem aprovação do Product Owner:

- **Definição dos campos fiscais definitivos.** Os campos fiscais listados na Seção 3 são provisórios. A estrutura final depende de decisão de negócio.
- **Formato de persistência dos descontos.** Como os descontos individuais e gerais serão armazenados (campos separados, estrutura JSON, tabela associada) não foi definido.
- **Estratégia técnica de armazenamento permanente dos documentos.** O armazenamento técnico (sistema de arquivos ou banco de dados) mencionado na Seção 9 será definido durante a especificação técnica.
- **Política de retenção e descarte das sessões OCR.** Há divergência entre D-12, D-13 e a especificação funcional sobre quando e como as sessões OCR temporárias devem ser descartadas. Esta decisão requer alinhamento entre as decisões técnicas e a especificação funcional.

---

## 14. Diretriz de implementação

Reutilizar a estrutura de compras e movimentações de estoque já implementada em M6 e o processo de importação OCR de M13.

A compra manual e a compra importada devem convergir para o mesmo processo de confirmação.

Não duplicar regras de negócio nem criar estruturas adicionais sem necessidade funcional comprovada.

**Princípio geral:** o OCR facilita o preenchimento; a confirmação humana registra a compra; o módulo de compras é responsável pela consistência do estoque.

---

## 15. Histórico de versões

| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0 | — | Especificação inicial do módulo de Compras |
| 1.1 | — | Consolidação funcional com decisões aprovadas (status, persistência de rascunhos, conversão de unidades, preservação de documentos, descontos) |
| 1.2 | 2026-11-05 | Atualização após auditoria técnica de M6/M13: nova regra de edição de compras confirmadas (seção 7 substituída), pendências explicitadas (seção 13) |
