# M13 — Melhorias Futuras (Backlog)

**Versão do documento:** 0.1
**Status:** Backlog — ideias registradas, não são requisitos aprovados
**Marco:** M13 — Importação de Documentos de Compra com Gemini
**Data:** 2026-11-03

---

## Objetivo

Registrar melhorias identificadas durante o planejamento do M13 que não fazem parte do escopo atual, mas podem ser consideradas em marcos futuros.

Estas ideias são classificadas como **Categoria C — Ideia para o Backlog Futuro** conforme a política de classificação do roadmap (§18). Elas são registradas sem afetar a arquitetura atual e sem constituir compromissos de implementação.

---

## 1. Distribuição proporcional de descontos

**Problema:** Os documentos de compra podem conter descontos aplicados ao total ou a grupos de itens. O M13 não trata descontos.

**Proposta:** Distribuir o desconto proporcionalmente entre os itens, considerando arredondamentos e conferência dos valores para garantir que a soma dos itens com desconto aplicado corresponda ao total descontado.

**Implicações:**
- Requer decisão sobre como lidar com centavos de arredondamento;
- Requer conferência entre total do documento e soma dos itens após distribuição;
- Pode exigir campo adicional no schema de itens para registrar o desconto aplicado por item.

**Dependências:** Decisão sobre tratamento de descontos (§8.7 da especificação).

---

## 2. Matching aprimorado com sinônimos e histórico

**Problema:** O matching inicial entre itens extraídos e produtos cadastrados pode usar apenas correspondência exata ou parcial de nome, o que pode gerar muitas sugestões incorretas.

**Proposta:**
- Manter um dicionário de sinônimos e nomes comerciais por produto;
- Registrar o histórico de associações confirmadas pelo operador para melhorar as sugestões futuras;
- Usar o histórico para priorizar sugestões já confirmadas anteriormente.

**Implicações:**
- Requer tabela ou mecanismo para armazenar sinônimos e histórico de associações;
- O histórico de associações melhora com o uso — o sistema aprende com as confirmações do operador;
- Não substitui a revisão humana (D-4).

**Dependências:** Decisão sobre critérios de matching (§8.8 da especificação).

---

## 3. Complementação do cadastro de produtos durante a revisão

**Problema:** O cadastro rápido (D-5) cria o produto com campos mínimos. O operador precisa interromper o fluxo de revisão para complementar o cadastro do produto posteriormente.

**Proposta:** Permitir que o operador preencha campos adicionais do produto diretamente durante a revisão da compra, sem interromper o fluxo — por exemplo, unidade base, referência de preço, ou outros campos relevantes.

**Implicações:**
- Requer interface expandida no modal de revisão;
- Os campos adicionais devem seguir as mesmas validações do cadastro normal;
- O produto continua pendente de complementação para campos não preenchidos.

**Dependências:** Regras completas do cadastro rápido (§8.9 da especificação).

---

## 4. Métricas de comparação de modelos Gemini

**Problema:** Diferentes modelos do Gemini têm diferentes capacidades de extração, latência e custo. Sem métricas, é difícil avaliar qual modelo oferece o melhor custo-benefício.

**Proposta:**
- Rastrear precisão da extração por modelo (itens corretos / total de itens);
- Rastrear latência média de processamento por modelo;
- Rastrear custo por documento processado por modelo;
- Permitir comparação entre modelos para decisão informada.

**Implicações:**
- Requer mecanismo de log estruturado para registrar métricas por extração;
- Não afeta o fluxo de importação — é uma capacidade de observabilidade;
- Pode informar a decisão sobre modelo e versão do Gemini (§8.10 da especificação).

**Dependências:** Nenhuma decisão pendente bloqueia a implementação das métricas.

---

## 5. Repetição automática para falhas transitórias

**Problema:** Falhas transitórias na API do Gemini (timeouts, erros de rede) podem causar falha no processamento sem que o conteúdo do documento esteja realmente ilegível.

**Proposta:** Implementar repetição automática limitada para falhas transitórias, com:
- Controle de número máximo de tentativas;
- Backoff exponencial entre tentativas;
- Controle de custos para evitar repetições excessivas;
- Notificação ao operador se todas as tentativas falharem.

**Implicações:**
- Requer política de retry configurável;
- O controle de custos é essencial para evitar gastos excessivos com a API;
- Não substitui o tratamento de falhas gerais (§8.11 da especificação).

**Dependências:** Decisão sobre tratamento de falhas e repetição (§8.11 da especificação).

---

## 6. Estratégia alternativa de duplicidade sem chave de acesso

**Problema:** A D-8 usa a chave de acesso da nota fiscal como identificador único. Se futuramente forem aceitos documentos sem chave de acesso (recibos, notas simplificadas), será necessário um mecanismo alternativo.

**Proposta:** Avaliar estratégias alternativas quando documentos sem chave de acesso forem aceitos:
- Combinação de fornecedor + data + total como chave composta;
- Hash do conteúdo extraído do documento;
- Confirmação manual pelo operador de que o documento não foi previamente importado;
- Registro visual dos documentos já importados para consulta do operador.

**Implicações:**
- Nenhuma estratégia alternativa é tão confiável quanto a chave de acesso;
- A decisão depende de quando e se documentos sem chave de acesso forem aceitos;
- O hash do arquivo não é recomendado como mecanismo principal, pois o mesmo documento pode ser enviado em formatos diferentes.

**Dependências:** Decisão sobre formatos aceitos (§8.3 da especificação) e reavaliação da D-8.

---

## Notas

- Este documento não é um compromisso de implementação.
- As ideias podem ser promovidas para requisitos aprovados quando o negócio demonstrar necessidade concreta.
- Novas ideias identificadas durante a implementação do M13 devem ser adicionadas a este documento, não à especificação.
- A classificação Categoria C significa que a ideia pode ser útil, mas exige validação adicional antes de entrar em desenvolvimento.
