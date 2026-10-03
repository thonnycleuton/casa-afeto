# Casa Afeto — Agent Development Guidelines

**Document version:** 0.1
**Status:** Active
**Last updated:** 2026-10-02

---

## 1. Purpose

This document defines how AI agents must work on the Casa Afeto project.

AI agents are development assistants.

They may analyze requirements, propose solutions, implement code, write tests, inspect existing code, identify problems, and suggest improvements.

However, agents must operate within the business requirements and architectural boundaries defined by the project.

The agent is **not authorized to redefine the product independently**.

The fundamental principle is:

> **The agent implements the approved product. It does not invent the product.**

---

# 2. Source of Truth

When deciding how the system should behave, use the following hierarchy:

```text
1. Explicit user/business decision
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

Higher-level sources take precedence over lower-level assumptions.

The existing code is **not automatically the source of truth for business behavior**.

If existing code conflicts with an approved specification, the specification takes precedence unless the user explicitly decides otherwise.

---

# 3. Human Authority

The human project owner has final authority over:

* business rules;
* product scope;
* architectural decisions;
* milestone priorities;
* acceptance criteria;
* trade-offs;
* whether proposed complexity is justified.

The agent may recommend alternatives.

The agent must not silently choose between materially different business behaviors.

When a decision affects the business domain and the requirement is ambiguous, the agent must stop and ask.

---

# 4. Development Philosophy

The project follows:

> **Build little, validate, learn, then build the next thing.**

Development should proceed incrementally:

```text
Business requirement
        ↓
Specification
        ↓
Agent analysis
        ↓
Implementation
        ↓
Automated tests
        ↓
Human validation
        ↓
Approval
        ↓
Next increment
```

Do not skip directly from an idea to a large implementation.

---

# 5. Current Development Scope

The current roadmap is defined in:

```text
docs/product/roadmap.md
```

The current development phase is:

```text
Phase 1 — Core Operations
```

The current milestone is:

```text
M1 — Products & Inventory
```

The agent must treat the current milestone as the active scope.

Future milestones must not be implemented early unless explicitly authorized.

---

# 6. Scope Control

Before implementing a feature, determine whether it belongs to the current milestone.

Classify newly discovered requirements as:

### A — Current milestone requirement

Necessary for the current milestone.

Proceed after confirming the requirement.

### B — Future milestone requirement

Important, but not necessary now.

Document it and defer it.

### C — Future backlog idea

Potentially useful, but not sufficiently defined or prioritized.

Record it without implementing it.

### D — Unnecessary complexity

Does not solve a meaningful current problem or introduces disproportionate complexity.

Do not implement it.

---

# 7. No Scope Expansion

An agent must not expand the scope of a milestone because:

* a feature would be "nice to have";
* a generic abstraction might be useful later;
* another business system commonly has the feature;
* the agent anticipates a future requirement;
* implementing it now appears easier;
* a framework supports it;
* the agent believes it represents "best practice" without a current requirement.

If a future requirement affects the current design, the agent may explain the potential impact.

It must not implement the future functionality without approval.

---

# 8. Business Ambiguity

When a requirement is ambiguous, do not invent a business rule.

For example, if the requirement says:

> "Remove inventory."

but does not define what should happen when there is insufficient stock, the agent must not arbitrarily decide:

* allow negative stock;
* block the operation;
* create a pending reservation;
* create an automatic purchase;
* warn and continue.

Instead, the agent should identify the ambiguity and request a business decision.

---

# 9. Technical Ambiguity vs Business Ambiguity

Not every uncertainty requires stopping.

### Technical ambiguity

If several technical solutions produce the same approved business behavior, the agent may choose the simplest appropriate implementation.

For example:

> The specification says that products must be searchable.

The agent may choose an appropriate implementation without asking which internal algorithm should be used.

### Business ambiguity

If different solutions change what the business can do or how the business behaves, the agent must ask.

For example:

> What should happen when stock reaches zero?

This is a business decision.

The agent must not make the decision silently.

---

# 10. Simplicity First

Use the simplest architecture that correctly satisfies the current requirements.

Do not introduce abstractions merely because they may become useful later.

Prefer:

```text
Simple solution that works
```

over:

```text
Flexible framework designed for hypothetical future requirements
```

The following should not be introduced without a concrete justification:

* generic repositories;
* generic service frameworks;
* event buses;
* CQRS;
* microservices;
* plugin systems;
* dependency injection frameworks;
* unnecessary factories;
* unnecessary adapters;
* speculative domain abstractions;
* generic workflow engines;
* excessive configuration;
* infrastructure created solely for hypothetical future features.

This is not a prohibition against these techniques.

It is a requirement that their introduction be justified by an actual problem.

---

# 11. Architecture Must Follow Requirements

Do not design the entire future system before implementing the current milestone.

Architecture should emerge from real requirements.

A future concept such as:

```text
Inventory Lots
Production
Recipes
WhatsApp Integration
Affective Dates
```

does not automatically justify implementing abstractions for those concepts today.

When a real requirement arrives, evaluate the existing architecture and evolve it deliberately.

---

# 12. No Speculative Generalization

Avoid creating abstractions such as:

```text
GenericEntity
GenericRepository
GenericBusinessService
GenericWorkflow
GenericManager
GenericHandler
```

unless the current code demonstrates a real need for them.

Duplication is sometimes preferable to premature abstraction.

Before introducing an abstraction, identify:

1. What concrete problem exists?
2. Where does it currently occur?
3. Why is the existing implementation insufficient?
4. What complexity does the abstraction introduce?
5. What simpler alternatives were considered?

---

# 13. Three Similar Things Are Not Automatically an Abstraction

Do not automatically abstract code because several pieces look similar.

Similarity does not necessarily mean identical behavior.

Prefer understanding the domain behavior first.

An abstraction is justified when the shared concept is meaningful and the abstraction reduces complexity rather than merely moving it elsewhere.

---

# 14. Domain Language

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

# 15. Business Rules Must Be Explicit

Business rules should not exist only as hidden conditions inside implementation code.

Examples include:

```text
A sale requires at least one basket.

A sale can be confirmed when at least 50% has been paid.

Inventory is deducted when a sale is confirmed.

A confirmed sale may be modified.

Post-confirmation changes adjust inventory by delta.

A cancelled sale is preserved rather than deleted.
```

When a rule becomes sufficiently stable and important, it should be documented in:

```text
docs/domain/business-rules.md
```

Do not create a formal rule merely because a temporary implementation detail exists.

---

# 16. Specification Before Implementation

Before implementing a milestone, read:

```text
docs/product/vision.md
docs/product/roadmap.md
docs/domain/business-contract.md
docs/milestones/phase-1.md
```

Then read the current milestone specification when it exists.

The implementation should be derived from the specification.

If the specification is incomplete, do not compensate by inventing requirements.

Identify the missing decision.

---

# 17. Specification vs Implementation Problems

When validation fails, first determine whether the problem is:

### A — Specification problem

The expected behavior was wrong, incomplete, or ambiguous.

In this case, update the specification after the business decision is made.

### B — Implementation problem

The specification correctly describes the desired behavior, but the implementation does not satisfy it.

In this case, correct the implementation.

Do not silently modify the specification merely to make an implementation pass.

---

# 18. Tests

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

---

# 19. Test the Business Rules

When a rule is important, tests should make that rule visible.

For example:

```text
Given a sale totaling R$200
When R$100 is recorded as paid
Then the sale can reach the confirmation threshold.
```

The exact testing style depends on the technology stack.

The principle is that the test should make the intended behavior understandable.

---

# 20. Regression Safety

Before modifying existing behavior:

1. understand the existing behavior;
2. identify affected functionality;
3. inspect relevant tests;
4. implement the smallest necessary change;
5. run relevant tests;
6. run the broader test suite when appropriate.

Do not rewrite working code simply because another implementation appears cleaner.

---

# 21. Refactoring Policy

Refactoring is allowed when it improves the current system.

However, refactoring must have a concrete reason.

Examples:

* duplicated logic creates defects;
* a function is difficult to test;
* responsibilities are clearly mixed;
* the current structure prevents the required feature;
* the existing design creates significant maintenance problems.

Avoid refactoring unrelated code merely because the agent is already working nearby.

Keep changes focused.

---

# 22. Agent Must Explain Significant Architectural Changes

If the agent believes the current architecture is insufficient, it must explain:

1. What problem exists?
2. Why does the current architecture not solve it?
3. What change is being proposed?
4. What alternatives were considered?
5. Why is the proposed solution appropriate now?
6. What additional complexity does it introduce?

The agent must not silently introduce major architectural changes.

For significant decisions, create an ADR under:

```text
docs/architecture/decisions/
```

---

# 23. ADR Policy

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

# 24. Database Changes

Database design must follow the approved domain and feature requirements.

Do not create tables or fields solely because they might be useful later.

Before introducing a new persistent concept, identify:

* the business concept it represents;
* why it exists now;
* who uses it;
* what behavior depends on it;
* whether it belongs to the current milestone.

Avoid speculative columns and relationships.

---

# 25. API Design

APIs should represent actual application capabilities.

Do not create generic endpoints simply for theoretical reuse.

Prefer clear, domain-oriented operations.

The API should not expose internal implementation details unnecessarily.

API behavior should be derived from the milestone specification and acceptance criteria.

---

# 26. Frontend Development

The frontend should prioritize operational clarity.

Do not introduce complex state-management architecture unless the actual application requires it.

Prefer simple patterns that are easy to understand and maintain.

The UI should expose relevant business information clearly.

For example, if a product has insufficient stock but can still be selected, the user should be able to understand that situation.

Do not hide important business consequences behind technical abstractions.

---

# 27. Error Handling

Errors should communicate meaningful information to the user and developer.

Do not use broad exception handling simply to prevent visible errors.

An error should not silently convert an invalid business operation into a successful one.

When an operation fails after partially modifying state, the implementation must preserve data consistency.

---

# 28. Data Integrity

Business data should remain internally consistent.

When an operation affects multiple pieces of persistent information, consider whether it must be atomic.

For example, if a confirmed sale causes inventory deduction, the system should not leave the sale confirmed while only partially applying the corresponding inventory changes.

The exact transaction strategy depends on the technology and architecture.

---

# 29. Historical Data

Do not destroy historical business information when a correction can be represented as a new event or adjustment.

Examples:

```text
Original inventory movement
        +
Correction movement
```

rather than:

```text
Delete original movement
        +
Rewrite history
```

Similarly, cancelled sales should remain available for historical reference.

---

# 30. Handling Existing Code

When working on an existing implementation:

1. inspect before changing;
2. understand why the code exists;
3. identify the behavior that must be preserved;
4. compare it with the current specification;
5. change only what is necessary.

Do not assume existing code is correct.

Do not assume existing code is wrong.

Verify.

---

# 31. AI-Assisted Implementation

AI-assisted coding is expected in this project.

The agent may:

* generate code;
* modify code;
* create tests;
* refactor code;
* inspect implementation;
* propose architecture;
* investigate failures.

However, generated code must be treated as code requiring review.

The agent must not assume that generated code is correct merely because:

* it compiles;
* tests pass;
* the implementation is sophisticated;
* a common pattern was used;
* another project uses the same approach.

---

# 32. Avoid Overengineering

The following warning signs should trigger review:

* a simple feature requires many new classes;
* a CRUD operation introduces several abstraction layers;
* a simple rule requires a generic workflow engine;
* a small change requires widespread architectural modifications;
* code is being created for future features that do not yet exist;
* multiple configuration files are introduced without a clear need;
* an agent introduces infrastructure that the current application does not use;
* a simple business rule is represented through unnecessarily complex patterns.

When such a situation occurs, the agent should stop and explain why the complexity is necessary.

---

# 33. Prefer Local Reasoning

When implementing a feature, understand the smallest relevant portion of the system first.

Do not redesign unrelated modules simply because they could theoretically be improved.

A focused change is preferred over a broad rewrite.

---

# 34. Change Size

Prefer small, reviewable changes.

A milestone may contain several implementation steps.

Each step should ideally have a clear purpose.

Avoid large changes that simultaneously:

* introduce new architecture;
* change unrelated modules;
* refactor existing code;
* add future functionality;
* alter business behavior.

When multiple changes are necessary, separate them logically.

---

# 35. Validation

Every milestone must include explicit validation.

The validation process should include:

### Automated validation

Relevant tests and checks.

### Human validation

A realistic business scenario performed by the project owner.

Example:

```text
Create Chocolate
        ↓
Add 20 units
        ↓
Verify balance = 20
        ↓
Adjust -3
        ↓
Verify balance = 17
        ↓
Inspect movement history
```

Passing automated tests is not equivalent to business validation.

---

# 36. Definition of Done

A feature is not considered complete merely because code exists.

The minimum definition of done is:

```text
Requirement understood
        ↓
Specification defined
        ↓
Implementation complete
        ↓
Automated tests pass
        ↓
Relevant checks pass
        ↓
Human validation performed
        ↓
Business behavior approved
```

Only then should the feature be considered complete.

---

# 37. When the Agent Should Stop

The agent should stop and request clarification when:

* a business rule is ambiguous;
* two requirements conflict;
* the implementation would require a significant new architectural decision;
* the requested behavior conflicts with the current specification;
* a change would materially expand the milestone;
* data integrity could be compromised;
* the agent cannot determine the correct business behavior from existing documentation.

Stopping is preferable to inventing a business decision.

---

# 38. When the Agent May Proceed Without Asking

The agent may proceed when:

* the business behavior is explicitly defined;
* the implementation choice is purely technical;
* several technical approaches produce equivalent business behavior;
* the simpler approach is obvious;
* the change is clearly within the current milestone;
* existing project conventions provide sufficient guidance.

In these cases, choose the simplest appropriate implementation.

---

# 39. New Requirements Discovered During Development

When implementation reveals a new requirement, classify it.

Example:

> While implementing inventory, the agent discovers that product expiration dates would be useful.

The agent should not immediately implement expiration.

Instead:

```text
Discovery
   ↓
Document as future requirement
   ↓
Evaluate later
```

If the new requirement is actually necessary for the current business behavior, explain why and request confirmation if the existing specification does not already cover it.

---

# 40. Documentation Maintenance

Documentation should evolve with the system.

When a business decision changes:

* update the appropriate business document;
* update affected specifications;
* update acceptance criteria if necessary;
* update tests;
* update implementation.

Avoid leaving contradictory documentation.

There should be one authoritative location for each type of information.

---

# 41. Documentation Responsibilities

Use each document for its intended purpose.

```text
AGENTS.md
    How agents must work

README.md
    Project entry point

docs/product/vision.md
    Why the product exists

docs/product/roadmap.md
    Where the product is going

docs/domain/business-contract.md
    How the business operates

docs/domain/domain-model.md
    Domain concepts and relationships

docs/domain/business-rules.md
    Formal business rules

docs/milestones/phase-1.md
    Phase 1 sequence and boundaries

docs/milestones/<milestone>/specification.md
    What the milestone must do

docs/milestones/<milestone>/use-cases.md
    How users perform operations

docs/milestones/<milestone>/acceptance-criteria.md
    How correctness is determined

docs/milestones/<milestone>/validation.md
    How the implementation is manually validated

docs/architecture/decisions/
    Significant architectural decisions
```

Do not duplicate the same requirement across several documents unless necessary for context.

---

# 42. Security and Sensitive Data

Do not introduce storage or processing of sensitive information unless the product explicitly requires it.

When dealing with payment proofs or customer information:

* store only what is required;
* avoid unnecessary duplication;
* do not log sensitive information unnecessarily;
* do not expose sensitive information in error messages;
* follow the project's security requirements.

Security decisions that materially affect architecture should be documented.

---

# 43. Performance

Do not optimize prematurely.

Performance work should be based on:

* a measurable problem;
* a realistic workload;
* evidence that the current implementation is insufficient.

Avoid introducing caching, queues, asynchronous processing, indexing strategies, or distributed infrastructure without a concrete need.

Correctness and simplicity take precedence until performance evidence indicates otherwise.

---

# 44. Observability

Logging and monitoring should support meaningful operational and technical diagnosis.

Do not introduce elaborate observability infrastructure for hypothetical scale.

Logs should help answer questions such as:

* What operation failed?
* Where did it fail?
* What business operation was being performed?
* What information is necessary to diagnose the problem?

Do not log sensitive information unnecessarily.

---

# 45. Dependencies

Before adding a dependency, consider:

1. Is it necessary?
2. Does the existing stack already solve the problem?
3. Does it introduce significant maintenance cost?
4. Is the problem sufficiently important to justify it?

Prefer existing project capabilities when they are adequate.

---

# 46. Technology Decisions

Technology choices should be driven by the project requirements.

Do not introduce a technology merely because it is popular or considered modern.

A technology should solve a concrete problem.

When a technology materially affects the architecture, document the decision.

---

# 47. Final Principle

The most important rule for agents working on Casa Afeto is:

> **Do not build what has not been decided.**

The second most important rule is:

> **When something has been decided, implement it faithfully and simply.**

And the third is:

> **When the business has not decided, ask instead of guessing.**

The objective is not to create the most sophisticated software possible.

The objective is to create software that reliably helps Casa Afeto operate its business and can evolve naturally as the business grows.
