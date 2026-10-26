# Casa Afeto — Agent & Developer Protocol

**Document version:** 0.4
**Status:** Active
**Last updated:** 2026-10-25

**Changes in 0.4:** Added frontend guardrails: mandatory `[Frontend]` tags in acceptance criteria, frontend section requirement in specs, updated Definition of Done, and `validate_spec_casa.py` frontend detection.

**Changes in 0.3:** Added TLC-Spec-Driven validation components: deterministic gates scripts, Test Coverage Matrix, Test Adequacy Review, Discrimination Sensor, and Lessons Layer.

---

## Purpose

This document is the **permanent operational manual** for AI agents and human developers working on Casa Afeto.

It defines **how to work** on the project.

The other documents define **what the project must do**.

Any agent or developer must be able to work correctly on this project using only this document and the repository — without access to previous conversations.

The fundamental principle is:

> **The agent implements the approved product. It does not invent the product.**

---

## Table of Contents

1. [Fundamental Rule](#1-fundamental-rule)
2. [Source of Truth](#2-source-of-truth)
3. [Document Responsibilities](#3-document-responsibilities)
4. [Code vs Documentation](#4-code-vs-documentation)
5. [Change Classification](#5-change-classification)
6. [Handling Ambiguity](#6-handling-ambiguity)
7. [Before Implementing](#7-before-implementing)
8. [Scope Control](#8-scope-control)
9. [Parallel Work](#9-parallel-work)
10. [Documentation as Permanent Memory](#10-documentation-as-permanent-memory)
11. [Traceability](#11-traceability)
12. [Acceptance Criteria Format](#12-acceptance-criteria-format)
13. [Tests](#13-tests)
14. [Validation](#14-validation)
15. [TLC Validation Components](#15-tlc-validation-components)
16. [Milestones](#16-milestones)
17. [Agent Final Report](#17-agent-final-report)
18. [Product Owner Authority](#18-product-owner-authority)
19. [Technical Principles](#19-technical-principles)
20. [Final Principles](#20-final-principles)

---

# 1. Fundamental Rule

Before modifying any code, documentation, or configuration file:

1. Read `AGENTS.md`.
2. Identify which documents are relevant to the task.
3. Inspect the existing implementation.
4. Check existing tests.
5. Check the current Git state (`git status`, `git diff`).
6. Do not invent business rules.
7. Do not assume that information provided by a prompt is correct if it can be verified in the repository.

**The repository is the source of truth. The conversation is not.**

---

# 2. Source of Truth

When deciding how the system should behave, use the following hierarchy:

```text
1. Explicit product owner / business decision
        ↓
2. Current milestone specification
        ↓
3. Business contract
        ↓
4. Product vision
        ↓
5. Product roadmap
        ↓
6. Existing implementation
        ↓
7. Agent assumptions
```

Higher-level sources take precedence over lower-level ones.

The existing code is **not automatically the source of truth for business behavior**.

If existing code conflicts with an approved specification, the specification takes precedence unless the product owner explicitly decides otherwise.

---

# 3. Document Responsibilities

Each document area has a defined responsibility. Do not duplicate content across areas unnecessarily.

### Product

```text
docs/product/
```

Responsibility:

* product vision and purpose;
* product objectives;
* roadmap and milestone sequence;
* macro implementation order.

Files:

```text
docs/product/vision.md       — Why the product exists
docs/product/roadmap.md      — Where the product is going
```

---

### Domain and Business Rules

```text
docs/domain/
```

Responsibility:

* business rules and functional decisions;
* business contracts;
* domain concepts and terminology;
* domain model.

Files:

```text
docs/domain/business-contract.md  — How the business operates
docs/domain/business-rules.md     — Formal business rules (when stable enough)
docs/domain/domain-model.md       — Domain concepts and relationships (if it exists)
```

If a file does not yet exist, do not create it just to fill the gap — only when there is real content to place there.

---

### Milestones

```text
docs/milestones/
```

Responsibility:

* detailed scope of each milestone;
* expected behavior for that milestone.

Structure:

```text
docs/milestones/phase-1.md                              — Phase 1 sequence and boundaries
docs/milestones/<milestone>/specification.md            — What the milestone must do
docs/milestones/<milestone>/use-cases.md                — How users perform operations
docs/milestones/<milestone>/acceptance-criteria.md      — How correctness is determined
docs/milestones/<milestone>/validation.md               — How the implementation is manually validated
```

Currently active milestone:

```text
docs/milestones/m1-products-inventory/
```

---

### Architecture

```text
docs/architecture/
```

Responsibility:

* architectural decisions;
* technical foundations;
* ADRs;
* architectural constraints.

Files:

```text
docs/architecture/technical-foundation.md  — Technical foundations and constraints
docs/architecture/decisions/               — Architecture Decision Records (ADRs)
```

---

### Design

```text
docs/design/
```

Responsibility:

* design system;
* visual patterns;
* UI components and principles;
* visual experience decisions.

Files:

```text
docs/design/design-system.md  — Design system and visual principles
```

---

### Code

The code implements documented decisions.

The code must be inspected before any change.

Do not assume existing code is correct. Do not assume it is wrong. Verify.

---

### Tests

Tests represent and protect the expected behavior of the system.

They do not replace business documentation, but are a fundamental part of implementation validation.

---

# 4. Code vs Documentation

> Code explains **how** the system works.
> Documentation preserves important decisions about **why** it works that way.

Do not create documentation for every trivial change.

Document when a decision has lasting consequences for the business or architecture.

---

# 5. Change Classification

Classify every change before executing it. The classification determines the required steps.

---

## 5.1 Trivial Technical Change

Examples:

* typo correction;
* name change without semantic difference;
* refactoring without behavior change;
* CSS adjustment;
* clearly equivalent internal improvement;
* obvious technical bug fix that does not alter any business rule.

May normally be executed directly.

Still required:

* keep tests passing;
* keep scope controlled;
* do not silently introduce new business decisions.

---

## 5.2 Functional Change

Changes that modify the observable behavior of the system.

Examples:

* new field;
* new endpoint;
* new validation;
* flow change;
* behavior change in an existing feature.

Required steps:

1. identify affected tests;
2. update or add tests;
3. check whether the milestone specification needs updating;
4. check acceptance criteria;
5. check validation;
6. update relevant documentation when officially expected behavior has changed.

---

## 5.3 Business Change

Any change that involves a business rule or business decision.

Examples:

* changing when a sale is considered confirmed;
* changing an inventory rule;
* changing cancellation behavior;
* changing basket composition rules;
* adding a new commercial rule.

Required steps:

1. do not assume the decision — stop and ask if not defined;
2. identify the affected business document;
3. update the corresponding documentation;
4. update specification / use cases / acceptance criteria / validation as applicable;
5. update tests;
6. only then implement the change.

If the rule is not defined:

```text
OPEN QUESTION — REQUIRES PRODUCT OWNER
```

Do not invent a response.

---

## 5.4 Architectural Change

Changes that significantly affect the technical structure of the system.

Examples:

* stack change;
* architectural pattern change;
* introduction of significant infrastructure;
* persistence strategy change;
* new concurrency mechanism;
* integration change;
* adoption of a new structural framework.

Required steps:

1. identify impact;
2. update `docs/architecture/technical-foundation.md` when applicable;
3. create or update an ADR in `docs/architecture/decisions/`;
4. record alternatives considered when relevant;
5. only then implement.

The agent must explain to the product owner before proceeding with significant architectural changes:

1. What problem exists?
2. Why does the current architecture not solve it?
3. What change is proposed?
4. What alternatives were considered?
5. Why is the proposed solution appropriate now?
6. What additional complexity does it introduce?

---

# 6. Handling Ambiguity

Never invent business rules.

### Technical ambiguity

If several technical solutions produce the same approved business behavior, the agent may choose the simplest appropriate implementation without asking.

### Business ambiguity

If different solutions change what the business can do or how it behaves, the agent must stop.

When a doubt could affect:

* user behavior;
* commercial rules;
* persistence;
* business flow;
* API contract;
* expected behavior;

report:

```text
OPEN QUESTION — REQUIRES PRODUCT OWNER
```

The agent may present technical options or consequences, but must not silently choose a business rule.

---

# 7. Before Implementing

Every agent must:

1. Read `AGENTS.md`.
2. Read relevant documentation.
3. Identify the related milestone.
4. Read available specification / use cases / acceptance criteria / validation.
5. Inspect existing code.
6. Inspect existing tests.
7. Run relevant tests before the change, when possible.
8. Check `git status` and local changes.
9. Confirm the task scope.

Do not assume the project is in a given state simply because the prompt states it.

---

# 8. Scope Control

Work only within the requested scope.

Do not:

* add features "while at it";
* create premature abstractions;
* create internal frameworks without need;
* introduce architectural patterns that were not requested;
* modify other system areas without necessity;
* silently expand the milestone.

Avoid overengineering.

A simple solution that satisfies the requirement is preferred over a more complex architecture without proven need.

### Requirement Classification

Before implementing a feature, determine whether it belongs to the current milestone:

| Class | Definition | Action |
|-------|-----------|--------|
| **A** | Current milestone requirement | Proceed after confirming |
| **B** | Future milestone requirement | Document and defer |
| **C** | Future backlog idea | Record without implementing |
| **D** | Unnecessary complexity | Do not implement |

---

# 9. Parallel Work

Different agents or developers may work on the project simultaneously.

Each must:

* follow `AGENTS.md`;
* consult documentation;
* inspect current state;
* limit their own scope;
* avoid overwriting others' changes;
* validate their own changes.

**The real state of the repository always takes precedence over the context of a previous conversation.**

Before changing something:

* check `git status`;
* check `git diff`;
* inspect the current code;
* check current documentation;
* check current tests.

If an existing implementation diverges from the documentation:

1. do not automatically correct assuming documentation is right;
2. identify the divergence;
3. determine whether it is incorrect implementation or outdated documentation;
4. when a business decision is involved, ask the product owner.

No agent should assume exclusive ownership of the repository.

---

# 10. Documentation as Permanent Memory

Prompts are temporary instructions.

Do not use prompts as a permanent source of project decisions.

If a decision is important for the future of the project, record it in the appropriate document:

```text
Business decision
→ docs/domain/

Product decision
→ docs/product/

Milestone behavior
→ docs/milestones/

Architectural decision
→ docs/architecture/

Visual / design decision
→ docs/design/
```

The project must remain comprehensible even if:

* another developer joins tomorrow;
* another agent is used;
* this conversation is not available;
* an implementation was changed manually;
* a decision was made months ago.

Permanent knowledge must be in the repository.

---

# 11. Traceability

When applicable, maintain the chain:

```text
Business Decision
        ↓
Specification
        ↓
Use Cases
        ↓
Acceptance Criteria
        ↓
Validation
        ↓
Implementation
        ↓
Tests
```

Do not unnecessarily duplicate the same rule across multiple documents.

Each document must maintain its responsibility.

When a business decision changes, update:

* the appropriate business document;
* affected specifications;
* acceptance criteria if necessary;
* validation;
* tests;
* implementation.

Avoid leaving contradictory documentation.

There should be one authoritative location for each type of information.

---

# 12. Acceptance Criteria Format

Every `acceptance-criteria.md` must follow these rules so the agent and validation gates can distinguish backend work from frontend work.

### 12.1 Tags on Every AC

Each acceptance criterion heading must include a tag that indicates which layer it affects:

- `[Backend]` — only backend code (models, services, APIs, migrations)
- `[Frontend]` — only frontend code (types, components, templates, styles)
- `[Backend + Frontend]` — both layers are affected

**Example:**
```markdown
### AC-M8-001 [Backend] — Vencimento opcional no lote
### AC-M8-015 [Backend + Frontend] — Vencimento na entrada manual
### AC-M8-017 [Frontend] — Badge visual no modal de estoque
```

**Why:** Without tags, the validation gate cannot detect that a `[Frontend]` AC has no corresponding implementation. The agent may close the milestone thinking "all ACs are covered" while the frontend ACs were never implemented.

### 12.2 Mandatory Frontend Section

If a milestone has any `[Frontend]` or `[Backend + Frontend]` ACs, the `acceptance-criteria.md` must contain a dedicated section:

```markdown
## Frontend
```

All `[Frontend]` ACs must be grouped under this section. `[Backend + Frontend]` ACs may appear in either the backend section or the frontend section, but must appear in at least one.

**Why:** Mixing frontend and backend ACs in the same section makes it easy to skip the frontend ACs when the agent focuses on backend implementation.

### 12.3 Validation Gate

The `validate_spec_casa.py` script checks:

1. If any AC contains `[Frontend]` or `[Backend + Frontend]`, there must be a `## Frontend` section in the acceptance criteria file.
2. If a `## Frontend` section exists, it must contain at least one AC heading.
3. ACs without tags receive a warning (future versions may make tags mandatory).

A missing frontend section when frontend ACs exist produces an **ERROR** that blocks milestone closure.

### 12.4 Backward Compatibility

Existing milestones (M1–M8) are exempt from the tag requirement until they are revisited. The tag requirement applies to new milestones created after this rule is adopted.

---

# 13. Tests

Tests are part of the implementation, not an optional final step.

For business behavior, prefer tests that verify observable behavior.

Tests should provide confidence that:

* business rules are respected;
* important edge cases are handled;
* regressions are detected;
* changes do not silently alter existing behavior.

When appropriate, use:

* unit tests;
* integration tests;
* API tests;
* frontend tests;
* end-to-end tests.

The appropriate level depends on the actual architecture and feature.

Do not create large numbers of tests that merely test framework behavior or trivial getters/setters.

### On every functional change, the agent must:

* add tests when necessary;
* update affected tests;
* run relevant tests;
* run the full suite when appropriate;
* not remove or weaken tests just to make the implementation pass.

### Test Coverage Matrix

For each new milestone, generate a Test Coverage Matrix that maps every Acceptance Criterion to a specific test with an exact `file:line` reference. See [Section 15.2](#152-test-coverage-matrix) for format.

### Test Adequacy Review

After each task, execute the 4 checks defined in [Section 15.3](#153-test-adequacy-review). The evidence-or-zero rule applies: each covered AC must cite the exact `file:line` of its test assertion.

### Test the Business Rules

When a rule is important, tests should make it visible.

Example:

```text
Given a sale totaling R$200
When R$100 is recorded as paid
Then the sale has reached the confirmation threshold.
```

---

# 14. Validation

Before declaring a task complete:

1. run relevant tests;
2. check lint / type checks / build when applicable;
3. check integration when applicable;
4. verify that no documented rule was broken;
5. check for unexpected changes in Git;
6. confirm that the requested scope was respected.

Never declare a task "complete" without indicating what was actually validated.

### Definition of Done

A feature is not considered complete merely because code exists.

Minimum definition of done:

```text
Requirement understood
        ↓
Specification defined
        ↓
Implementation complete
  ├─ Backend: endpoints, models, services, tests
  └─ Frontend: types, components, fields, visual elements
        ↓
Automated tests pass
        ↓
Relevant checks pass
  ├─ Backend: pytest suite, lint
  └─ Frontend: vue-tsc --noEmit, visual verification
        ↓
Human validation performed
        ↓
Business behavior approved
```

**Frontend is not optional.** If the milestone specification describes any user-facing behavior — new fields, new sections, new visual elements, new interactions — the frontend implementation is part of "Implementation complete." A milestone cannot be closed with pending frontend ACs.

Only then should the feature be considered complete.

Passing automated tests is not equivalent to business validation.

---

# 16. Milestones

The roadmap defines the macro sequence of the product.

A milestone should only begin implementation when all of the following are in place:

1. defined scope;
2. relevant business rules defined;
3. specification available;
4. use cases available when necessary;
5. acceptance criteria defined;
6. validation strategy defined;
7. technical dependencies satisfied;
8. blocking questions resolved;
9. necessary foundations available.

Do not start a new milestone simply because the previous one had its implementation completed.

### Milestone Lifecycle

Distinguish clearly:

```text
Implementation       — code being written
Visual Refinement    — UI/UX adjustments after functional implementation
Validation           — automated and manual testing phase
Human Acceptance     — product owner validates business behavior
Completed            — approved and ready for next milestone
```

The current development phase and milestone are defined in:

```text
docs/product/roadmap.md
docs/milestones/phase-1.md
```

Read those documents to determine current scope before beginning any work.

### Milestone Completion

When a milestone reaches the **Completed** stage, the agent must commit all changes to Git before submitting the final report.

**Required steps:**

1. Run relevant tests and confirm they pass.
2. Stage all changes: `git add .`.
3. Commit with a Conventional Commits message:
   ```
   feat: complete <milestone-id> — <short description>
   
   Co-authored-by: Junie <junie@jetbrains.com>
   ```
4. Verify the commit using `git log -1` and `git status`.
5. Push to origin if the remote is available: `git push origin main`.

**Why:** Without commits, work done in a session is lost when the session ends. The repository is the source of truth, and uncommitted changes are not part of the repository.

**Commit message format:** Use Conventional Commits (see `scripts/tlc/check_commit.py`). The message should be in Portuguese if the milestone documentation is in Portuguese.

---

# 17. Agent Final Report

When completing a task, the agent must report:

### Changes

* files modified;
* main changes made.

### Documentation

* documents updated;
* new documents created;
* or state that no documentation was necessary.

### Tests

* tests executed;
* result.

### Validation

* additional validations performed.

### Open Questions

* pending questions, if any.

### Scope

* confirm whether any out-of-scope changes were made.

When a step could not be validated, state explicitly:

```text
NOT VALIDATED
```

and explain why.

---

# 18. Product Owner Authority

The product owner has final authority over:

* business rules;
* product scope;
* architectural decisions;
* milestone priorities;
* acceptance criteria;
* trade-offs;
* whether proposed complexity is justified.

The agent may:

* analyze;
* propose alternatives;
* explain consequences;
* identify inconsistencies;
* suggest technical solutions.

The agent must not:

* invent commercial rules;
* silently choose between business alternatives;
* change requirements on its own.

---

# 19. Technical Principles

### Simplicity First

Use the simplest architecture that correctly satisfies the current requirements.

Do not introduce abstractions merely because they may become useful later.

The following should not be introduced without concrete justification:

* generic repositories;
* generic service frameworks;
* event buses;
* CQRS;
* microservices;
* plugin systems;
* dependency injection frameworks;
* unnecessary factories or adapters;
* speculative domain abstractions;
* generic workflow engines;
* excessive configuration;
* infrastructure created solely for hypothetical future features.

This is not a prohibition against these techniques. It is a requirement that their introduction be justified by an actual problem.

---

### Architecture Must Follow Requirements

Do not design the entire future system before implementing the current milestone.

Architecture should emerge from real requirements.

---

### No Speculative Generalization

Avoid creating abstractions like `GenericEntity`, `GenericRepository`, `GenericWorkflow` unless the current code demonstrates a real need.

Duplication is sometimes preferable to premature abstraction.

Before introducing an abstraction, identify:

1. What concrete problem exists?
2. Where does it currently occur?
3. Why is the existing implementation insufficient?
4. What complexity does the abstraction introduce?
5. What simpler alternatives were considered?

---

### Domain Language

Use the language of the Casa Afeto business.

Core terms currently include:

* Product
* Inventory
* Inventory Movement
* Basket
* Basket Template
* Basket Item
* Customer
* Sale
* Payment

Do not introduce alternative terminology without a reason.

If the business uses one term and the code uses another, document the mapping.

---

### Business Rules Must Be Explicit

Business rules should not exist only as hidden conditions inside implementation code.

When a rule becomes sufficiently stable and important, document it in:

```text
docs/domain/business-rules.md
```

Do not create a formal rule merely because a temporary implementation detail exists.

---

### Handling Existing Code

When working on an existing implementation:

1. inspect before changing;
2. understand why the code exists;
3. identify the behavior that must be preserved;
4. compare it with the current specification;
5. change only what is necessary.

Do not assume existing code is correct. Do not assume it is wrong. Verify.

---

### ADR Policy

Architecture Decision Records should be created only for meaningful architectural decisions.

Examples:

* choosing a persistence strategy;
* introducing a significant integration pattern;
* changing application boundaries;
* introducing a technology that affects the architecture;
* choosing between materially different architectural approaches.

Do not create ADRs for every small coding decision.

The purpose of an ADR is to preserve the reasoning behind a significant decision.

---

### Regression Safety

Before modifying existing behavior:

1. understand the existing behavior;
2. identify affected functionality;
3. inspect relevant tests;
4. implement the smallest necessary change;
5. run relevant tests;
6. run the broader test suite when appropriate.

Do not rewrite working code simply because another implementation appears cleaner.

---

### Refactoring Policy

Refactoring is allowed when it improves the current system with a concrete reason.

Examples of justified reasons:

* duplicated logic creates defects;
* a function is difficult to test;
* responsibilities are clearly mixed;
* the current structure prevents the required feature;
* the existing design creates significant maintenance problems.

Avoid refactoring unrelated code merely because the agent is already working nearby.

---

### Database Changes

Do not create tables or fields solely because they might be useful later.

Before introducing a new persistent concept, identify:

* the business concept it represents;
* why it exists now;
* who uses it;
* what behavior depends on it;
* whether it belongs to the current milestone.

---

### API Design

APIs should represent actual application capabilities.

Do not create generic endpoints simply for theoretical reuse.

Prefer clear, domain-oriented operations.

API behavior should be derived from the milestone specification and acceptance criteria.

---

### Frontend Development

The frontend should prioritize operational clarity.

Do not introduce complex state-management architecture unless the actual application requires it.

The UI should expose relevant business information clearly.

Do not hide important business consequences behind technical abstractions.

---

### Error Handling

Errors should communicate meaningful information to the user and developer.

Do not use broad exception handling simply to prevent visible errors.

An error should not silently convert an invalid business operation into a successful one.

When an operation fails after partially modifying state, the implementation must preserve data consistency.

---

### Data Integrity

Business data should remain internally consistent.

When an operation affects multiple pieces of persistent information, consider whether it must be atomic.

---

### Historical Data

Do not destroy historical business information when a correction can be represented as a new event or adjustment.

Example:

```text
Original inventory movement
        +
Correction movement
```

Rather than:

```text
Delete original movement
        +
Rewrite history
```

---

### Security and Sensitive Data

Do not introduce storage or processing of sensitive information unless the product explicitly requires it.

When dealing with payment proofs or customer information:

* store only what is required;
* avoid unnecessary duplication;
* do not log sensitive information unnecessarily;
* do not expose sensitive information in error messages.

Security decisions that materially affect architecture should be documented.

---

### Performance

Do not optimize prematurely.

Performance work should be based on a measurable problem and evidence that the current implementation is insufficient.

Correctness and simplicity take precedence until performance evidence indicates otherwise.

---

### Dependencies

Before adding a dependency, consider:

1. Is it necessary?
2. Does the existing stack already solve the problem?
3. Does it introduce significant maintenance cost?
4. Is the problem sufficiently important to justify it?

---

### AI-Assisted Implementation

AI-assisted coding is expected in this project.

Generated code must be treated as code requiring review.

The agent must not assume that generated code is correct merely because it compiles, tests pass, or a common pattern was used.

---

# 15. TLC Validation Components

This section describes the deterministic validation tools adopted from [TLC-Spec-Driven](https://github.com/tech-leads-club/agent-skills) and integrated into the Casa Afeto workflow.

Scripts are located in `scripts/tlc/`. See `scripts/tlc/README.md` for usage details.

---

## 15.1 Deterministic Gates

The agent must execute validation scripts at key points instead of relying on memory to remember checks.

| Script | When to run | Purpose |
|--------|-------------|--------- |
| `validate_spec_casa.py` | Before confirming a spec with the Product Owner | Validates Casa Afeto spec format: required sections, testable ACs, pending decisions |
| `validate_tasks.py` | Before starting milestone implementation | Validates task granularity and dependency consistency |
| `check_commit.py` | On every commit | Validates Conventional Commits format |
| `validate_state.py` | At the end of a milestone | Validates the feature is truly complete |

A script failure (non-zero exit code) means the gate is not passed. The agent must fix the issue before proceeding.

---

## 15.2 Test Coverage Matrix

For each new milestone, the agent must generate a Test Coverage Matrix before implementation.

Format (add to `acceptance-criteria.md` or a separate file):

```markdown
## Test Coverage Matrix

| AC ID | Test Name | File | Line | Status |
|-------|-----------|------|------|--------|
| AC-M5-001 | test_payment_linked_to_sale | tests/test_payments.py | 42 | ✓ |
| AC-M5-002 | test_payment_value_positive | tests/test_payments.py | 58 | ✗ |
```

Each Acceptance Criterion must be mapped to a specific test with an exact `file:line` reference. ACs without a test are marked `✗` and must be covered before closing the milestone.

---

## 15.3 Test Adequacy Review

After each task, the agent must execute 4 quality checks on the tests:

**Check A — Sufficient coverage:** Each AC is mapped to `file:line` + assertion expression.

**Check B — No shallow litmus:** Rejects trivial tests that only verify getters/setters.

**Check C — Necessity:** Each test is mapped to a real requirement.

**Check D — Compliance:** Tests follow the project's guidelines.

The **evidence-or-zero rule** requires that each covered criterion cites an exact `file:line`. Without evidence, the AC is not covered.

---

## 15.4 Discrimination Sensor

For critical features (payments, inventory, auth), the agent must run mutation testing after writing tests to verify they actually detect regressions.

```bash
python3 scripts/tlc/discrimination_sensor.py backend/app/payments/ \
  --test-cmd "cd backend && python -m pytest tests/test_payments.py -x"
```

The sensor injects intentional faults (inverting conditions, changing return values, swapping operators) and checks if tests fail. If mutations survive, the tests are weak and must be strengthened.

**Exit codes:**
- `0` — All mutations detected (tests are adequate)
- `1` — Some mutations survived (tests are weak)
- `2` — Error

---

## 15.5 Lessons Layer

The project learns from past validation failures. Lessons are stored in `scripts/tlc/lessons.json` and managed by `scripts/tlc/lessons.py`.

**Workflow:**

1. After each validation failure, record a lesson:
   ```bash
   python3 scripts/tlc/lessons.py add \
     --feature "M5-Payments" \
     --signal surviving_mutant \
     --source "backend/app/payments/service.py:42" \
     --text "Concurrency tests require explicit locks" \
     --scope "M5-Payments"
   ```
2. Before starting a new milestone, load confirmed lessons:
   ```bash
   python3 scripts/tlc/lessons.py list --status confirmed
   ```
3. The agent must check relevant lessons before implementing features in the same scope.

**Lesson statuses:**
- `candidate` — New lesson, needs confirmation
- `confirmed` — Confirmed by multiple occurrences
- `quarantined` — In doubt, may be removed

---

# 20. Final Principles

> **Do not build what has not been decided.**

> **When something has been decided, implement it faithfully and simply.**

> **When the business has not decided, ask instead of guessing.**

The objective is not to create the most sophisticated software possible.

The objective is to create software that reliably helps Casa Afeto operate its business and can evolve naturally as the business grows.
