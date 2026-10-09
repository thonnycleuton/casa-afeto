# Casa Afeto

Sistema de gestão de vendas e operações para Casa Afeto.

Casa Afeto é um negócio focado em cestas de café da manhã e cestas de presente afetivas. Este sistema centraliza as informações essenciais para gerenciar produtos, estoque, cestas, clientes, vendas e pagamentos.

---

## Visão do Produto

O sistema existe para tornar a operação da Casa Afeto mais fácil de gerenciar, sem forçar o negócio a adaptar seus processos a uma complexidade desnecessária de software.

O princípio central é:

> **Construa pouco, valide, aprenda e depois construa a próxima coisa.**

O sistema deve crescer a partir de requisitos reais do negócio, em vez de funcionalidade especulativa.

Para a visão completa do produto, consulte:

`docs/product/vision.md`

---

## Status Atual

A base técnica M0 foi estabelecida. M1 — Produtos e Estoque e M2 — Cestas e Templates de Cesta foram aceitos pelo Product Owner e estão concluídos.

```text
M1 — Produtos e Estoque: COMPLETED
M2 — Cestas e Templates de Cesta: COMPLETED
M3 — Clientes e Datas Importantes: COMPLETED
M2 Implementation Gate: READY FOR IMPLEMENTATION
M2 Implementation: Concluída
M2 Validation/Review: VALIDATED
M2 Aprovação humana: Concluída
M3 Implementation: IMPLEMENTED
M3 Validation/Review: VALIDATED
M3 Aprovação humana: Concluída
```

M3 — Clientes e Datas Importantes foi validado e concluído.

A primeira fase de desenvolvimento é:

**Fase 1 — Operações Centrais**

```text
Produtos
    ↓
Estoque
    ↓
Cestas
    ↓
Clientes
    ↓
Vendas
    ↓
Pagamentos
```

O marco concluído mais recente é:

**M3 — Clientes e Datas Importantes**

M4 — Vendas é o próximo marco planejado.

Consulte:

`docs/product/roadmap.md`

---

## Fase 1

A Fase 1 é dividida em cinco marcos:

| Marco | Escopo                               | Status  |
| ----- | ------------------------------------ | ------- |
| M1    | Produtos e Estoque                  | Concluído (COMPLETED) |
| M2    | Cestas e Templates de Cesta          | Concluído (COMPLETED) |
| M3    | Clientes e Datas Importantes        | Concluído (COMPLETED) |
| M4    | Vendas                               | Planejado |
| M5    | Pagamentos                           | Planejado |

Cada marco deve ser especificado, implementado, testado e validado manualmente antes de avançar para o próximo.

Informações detalhadas da Fase 1:

`docs/milestones/phase-1.md`

---

## Documentação

A documentação do projeto é organizada por responsabilidade.

```text
docs/
│
├── product/
│   ├── vision.md
│   └── roadmap.md
│
├── domain/
│   ├── business-contract.md
│   ├── domain-model.md
│   └── business-rules.md
│
├── architecture/
│   └── decisions/
│
└── milestones/
    ├── phase-1.md
    │
    ├── m1-products-inventory/
    ├── m2-baskets/
    ├── m3-customers/
    ├── m4-sales/
    └── m5-payments/
```

Nem todos os documentos ou diretórios precisam existir desde o início.

Eles devem ser criados quando o conteúdo se tornar necessário.

### Responsabilidades da documentação

**`AGENTS.md`**

Define como os agentes de IA devem trabalhar no projeto, incluindo controle de escopo, tratamento de ambiguidades, testes, decisões de arquitetura e regras anti-sobreengenharia.

**`docs/product/vision.md`**

Define por que o produto existe, seu propósito, princípios e direção de longo prazo.

**`docs/product/roadmap.md`**

Define a evolução planejada do produto e os limites entre funcionalidade atual e futura.

**`docs/domain/business-contract.md`**

Descreve como o negócio da Casa Afeto opera e as premissas de domínio já estabelecidas.

**`docs/domain/domain-model.md`**

Descreve entidades de domínio e suas relações quando o modelo estiver suficientemente definido.

**`docs/domain/business-rules.md`**

Contém regras formais de negócio quando elas estiverem estáveis o suficiente para receber identificadores explícitos e serem mantidas independentemente.

**`docs/milestones/`**

Contém as especificações e materiais de validação para marcos individuais de desenvolvimento.

**`docs/architecture/decisions/`**

Contém Registros de Decisão de Arquitetura (ADRs) para decisões arquiteturais significativas.

---

## Filosofia de Desenvolvimento

O desenvolvimento segue:

```text
Requisito de negócio
        ↓
Especificação
        ↓
Implementação
        ↓
Testes Automatizados
        ↓
Validação Humana
        ↓
Aprovação
        ↓
Próximo Incremento
```

O agente não deve inventar regras de negócio quando os requisitos são ambíguos.

Quando uma decisão muda a forma como o negócio opera, a decisão pertence ao proprietário do projeto.

Quando várias soluções técnicas atendem ao mesmo requisito, a solução mais simples e apropriada deve normalmente ser preferida.

---

## Controle de Escopo

Ideias futuras não se tornam automaticamente requisitos atuais.

Novas ideias devem ser classificadas como:

* **Requisito do marco atual**
* **Requisito de marco futuro**
* **Ideia futura no backlog**
* **Complexidade desnecessária**

O projeto deve evitar implementar funcionalidade apenas porque ela pode se tornar útil no futuro.

Exemplos de capacidades intencionalmente fora do escopo inicial incluem:

* lembretes de data afetiva;
* integração com WhatsApp;
* marketing automatizado;
* gestão de fornecedores;
* gestão de vencimentos;
* reposição automatizada;
* gestão de produção;
* gestão de receitas;
* CRM avançado;
* análises avançadas.

Essas podem ser consideradas mais tarde quando requisitos reais do negócio justificarem.

---

## Regras de Desenvolvimento

Antes de implementar uma funcionalidade, o agente deve:

1. Ler `AGENTS.md`.
2. Identificar o marco atual.
3. Ler a documentação relevante de produto e domínio.
4. Ler a especificação do marco.
5. Identificar regras de negócio e critérios de aceitação.
6. Implementar a menor solução apropriada.
7. Adicionar ou atualizar testes relevantes.
8. Validar a implementação.
9. Reportar qualquer ambiguidade não resolvida em vez de inventar uma regra.

---

## Sequência Atual de Desenvolvimento

```text
M1 — Produtos e Estoque (Products & Inventory)
        ↓
M2 — Cestas e Templates de Cesta (Baskets & Basket Templates)
        ↓
M3 — Clientes (Customers)
        ↓
M4 — Vendas (Sales)
        ↓
M5 — Pagamentos (Payments)
```

A sequência pode mudar se requisitos reais do negócio justificarem.

Qualquer mudança significativa no roadmap deve ser deliberada e documentada.

---

## Próximo Passo

As decisões de negócio fundamentais para **M1 — Produtos e Estoque** foram finalizadas:

* **Política de estoque negativo: RESOLVIDA**
  * **Política:** O estoque físico nunca pode ficar negativo.
  * Operações que produziriam um saldo negativo são rejeitadas.
  * Este invariante é absoluto e também se aplica a operações concorrentes de estoque.
  * Decisão técnica de concorrência documentada em `docs/architecture/decisions/ADR-001-inventory-concurrency.md`.

A validação técnica e a aceitação humana de M1, M2 e M3 foram concluídas; os três marcos estão finalizados (COMPLETED). M4 — Vendas permanece planejado.

---

## Fundação Técnica (M0)

A fundação técnica M0 estabelece a pilha inicial e a infraestrutura de desenvolvimento:
- **Servidor:** Python 3.12 + FastAPI (REST / JSON)
- **Banco de dados:** PostgreSQL 16 + SQLAlchemy 2.x
- **Migrações:** Alembic
- **Validação:** Pydantic
- **Interface web:** Vue 3 + TypeScript + Vite
- **Testes:** pytest (backend) + Vitest (frontend)
- **Conteinerização:** Docker e Docker Compose

### Pré-requisitos
- Docker & Docker Compose (v2+)
- Python 3.12+ (para desenvolvimento local do host)
- Node.js 18+ & npm (para desenvolvimento local do host)

### Primeiros Passos

#### 1. Configuração do Ambiente
Copie `.env.example` para `.env`:
```bash
cp .env.example .env
```

#### 2. Execução com Docker Compose (recomendado)
Inicie todos os serviços (PostgreSQL, servidor FastAPI e interface Vue):
```bash
docker compose up -d
```
- Frontend: [http://localhost:5173](http://localhost:5173)
- Saúde do servidor: [http://localhost:8000/health](http://localhost:8000/health)
- Documentação da API (OpenAPI / Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

#### 3. Execução local (máquina de desenvolvimento)

##### Banco de Dados
Inicie o PostgreSQL usando Docker:
```bash
docker compose up -d db
```

##### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

##### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Executando Testes

#### Testes do Backend (pytest)
```bash
cd backend
source .venv/bin/activate
pytest
```

#### Testes do Frontend (Vitest)
```bash
cd frontend
npm run test
```

### Migrações do Banco de Dados (Alembic)
Aplicar migrações:
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Gerar uma nova migração:
```bash
alembic revision -m "description_of_change"
```

---

## Princípio do Projeto

> **Não construa o que não foi decidido.**
>
> **Quando algo foi decidido, implemente-o fielmente e de forma simples.**
>
> **Quando o negócio ainda não decidiu, pergunte em vez de adivinhar.**
