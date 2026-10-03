# Casa Afeto — Phase 1

**Document version:** 0.1
**Status:** Active
**Phase:** 1 — Core Operations

---

## 1. Purpose

Phase 1 establishes the operational foundation of the Casa Afeto Sales Management System.

The objective is to implement the minimum set of capabilities required to manage:

* products;
* inventory;
* basket templates;
* baskets;
* customers;
* sales;
* payments.

The phase must result in a coherent operational flow from product registration through sale confirmation and inventory deduction.

Phase 1 follows the project's core development principle:

> Build little, validate, learn, then build the next thing.

Each milestone must be implemented, tested, and manually validated before the next milestone begins.

---

## 2. Phase 1 Development Sequence

Phase 1 is divided into five milestones:

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

The order is intentional.

Each milestone should establish the minimum foundation required by the next one without implementing functionality that belongs to later milestones.

---

# 3. Milestone M1 — Products & Inventory

## Objective

Establish the basic product and inventory foundation.

## Scope

M1 includes:

* product creation;
* product editing;
* product activation/deactivation;
* product listing;
* product search;
* base inventory unit;
* manual inventory entry;
* inventory adjustments;
* inventory balance;
* inventory movement history;
* basic inventory availability information.

## Expected capabilities

The user must be able to:

1. Create a product.
2. Define its base inventory unit.
3. Edit its basic information.
4. Activate or deactivate the product.
5. Add inventory manually.
6. Adjust inventory.
7. View the current balance.
8. View inventory movement history.
9. Identify whether a product currently has available stock.

## Important business behavior

Inventory must be represented through movements rather than relying exclusively on a mutable stock value.

The system must preserve the history of inventory changes.

An inventory correction must not erase or rewrite previous movements.

A product with insufficient stock may still be selected for a future basket, provided that the lack of stock is clearly visible to the user.

## Explicitly out of scope

M1 does not implement:

* purchases;
* suppliers;
* purchase items;
* inventory lots;
* expiration dates;
* FEFO/lot selection;
* automatic replenishment;
* loss management;
* production;
* recipes;
* reserved inventory;
* sales-related inventory deduction.

These capabilities may be introduced in later phases or milestones.

## M1 validation example

A basic validation flow should demonstrate:

```text
Create Chocolate
    ↓
Add 20 units
    ↓
Balance = 20
    ↓
Adjust -3
    ↓
Balance = 17
    ↓
Review movement history
    ↓
Deactivate product
    ↓
Verify inactive product cannot be selected for new operations
```

## Dependency

None.

M1 is the foundation of Phase 1.

---

# 4. Milestone M2 — Baskets & Basket Templates

## Objective

Allow Casa Afeto to define reusable basket compositions and create concrete baskets from them.

## Scope

M2 includes:

* basket template creation;
* basket template editing;
* basket template activation/deactivation;
* template composition;
* product quantities in templates;
* basket creation from a template;
* basket creation without a template;
* basket customization;
* adding products;
* removing products;
* substituting products;
* multiple quantities of the same product;
* basket composition persistence;
* basket cost calculation;
* suggested basket price calculation;
* manual final price.

## Expected capabilities

The user must be able to:

1. Create a basket template.
2. Add products and quantities to the template.
3. Create a concrete basket from the template.
4. Create a basket without a template.
5. Modify the concrete basket.
6. Add or remove products.
7. Substitute products.
8. Use multiple units of the same product.
9. View the basket cost.
10. View a suggested selling price.
11. Define the final selling price manually.

## Important business behavior

A concrete basket must be independent from future changes to its template.

For example:

```text
Template A
    Chocolate × 2
    Juice × 1

        ↓ create basket

Basket X
    Chocolate × 2
    Juice × 1

        ↓ later change template

Template A
    Chocolate × 1
    Juice × 2
```

Basket X must continue to contain:

```text
Chocolate × 2
Juice × 1
```

The template change must not modify the existing basket.

A basket may also be customized after creation.

A product with insufficient inventory may still be added to the basket, but the user must receive a clear stock warning.

## Pricing behavior

The system should calculate:

```text
Basket Cost
    ↓
Suggested Price
    ↓
Final Selling Price
```

The current business practice of approximately 2× cost is treated as a pricing suggestion, not as an enforced rule.

The final selling price remains under user control.

## Explicitly out of scope

M2 does not implement:

* sales;
* customers;
* payments;
* stock deduction;
* purchase management;
* lot selection;
* expiration management;
* recipient management as a separate entity;
* discounts or promotions.

## Dependency

M1.

---

# 5. Milestone M3 — Customers

## Objective

Establish the basic customer information required to associate sales with customers.

## Scope

M3 includes:

* customer creation;
* customer editing;
* customer activation/deactivation;
* customer listing;
* customer search.

## Expected capabilities

The user must be able to:

1. Create a customer.
2. Edit customer information.
3. Search for customers.
4. Identify an active customer.
5. Deactivate a customer.

## Business model

A customer represents the person who makes the purchase.

The recipient of a basket does not need to be represented as a separate customer/person entity during Phase 1.

Recipient information will be associated with the basket/delivery context when sales are implemented.

## Explicitly out of scope

M3 does not implement:

* CRM;
* customer segmentation;
* customer campaigns;
* affective dates;
* birthday management;
* wedding anniversary management;
* automated reminders;
* recipient entities;
* communication integrations;
* WhatsApp integration.

These are future capabilities.

## Dependency

M2.

---

# 6. Milestone M4 — Sales

## Objective

Introduce the sale as the operational transaction connecting customers and baskets.

## Scope

M4 includes:

* sale creation;
* customer selection;
* one or more baskets per sale;
* basket selection;
* basket composition visualization;
* basket composition editing;
* recipient information;
* delivery address;
* delivery date;
* sale notes;
* sale total;
* draft sales;
* sale editing.

## Expected capabilities

The user must be able to:

1. Create a sale.
2. Select a customer.
3. Add one or more baskets.
4. Review each basket's composition.
5. Modify basket composition when necessary.
6. Define recipient information.
7. Define delivery address.
8. Define delivery date.
9. Add notes.
10. Review the sale total.
11. Save the sale as a draft.
12. Edit the sale before confirmation.

## Sale structure

Conceptually:

```text
Customer
    │
    └── Sale
          │
          ├── Basket
          │     └── Basket Items
          │
          ├── Basket
          │     └── Basket Items
          │
          └── ...
```

A sale must contain at least one basket.

A sale may contain multiple baskets.

Each basket has its own delivery/recipient information.

Multiple baskets may share the same address.

## Important business behavior

M4 introduces the sale but does not yet confirm the sale from a payment perspective.

Inventory must not be deducted merely because a draft sale exists.

Payment processing and confirmation rules belong to M5.

## Explicitly out of scope

M4 does not implement:

* payment recording;
* payment confirmation;
* payment proofs;
* 50% confirmation rule;
* 100% payment-before-delivery rule;
* inventory deduction caused by confirmation;
* payment gateways;
* automatic payment reconciliation.

## Dependency

M1, M2, and M3.

---

# 7. Milestone M5 — Payments

## Objective

Introduce payment tracking and complete the operational sale flow.

## Scope

M5 includes:

* payment registration;
* PIX payments;
* card payments;
* payment amount;
* payment proof;
* payment status;
* total amount paid;
* remaining amount;
* sale confirmation;
* inventory deduction on confirmation;
* post-confirmation sale changes;
* inventory delta adjustments;
* delivery payment requirement.

## Payment rules

The system must support the following business rules:

### Confirmation threshold

A sale is confirmed when at least 50% of its total value has been paid.

```text
Total = R$ 200
Paid  = R$ 100
       ↓
Sale may be confirmed
```

### Delivery requirement

The remaining balance must be fully paid before delivery.

```text
Confirmed
    ↓
Remaining balance
    ↓
Payment completed
    ↓
Delivery allowed
```

Payment status and sale status are separate concepts.

A sale may be confirmed while still having an outstanding balance.

## Inventory behavior

When a sale becomes confirmed, the system deducts the required inventory.

Example:

```text
Before confirmation

Chocolate: 20
Juice:      8

Sale:
Chocolate × 2
Juice × 1

After confirmation

Chocolate: 18
Juice:      7
```

## Changes after confirmation

A confirmed sale may be modified.

Inventory must be adjusted according to the difference between the previous and new composition.

Example:

```text
Original:
Chocolate × 2
Juice × 1

New:
Biscuit × 2
Juice × 1
```

The adjustment is:

```text
+2 Chocolate
-2 Biscuit
```

The original inventory movements remain in history.

The system must not rewrite the original movement to make it appear as though the original sale never happened.

## Cancellation

A confirmed sale may later be cancelled.

Cancellation must preserve the sale and its historical information.

The system must not assume that every item physically returns to inventory.

The physical inventory situation must determine whether inventory corrections are required.

## Explicitly out of scope

M5 does not implement:

* payment gateway integration;
* automatic bank reconciliation;
* automatic PIX verification;
* credit card processing;
* refunds through external providers;
* advanced financial reporting.

## Dependency

M1, M2, M3, and M4.

---

# 8. Phase 1 Integrated Flow

At the end of Phase 1, the following operational flow must be possible:

```text
Product
   ↓
Inventory
   ↓
Basket Template
   ↓
Basket
   ↓
Customer
   ↓
Sale
   ↓
Payment
   ↓
Sale Confirmation
   ↓
Inventory Deduction
```

The system should support the following real-world scenario:

```text
1. Register products
2. Add products to inventory
3. Create or select a basket template
4. Create a basket
5. Customize the basket if necessary
6. Register/select the customer
7. Create a sale
8. Add one or more baskets
9. Define recipient and delivery information
10. Register payment
11. Reach the 50% payment threshold
12. Confirm the sale
13. Deduct inventory
14. Register remaining payment
15. Allow delivery only after full payment
```

---

# 9. Phase 1 Definition of Done

Phase 1 is considered complete only when all of the following are true:

## Product and inventory

* Products can be created and managed.
* Product activation/deactivation works.
* Inventory can be added manually.
* Inventory adjustments are supported.
* Current balances can be viewed.
* Inventory movements are preserved historically.

## Baskets

* Basket templates can be created and managed.
* Baskets can be created from templates.
* Baskets can be created without templates.
* Basket compositions can be customized.
* Multiple quantities of the same product are supported.
* Existing baskets are independent from future template changes.
* Basket cost is calculated.
* Suggested price is calculated.
* Final price can be manually controlled.

## Customers

* Customers can be created and managed.
* Customers can be searched.
* Customers can be activated/deactivated.

## Sales

* Sales can be created.
* A sale can contain one or more baskets.
* Customer association works.
* Basket delivery information works.
* Draft sales can be saved and edited.
* Sale totals are calculated.

## Payments

* PIX and card payments can be recorded.
* Payment amounts are tracked.
* Payment proof can be associated.
* Total paid and remaining balance are visible.
* Sale confirmation follows the 50% payment rule.
* Inventory is deducted when the sale is confirmed.
* Confirmed sale changes adjust inventory by delta.
* Full payment is required before delivery.
* Cancelled sales preserve their history.

## Quality

* Automated tests cover the implemented business behavior.
* Existing automated tests remain passing.
* Manual validation has been performed for each milestone.
* No known critical data-integrity issue remains.
* No milestone has introduced undocumented business rules.
* No unnecessary future functionality has been implemented.

---

# 10. Milestone Completion Rule

A milestone is not considered complete merely because its code has been implemented.

The completion sequence is:

```text
Specification
    ↓
Implementation
    ↓
Automated Tests
    ↓
Agent Verification
    ↓
Human Validation
    ↓
Approval
    ↓
Next Milestone
```

The next milestone must not begin until the current milestone has been explicitly validated.

---

# 11. Scope Control

During Phase 1, new requirements must be classified before implementation.

### A — Required for current milestone

The requirement is necessary for the current milestone to work correctly.

It may be added to the current specification.

### B — Required for a later milestone

The requirement is valid but belongs to another milestone.

It must be documented for that milestone without expanding the current implementation.

### C — Future backlog

The idea may be useful but is not currently required.

It should be recorded as a future opportunity.

### D — Unnecessary complexity

The proposal does not solve a currently established business problem or introduces speculative architecture.

It should not be implemented.

The agent must not silently expand the scope of a milestone.

---

# 12. Handling New Business Rules

If implementation reveals a behavior that has not been defined by the business documentation, the agent must stop and identify the ambiguity.

The agent must not silently invent a business rule.

The process is:

```text
Ambiguity detected
        ↓
Identify the exact business decision
        ↓
Ask the user
        ↓
Document the decision
        ↓
Update specification if necessary
        ↓
Continue implementation
```

Technical implementation details may be chosen by the agent when they do not change business behavior and the simplest reasonable solution is clear.

Business behavior requires explicit confirmation.

---

# 13. Phase 1 Architecture Principle

Phase 1 should remain intentionally simple.

The implementation should favor:

* clear domain concepts;
* straightforward data models;
* simple service/application logic;
* explicit business rules;
* readable code;
* automated tests;
* maintainable database design;
* minimal abstraction;
* incremental evolution.

The implementation must not introduce speculative architecture for future requirements.

The existence of future ideas such as lots, expiration, production, affective dates, communication, or advanced pricing does not justify implementing them during Phase 1.

The current system should be designed so that future evolution remains possible without prematurely implementing that evolution.

---

# 14. Phase 1 Documentation

Each milestone must have its own documentation folder:

```text
docs/milestones/
│
├── phase-1.md
│
├── m1-products-inventory/
│   ├── specification.md
│   ├── use-cases.md
│   ├── acceptance-criteria.md
│   └── validation.md
│
├── m2-baskets/
│   ├── specification.md
│   ├── use-cases.md
│   ├── acceptance-criteria.md
│   └── validation.md
│
├── m3-customers/
│   ├── specification.md
│   ├── use-cases.md
│   ├── acceptance-criteria.md
│   └── validation.md
│
├── m4-sales/
│   ├── specification.md
│   ├── use-cases.md
│   ├── acceptance-criteria.md
│   └── validation.md
│
└── m5-payments/
    ├── specification.md
    ├── use-cases.md
    ├── acceptance-criteria.md
    └── validation.md
```

Milestone-specific documentation should be created when that milestone is about to begin.

Do not create detailed specifications for all milestones in advance.

---

# 15. Current Phase Status

| Milestone                       | Status                   | Notes                                                                        |
| ------------------------------- | ------------------------ | ---------------------------------------------------------------------------- |
| M1 — Products & Inventory       | Ready for implementation | Core business decisions resolved; documentation finalized for implementation |
| M2 — Baskets & Basket Templates | Planned                  | Depends on M1                                                                |
| M3 — Customers                  | Planned                  | Depends on M2                                                                |
| M4 — Sales                      | Planned                  | Depends on M1, M2, M3                                                        |
| M5 — Payments                   | Planned                  | Depends on M1–M4                                                             |

The current development focus is:

> **M1 — Products & Inventory**

Core business decisions for M1 have been resolved:

* **Negative inventory policy: RESOLVED**
  * **Policy:** Physical inventory must never become negative (`INV-006`).
  * Operations that would produce a negative balance are rejected.
  * The invariant is absolute and applies also to concurrent inventory operations (`ADR-001`).

---

# 16. Relationship With Other Documentation

Phase 1 follows the project's documentation hierarchy:

```text
Product Vision
      ↓
Product Roadmap
      ↓
Business Contract
      ↓
Phase 1
      ↓
Milestone Specification
      ↓
Use Cases
      ↓
Acceptance Criteria
      ↓
Implementation
      ↓
Validation
```

The documents serve different purposes and should not duplicate one another unnecessarily.

`phase-1.md` defines the phase structure and boundaries.

It does not replace:

* the Business Contract;
* milestone specifications;
* acceptance criteria;
* architectural decisions;
* implementation documentation.

---

# 17. Guiding Principle

Phase 1 should produce a useful operational system without attempting to solve the entire future of Casa Afeto.

The objective is not to predict every future requirement.

The objective is to establish a solid, simple foundation that can evolve based on real business needs.

> **Build what has been decided. Validate it. Learn from using it. Then build the next thing.**
