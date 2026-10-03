# Casa Afeto — Product Roadmap

**Document version:** 0.1
**Status:** Draft
**Last updated:** 2026-10-02

---

## 1. Purpose

This document defines the planned evolution of the Casa Afeto management system.

Its purpose is to establish:

* the initial delivery sequence;
* the capabilities planned for each phase;
* future areas of evolution;
* boundaries between current scope and future scope.

This roadmap is intentionally high-level.

Detailed behavior belongs in milestone specifications and business rules.

The roadmap is not a commitment to implement every future capability listed here.

Future capabilities must be validated against real business needs before entering active development.

---

# 2. Product Evolution Strategy

The system will be developed incrementally.

The project follows the principle:

> **Build little, validate, learn, then build the next thing.**

The initial product will focus on the operational core:

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

Only after this core flow is operational should additional capabilities be considered.

The roadmap therefore distinguishes between:

1. **Phase 1 — Core Operations**
2. **Phase 2 — Inventory & Customer Evolution**
3. **Phase 3 — Operational Automation**
4. **Future Opportunities**

The phase boundaries are intentionally flexible.

Actual priorities may change based on business feedback.

---

# 3. Phase 1 — Core Operations

## Objective

Create the first reliable version of the Casa Afeto operational system.

The system should allow Casa Afeto to manage the basic relationship between:

* products;
* inventory;
* baskets;
* customers;
* sales;
* payments.

At the end of Phase 1, the system should support the core business flow:

```text
Product
    ↓
Inventory
    ↓
Basket
    ↓
Customer
    ↓
Sale
    ↓
Payment
    ↓
Inventory deduction
```

---

# 4. Phase 1 Milestones

Phase 1 is divided into five milestones.

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

Each milestone should be:

* specified;
* implemented;
* tested;
* manually validated;
* reviewed against the business requirements

before the project moves to the next milestone.

---

# 5. M1 — Products & Inventory

## Objective

Establish the foundation for managing the products used by Casa Afeto and their current inventory.

## Planned capabilities

### Products

* create products;
* edit product information;
* activate products;
* deactivate products;
* search/list products;
* define the product's base inventory unit.

### Inventory

* add inventory;
* remove inventory through supported adjustments;
* view current balance;
* view inventory movement history;
* perform inventory corrections while preserving movement history.

## Important business concepts

M1 establishes inventory as a movement-based concept.

The system should not rely solely on manually changing a single stock number without preserving how that number was produced.

## Explicitly outside M1

The following are not part of this milestone:

* purchases;
* suppliers;
* purchase invoices;
* purchase items;
* inventory lots;
* expiration dates;
* FEFO selection;
* expiration warnings;
* automated replenishment;
* production;
* recipes;
* reserved stock;
* sales-related inventory deduction.

Those concepts may be introduced in later milestones.

---

# 6. M2 — Baskets & Basket Templates

## Objective

Allow Casa Afeto to define standard baskets and create customized baskets for individual sales.

## Planned capabilities

### Basket templates

* create templates;
* edit templates;
* activate/deactivate templates;
* define template composition;
* define product quantities.

### Baskets

* create a basket from a template;
* create a basket without a template;
* add products;
* remove products;
* substitute products;
* define multiple quantities of the same product;
* preserve the concrete basket composition.

A basket may contain a product more than once conceptually, but the preferred representation is a product item with an explicit quantity.

For example:

```text
Chocolate — quantity: 2
Cereal Bar — quantity: 3
Juice — quantity: 1
```

## Stock behavior

A product may be selected for a basket even when there is currently insufficient stock.

The system should make the stock situation visible to the user.

The business may replenish the product before the basket is assembled or delivered.

## Template independence

Once a concrete basket is created, its composition must be independent of future changes to the template.

Changing a template must not modify existing baskets.

## Pricing

M2 may calculate basket cost and suggested price based on its composition.

The final selling price remains under business control.

---

# 7. M3 — Customers

## Objective

Establish the basic customer record required to associate sales with customers.

## Planned capabilities

* create customers;
* edit customer information;
* search customers;
* activate/deactivate customers;
* associate sales with customers.

## Scope philosophy

M3 should remain intentionally simple.

It is not intended to become a full CRM.

## Explicitly outside M3

* customer segmentation;
* marketing campaigns;
* automated reminders;
* loyalty programs;
* customer scoring;
* advanced customer analytics;
* affective dates;
* automated WhatsApp communication.

These may be evaluated later.

---

# 8. M4 — Sales

## Objective

Create and manage the commercial transaction connecting customers and baskets.

## Planned capabilities

A sale should allow the user to:

* select a customer;
* add one or more baskets;
* view basket compositions;
* modify basket composition;
* define recipient information;
* define delivery address;
* define delivery date;
* add relevant notes;
* calculate sale totals;
* save the sale as a draft;
* modify a draft sale.

## Sale lifecycle

The initial operational lifecycle is expected to follow:

```text
DRAFT
   ↓
CONFIRMED
   ↓
PREPARING
   ↓
READY
   ↓
DELIVERED
```

A cancelled state is also expected:

```text
DRAFT / CONFIRMED / PREPARING / READY
                  ↓
              CANCELLED
```

The exact transition rules will be defined in the milestone specification.

## Important scope boundary

M4 creates the sales structure but does not introduce the complete payment-confirmation workflow.

Payment behavior belongs to M5.

---

# 9. M5 — Payments

## Objective

Connect payment information to the sales lifecycle and establish the rules for sale confirmation and inventory deduction.

## Planned capabilities

* record payments;
* support PIX;
* support card payments;
* record payment proof;
* track total amount paid;
* calculate remaining balance;
* determine whether the confirmation threshold has been reached.

## Confirmation rule

The current business rule is:

> A sale is confirmed when at least 50% of its total value has been paid.

Once confirmed, the sale generates the corresponding inventory deduction.

```text
Payment >= 50%
       ↓
Sale confirmed
       ↓
Inventory deducted
```

## Remaining payment

The remaining balance must be paid before delivery.

The current business rule is:

> 100% of the sale must be paid before delivery.

## Post-confirmation changes

A confirmed sale may be modified.

When its basket composition changes, inventory should be adjusted according to the difference between the previous and new compositions.

Example:

```text
Original:
2 × Chocolate
1 × Juice

New:
2 × Biscuit
1 × Juice

Inventory adjustment:
+2 Chocolate
-2 Biscuit
```

The original inventory movement remains part of the historical record.

---

# 10. Phase 1 Definition of Done

Phase 1 should be considered complete when Casa Afeto can execute the following flow through the system:

```text
Create Product
      ↓
Manage Inventory
      ↓
Create Basket Template
      ↓
Create Customized Basket
      ↓
Create Customer
      ↓
Create Sale
      ↓
Record Payment
      ↓
Reach Confirmation Threshold
      ↓
Confirm Sale
      ↓
Deduct Inventory
      ↓
Complete Delivery Flow
```

The exact acceptance criteria belong to the individual milestone documents.

---

# 11. Phase 2 — Inventory & Customer Evolution

Phase 2 represents capabilities that become valuable once the core operational flow is working.

These capabilities should only be promoted into active development after the Phase 1 experience provides sufficient evidence that they are needed.

---

## 11.1 Purchase Management

Potential capabilities:

* register purchases;
* register purchase items;
* record acquisition quantities;
* record purchase prices;
* convert commercial purchase units into inventory units;
* associate purchases with inventory.

Example:

```text
1 box
×
24 units per box
=
24 inventory units
```

The system should preserve the actual acquisition price rather than replacing previous historical costs.

---

## 11.2 Inventory Lots

Potential capability:

Represent stock acquired at different times and prices as separate inventory lots.

Example:

```text
Chocolate

Lot A
Cost: R$2.50
Quantity: 20

Lot B
Cost: R$1.80
Quantity: 15
Expiration: earlier
```

This allows the system to distinguish between different acquisition contexts.

The exact lot-selection strategy must be defined as a business rule when this functionality enters active development.

---

## 11.3 Expiration Management

Potential capabilities:

* expiration dates;
* expiration warnings;
* products approaching expiration;
* preferential use of products with nearer expiration;
* visibility of expired inventory.

A nearest-expiration-first strategy is currently a possible business policy.

It should remain a replaceable business rule rather than becoming an architectural assumption.

---

## 11.4 Inventory Replenishment

Potential capabilities:

* identify products needed by upcoming baskets;
* identify insufficient inventory;
* highlight products requiring replenishment;
* distinguish normal stock needs from urgent needs created by confirmed sales.

The system should first provide visibility before attempting to automate purchasing.

---

## 11.5 Affective Dates

Potential customer-related functionality may include:

```text
Customer
   ↓
Person / Recipient
   ↓
Occasion
   ↓
Date
```

Examples:

* birthday;
* wedding anniversary;
* other relevant occasions.

Potential future capabilities:

* record important dates;
* list upcoming dates;
* notify the business;
* support proactive customer contact.

This functionality is explicitly outside Phase 1.

---

# 12. Phase 3 — Operational Automation

After the core operation and inventory/customer evolution are stable, the system may evolve toward reducing repetitive work.

Potential areas include:

## Communication

Possible integrations with:

* WhatsApp;
* customer communication workflows;
* order status communication;
* payment reminders.

These integrations should only be implemented when their business process is clearly defined.

---

## Automated Notifications

Potential notifications may include:

* upcoming delivery;
* outstanding payment;
* approaching expiration;
* upcoming affective date;
* replenishment needs.

Each notification should have an explicit business purpose before implementation.

---

## Operational Dashboards

Potential dashboards may provide:

* upcoming deliveries;
* sales by period;
* outstanding payments;
* inventory situation;
* products requiring attention;
* upcoming affective dates.

Reporting should be introduced according to actual business needs rather than creating a large reporting subsystem in advance.

---

# 13. Future Opportunities

The following capabilities may become relevant as Casa Afeto grows.

They are recorded here as possibilities, not commitments.

---

## 13.1 Internal Production

Some products may be produced internally.

Potential capabilities:

* recipes;
* ingredients;
* production batches;
* production quantities;
* production costs;
* expiration dates.

Example:

```text
Recipe
   ↓
Ingredients
   ↓
Production
   ↓
Finished Product
   ↓
Inventory
```

This should only be introduced once the business defines an actual production process.

---

## 13.2 Advanced Pricing

Future pricing functionality could include:

* pricing rules;
* margin analysis;
* historical prices;
* seasonal pricing;
* promotions;
* discounts.

The current system should not implement these concepts speculatively.

---

## 13.3 Advanced Customer Management

Possible future capabilities:

* customer history;
* purchase patterns;
* customer preferences;
* segmentation;
* repeat-purchase analysis;
* personalized offers.

These should only be introduced if they provide measurable operational or commercial value.

---

## 13.4 Business Analytics

Potential future reporting may include:

* revenue;
* cost;
* margins;
* sales by basket;
* product consumption;
* inventory turnover;
* payment behavior;
* customer recurrence.

Analytics should evolve from actual data and business questions.

---

# 14. Backlog Classification

Ideas discovered during development should be classified rather than automatically implemented.

Each new idea should belong to one of the following categories:

### A — Current milestone requirement

The functionality is necessary to complete the milestone currently being implemented.

It may enter the current specification.

### B — Required future milestone

The functionality is important but does not belong to the current milestone.

It should be documented and deferred.

### C — Future backlog idea

The idea may be useful but requires further validation.

It should be recorded without affecting the current architecture.

### D — Unnecessary complexity

The idea does not currently solve a meaningful business problem or introduces disproportionate complexity.

It should not be implemented.

---

# 15. Roadmap Change Policy

The roadmap is not immutable.

Business learning may justify changing the sequence.

However, changes should be deliberate.

A proposed change should identify:

1. What changed?
2. What business problem does it address?
3. Why is it needed now?
4. Which milestone does it affect?
5. What existing scope would be displaced or delayed?
6. Does it introduce new domain concepts?
7. Does it require an architectural decision?

The project should avoid expanding a milestone simply because an agent identifies a potentially useful future capability.

---

# 16. Relationship Between Roadmap and Specifications

The roadmap defines **what is planned and approximately when**.

It does not define detailed behavior.

The relationship is:

```text
Vision
   ↓
Roadmap
   ↓
Milestone
   ↓
Specification
   ↓
Use Cases
   ↓
Acceptance Criteria
   ↓
Implementation
```

For example:

```text
Roadmap:
M1 — Products & Inventory

        ↓

M1 Specification:
Create and manage products

        ↓

Use Case:
Create Product

        ↓

Acceptance Criteria:
Given valid product information
When the user saves the product
Then the product is persisted and available for selection
```

The detailed rules belong in the milestone documentation.

---

# 17. Current Development Priority

The immediate development priority is:

> **M1 — Products & Inventory**

No functionality from later milestones should be implemented merely because it may eventually be useful.

The M1 specification is finalized with all core business decisions resolved:

* **Negative inventory policy: RESOLVED**
  * **Policy:** Physical inventory must never become negative (`INV-006`).
  * Operations that would produce a negative balance are rejected.
  * This invariant is absolute and also applies to concurrent inventory operations (`ADR-001`).

With these decisions established, M1 is ready for implementation with a stable business contract.

---

# 18. Roadmap Summary

```text
PHASE 1 — CORE OPERATIONS
─────────────────────────────────────

M1  Products & Inventory
 ↓
M2  Baskets & Basket Templates
 ↓
M3  Customers
 ↓
M4  Sales
 ↓
M5  Payments


PHASE 2 — EVOLUTION
─────────────────────────────────────

Purchases
Inventory Lots
Expiration
Replenishment
Affective Dates


PHASE 3 — AUTOMATION
─────────────────────────────────────

Communication
Notifications
Operational Dashboards


FUTURE OPPORTUNITIES
─────────────────────────────────────

Internal Production
Advanced Pricing
Advanced Customer Management
Business Analytics
```

The roadmap exists to provide direction without becoming a constraint on learning.

The system should evolve according to real Casa Afeto needs, with each capability entering development only when its business value and behavior are sufficiently understood.
