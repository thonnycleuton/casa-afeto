# Casa Afeto

Sales and operations management system for Casa Afeto.

Casa Afeto is a business focused on breakfast baskets and affectionate gift baskets. This system centralizes the core information required to manage products, inventory, baskets, customers, sales, and payments.

---

## Product Vision

The system exists to make the Casa Afeto operation easier to manage without forcing the business to adapt its processes to unnecessary software complexity.

The core principle is:

> **Build little, validate, learn, then build the next thing.**

The system should grow from real business requirements rather than speculative functionality.

For the complete product vision, see:

`docs/product/vision.md`

---

## Current Status

The project is currently in the **initial foundation stage**.

The first development phase is:

**Phase 1 — Core Operations**

```text
Products
    ↓
Inventory
    ↓
Baskets
    ↓
Customers
    ↓
Sales
    ↓
Payments
```

The current milestone is:

**M1 — Products & Inventory**

No later milestone should be implemented before its scope is explicitly authorized.

See:

`docs/product/roadmap.md`

---

## Phase 1

Phase 1 is divided into five milestones:

| Milestone | Scope                      | Status  |
| --------- | -------------------------- | ------- |
| M1        | Products & Inventory       | Current |
| M2        | Baskets & Basket Templates | Planned |
| M3        | Customers                  | Planned |
| M4        | Sales                      | Planned |
| M5        | Payments                   | Planned |

Each milestone must be specified, implemented, tested, and manually validated before moving to the next one.

Detailed Phase 1 information:

`docs/milestones/phase-1.md`

---

## Documentation

The project documentation is organized by responsibility.

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

Not all documents or directories need to exist from the beginning.

They should be created when their content becomes necessary.

### Documentation responsibilities

**`AGENTS.md`**

Defines how AI agents must work on the project, including scope control, ambiguity handling, testing, architectural decisions, and anti-overengineering rules.

**`docs/product/vision.md`**

Defines why the product exists, its purpose, principles, and long-term direction.

**`docs/product/roadmap.md`**

Defines the planned evolution of the product and the boundaries between current and future functionality.

**`docs/domain/business-contract.md`**

Describes how the Casa Afeto business operates and the domain assumptions currently established.

**`docs/domain/domain-model.md`**

Describes domain entities and their relationships once the model is sufficiently defined.

**`docs/domain/business-rules.md`**

Contains formalized business rules once they are stable enough to be given explicit identifiers and maintained independently.

**`docs/milestones/`**

Contains the specifications and validation material for individual development milestones.

**`docs/architecture/decisions/`**

Contains Architecture Decision Records for significant architectural decisions.

---

## Development Philosophy

Development follows:

```text
Business Requirement
        ↓
Specification
        ↓
Implementation
        ↓
Automated Tests
        ↓
Human Validation
        ↓
Approval
        ↓
Next Increment
```

The agent should not invent business rules when requirements are ambiguous.

When a decision changes how the business operates, the decision belongs to the project owner.

When several technical solutions satisfy the same requirement, the simplest appropriate solution should normally be preferred.

---

## Scope Control

Future ideas are not automatically current requirements.

New ideas should be classified as:

* **Current milestone requirement**
* **Future milestone requirement**
* **Future backlog idea**
* **Unnecessary complexity**

The project should avoid implementing functionality merely because it may become useful in the future.

Examples of capabilities intentionally outside the initial scope include:

* affective-date reminders;
* WhatsApp integration;
* automated marketing;
* supplier management;
* expiration management;
* automated replenishment;
* production management;
* recipe management;
* advanced CRM;
* advanced analytics.

These may be considered later when real business requirements justify them.

---

## Development Rules

Before implementing a feature, the agent should:

1. Read `AGENTS.md`.
2. Identify the current milestone.
3. Read the relevant product and domain documentation.
4. Read the milestone specification.
5. Identify business rules and acceptance criteria.
6. Implement the smallest appropriate solution.
7. Add or update relevant tests.
8. Validate the implementation.
9. Report any unresolved ambiguity instead of inventing a rule.

---

## Current Development Sequence

```text
M1 — Products & Inventory
        ↓
M2 — Baskets & Basket Templates
        ↓
M3 — Customers
        ↓
M4 — Sales
        ↓
M5 — Payments
```

The sequence may change if real business requirements justify it.

Any significant change to the roadmap should be deliberate and documented.

---

## Current Next Step

The immediate next step is to complete the foundation documentation and finalize the business decisions required for:

**M1 — Products & Inventory**

Before M1 implementation begins, all business behavior that materially affects the milestone must be sufficiently defined.

The first pending business decision is the policy for **negative inventory**.

---

---

## Technical Foundation (M0)

The M0 technical foundation establishes the initial stack and development infrastructure:
- **Backend:** Python 3.12 + FastAPI (REST / JSON)
- **Database:** PostgreSQL 16 + SQLAlchemy 2.x
- **Migrations:** Alembic
- **Validation:** Pydantic
- **Frontend:** Vue 3 + TypeScript + Vite
- **Testing:** pytest (backend) + Vitest (frontend)
- **Containerization:** Docker & Docker Compose

### Prerequisites
- Docker & Docker Compose (v2+)
- Python 3.12+ (for local host development)
- Node.js 18+ & npm (for local host development)

### Getting Started

#### 1. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

#### 2. Running with Docker Compose (Recommended)
Start all services (PostgreSQL, FastAPI Backend, Vue Frontend):
```bash
docker compose up -d
```
- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend Health: [http://localhost:8000/health](http://localhost:8000/health)
- API Docs (OpenAPI / Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

#### 3. Running Locally (Host)

##### Database
Start PostgreSQL using Docker:
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

### Running Tests

#### Backend Tests (pytest)
```bash
cd backend
source .venv/bin/activate
pytest
```

#### Frontend Tests (Vitest)
```bash
cd frontend
npm run test
```

### Database Migrations (Alembic)
Apply migrations:
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Generate a new migration:
```bash
alembic revision -m "description_of_change"
```

---

## Project Principle

> **Do not build what has not been decided.**
>
> **When something has been decided, implement it faithfully and simply.**
>
> **When the business has not decided, ask instead of guessing.**

