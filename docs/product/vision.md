# Casa Afeto — Product Vision

**Document version:** 0.1
**Status:** Draft
**Last updated:** 2026-10-02

---

## 1. Product Overview

Casa Afeto is a business focused on creating and selling breakfast baskets and affectionate gift baskets.

The business operates through personalized orders, where a customer chooses a basket, requests changes when necessary, agrees on a delivery date and recipient, makes payment, and the Casa Afeto team prepares and delivers the order.

The purpose of this system is to provide Casa Afeto with a simple, reliable, and centralized way to manage its sales operation.

The system should connect the main business activities involved in an order:

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
    ↓
Inventory
```

The system is intended to reduce manual work, improve visibility over the business, preserve historical information, and provide a foundation for future operational improvements.

---

## 2. Product Vision

Build a practical sales management system that allows Casa Afeto to manage its products, inventory, baskets, customers, sales, and payments in one place, while keeping the system simple enough to reflect the actual way the business operates.

The system should support the business without forcing the business to adapt its processes to unnecessary software complexity.

The guiding principle is:

> **The software should make the Casa Afeto operation easier to manage, not make the operation more complicated.**

---

## 3. Problem

The Casa Afeto operation involves several pieces of information that are naturally connected but can become difficult to manage when handled manually.

A single sale may involve:

* a customer;
* one or more baskets;
* different basket compositions;
* products with different quantities;
* a recipient different from the customer;
* a delivery address;
* a delivery date;
* payments made at different times;
* inventory consumption;
* changes to the order after it has been created.

Without a centralized system, maintaining consistency between these pieces of information becomes increasingly difficult.

The system therefore needs to provide a reliable source of operational information while preserving the flexibility required by the business.

---

## 4. Target Users

The primary users are the people responsible for operating Casa Afeto.

The initial system is designed primarily for internal business use rather than for customers to place orders directly.

The system should prioritize:

* simplicity;
* speed of operation;
* clarity;
* low administrative overhead;
* reliable historical information;
* easy correction of operational mistakes.

---

## 5. Core Business Flow

The system should support the real-world flow of a typical Casa Afeto order.

```text
Customer contacts Casa Afeto
        ↓
Customer chooses a basket
        ↓
Basket composition may be customized
        ↓
Delivery information is defined
        ↓
Payment is received
        ↓
Sale is confirmed
        ↓
Inventory is consumed
        ↓
Basket is prepared
        ↓
Basket is delivered
```

The system does not need to reproduce every communication or operational activity performed by the business.

Its responsibility is to maintain the information necessary to manage and control the business operation.

---

## 6. Product Principles

### 6.1 Business-first

Business rules should drive the software design.

The system should represent how Casa Afeto actually operates instead of introducing generic processes merely because they are common in other systems.

---

### 6.2 Simplicity over abstraction

The system should use the simplest design that correctly solves the current business problem.

It should avoid unnecessary:

* abstractions;
* frameworks;
* architectural layers;
* generic infrastructure;
* integrations;
* automation;
* domain concepts;
* configuration mechanisms.

Complexity should be introduced only when there is a concrete business or technical reason.

---

### 6.3 Historical information matters

Important business events should preserve their history.

For example:

* changing the cost of a product should not rewrite historical acquisition information;
* changing a basket template should not change baskets that were already created;
* correcting inventory should preserve the original movement and create a new correction;
* cancelling a sale should not erase the sale from the system.

The system should favor traceability over destructive updates when historical information is relevant.

---

### 6.4 Flexibility where the business needs it

Casa Afeto sells personalized baskets.

Therefore, the system must allow a basket based on a standard template to be modified for a specific customer.

A basket may:

* use a template;
* be created without a template;
* contain multiple quantities of the same product;
* have products added or removed;
* have products substituted.

The resulting basket represents the actual basket sold to the customer.

---

### 6.5 Human control over final decisions

The system may calculate and suggest values, but the business should retain control over important commercial decisions.

For example, the system may calculate:

* basket cost;
* suggested selling price;
* amount already paid;
* remaining amount.

The final selling price remains a business decision.

---

### 6.6 Progressive evolution

The product should evolve incrementally.

Each milestone should solve a clearly defined problem before the next area is implemented.

The project should follow:

```text
Define
  ↓
Specify
  ↓
Build
  ↓
Test
  ↓
Validate
  ↓
Learn
  ↓
Build the next thing
```

Future ideas should not automatically become current requirements.

---

## 7. Core Product Areas

The initial product is organized around five core operational areas.

### Products

Products represent items that Casa Afeto uses in its baskets.

Examples include:

* chocolates;
* cereal bars;
* juices;
* cakes;
* coffees;
* mugs;
* cards;
* packaging materials.

Products have a base inventory unit and can be activated or deactivated.

---

### Inventory

Inventory represents the physical availability of products used by Casa Afeto.

The system should provide visibility into:

* current quantities;
* additions;
* deductions;
* corrections;
* inventory history.

Inventory should ultimately be based on movements rather than relying only on a manually edited current quantity.

The system is expected to evolve toward more detailed inventory concepts such as acquisition lots, costs, and expiration dates as the business requires them.

---

### Baskets

Baskets are the main commercial product sold by Casa Afeto.

A basket can be created from a standard template or created independently.

A template provides a standard composition, but the concrete basket sold to a customer may differ from that template.

The system should preserve the actual composition of each basket.

---

### Customers

Customers represent the people who purchase from Casa Afeto.

The customer record should provide the information necessary to identify and manage customers and their sales.

More advanced customer relationship functionality is intentionally outside the initial product scope.

---

### Sales

A sale represents a commercial transaction with a customer.

A sale may contain one or more baskets.

Each basket may have its own:

* recipient;
* delivery address;
* delivery date;
* composition.

A sale progresses through operational states as it moves from creation to delivery.

---

### Payments

Payments represent amounts received for a sale.

The initial system should support the business's current payment process, including:

* PIX;
* card payments;
* payment proof;
* partial payments;
* payment balance.

Payment status is related to, but distinct from, the operational status of the sale.

---

## 8. Pricing Vision

The system should assist Casa Afeto with pricing without imposing a rigid pricing formula.

The current business practice uses approximately twice the basket cost as a reference for the suggested selling price.

Conceptually:

```text
Basket Cost
     ↓
Suggested Price
     ↓
Business Adjustment
     ↓
Final Selling Price
```

For example, a basket costing R$85 may have a suggested price of approximately R$170, while the final selling price may be manually adjusted.

The suggested price is therefore a reference, not a mandatory business rule.

When the composition of a basket changes, its cost and suggested price should be recalculated based on the resulting composition.

---

## 9. Inventory and Sales Relationship

Inventory is directly connected to the sales lifecycle.

The intended behavior is:

```text
Sale created
    ↓
Sale remains a draft
    ↓
Payment reaches confirmation threshold
    ↓
Sale becomes confirmed
    ↓
Inventory is deducted
```

The system should preserve the relationship between a sale and the inventory changes it causes.

If a confirmed sale is later modified, the system should adjust inventory according to the difference between the previous and new compositions rather than rewriting the original inventory history.

This allows the business to understand what happened over time.

---

## 10. Product Cost and Acquisition History

The cost of a product is not necessarily fixed.

The same product may be purchased at different prices.

For example:

```text
Cereal Bar

Purchase A → R$2.50 / unit
Purchase B → R$1.80 / unit
```

The system should therefore avoid treating product cost as a permanent property of the product itself.

Future inventory evolution may associate stock with its acquisition context, including:

* acquisition cost;
* quantity;
* expiration date;
* remaining quantity.

The exact implementation and business rules for this functionality will be defined when that functionality becomes part of an approved milestone.

---

## 11. Personalization

Personalization is an important characteristic of the Casa Afeto business.

The system should support the reality that a customer may request changes to a standard basket.

For example:

```text
Template
    ↓
Standard basket
    ↓
Customer requests changes
    ↓
Concrete basket
    ↓
Actual sale
```

The concrete basket must represent what was actually sold, regardless of later changes to the original template.

---

## 12. Future Product Evolution

The initial product focuses on the core sales operation.

Future versions may evolve to support additional capabilities such as:

### Customer relationship and affective dates

Casa Afeto may eventually maintain important dates associated with customers and recipients, such as:

* birthdays;
* wedding anniversaries;
* other relevant occasions.

This could allow the business to identify upcoming dates and proactively contact customers.

This functionality is intentionally outside the initial MVP.

---

### Expiration and inventory optimization

Future inventory functionality may include:

* product lots;
* expiration dates;
* expiration warnings;
* preferential use of products approaching expiration;
* more sophisticated stock selection.

The business currently considers a nearest-expiration-first strategy conceptually desirable, but this is a future business policy and should not be treated as an immutable architectural rule.

---

### Internal production

Some Casa Afeto products may eventually be produced internally, such as cakes.

Future functionality could therefore support:

* recipes;
* ingredients;
* production quantities;
* production costs;
* expiration.

This functionality is not part of the initial product.

---

### Replenishment

The system may eventually identify situations where products required by already-sold baskets need to be replenished.

This could provide visibility into upcoming inventory needs.

This functionality is not part of the initial product.

---

### Business communication

Future versions may integrate with communication channels such as WhatsApp to reduce manual work around customer communication.

Such integrations should only be introduced when there is a clearly defined business requirement.

---

## 13. MVP Scope

The first phase of the product focuses on the following capabilities:

```text
Products
    ↓
Inventory
    ↓
Basket Templates
    ↓
Baskets
    ↓
Customers
    ↓
Sales
    ↓
Payments
    ↓
Inventory deduction
```

The first phase is divided into:

```text
M1 — Products & Inventory
M2 — Baskets & Basket Templates
M3 — Customers
M4 — Sales
M5 — Payments
```

The goal is not to implement every possible Casa Afeto process.

The goal is to establish a reliable operational foundation that can be validated and evolved.

---

## 14. Explicitly Outside the Initial Scope

The following are not part of the initial product unless a future requirement explicitly brings them into scope:

* customer self-service ordering;
* online payment gateway integration;
* WhatsApp integration;
* automated marketing campaigns;
* affective-date reminders;
* advanced CRM;
* supplier management;
* automated purchasing;
* expiration alerts;
* automated replenishment;
* production management;
* recipe management;
* ingredient management;
* shipping/logistics management;
* promotions;
* discount management;
* invoicing integration;
* multi-company management;
* advanced reporting and business intelligence.

Their exclusion does not mean they can never exist.

It means they should not influence the architecture or implementation of the current product unless a concrete requirement makes them relevant.

---

## 15. Success Criteria

The initial product should be considered successful when Casa Afeto can manage the core operational flow without depending on disconnected manual records for the information covered by the system.

At minimum, the system should allow the business to:

1. Maintain its products.
2. Know current inventory quantities.
3. Understand inventory movements.
4. Define standard basket templates.
5. Create customized baskets.
6. Maintain customer information.
7. Create sales containing one or more baskets.
8. Record payment information.
9. Determine when a sale reaches the confirmation threshold.
10. Deduct inventory when a sale is confirmed.
11. Preserve historical information when corrections or changes occur.
12. Understand the current state of an order without reconstructing it manually from different sources.

---

## 16. Product Quality Attributes

The system should prioritize the following qualities.

### Correctness

Business rules must be respected consistently.

### Traceability

Important changes to inventory, sales, payments, and other business information should remain understandable after the fact.

### Simplicity

The system should remain easy to understand and operate.

### Maintainability

The codebase should be structured so that future changes can be made without unnecessary coupling.

### Evolvability

The system should be capable of growing as real business requirements emerge, without implementing speculative functionality in advance.

### Usability

Common operational tasks should require as few unnecessary steps as possible.

---

## 17. Guiding Principle for Development

Every feature should answer a concrete business need.

Before implementing a new capability, the project should be able to answer:

> **What problem in the Casa Afeto operation does this solve?**

If the answer is unclear, the feature should not automatically be added to the current scope.

The project should favor:

```text
Real requirement
    ↓
Clear business rule
    ↓
Small implementation
    ↓
Automated tests
    ↓
Human validation
    ↓
Real-world feedback
```

over:

```text
Possible future need
    ↓
Generic abstraction
    ↓
Complex architecture
    ↓
Unused functionality
```

---

## 18. Relationship With Other Documentation

This document defines the product vision and high-level direction.

It does not define detailed implementation requirements.

The documentation hierarchy is:

```text
Product Vision
      ↓
Business Contract
      ↓
Domain Model / Business Rules
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

Each document should have a clear responsibility and should avoid duplicating information already defined elsewhere.

The Product Vision should remain relatively stable as the system evolves.

---

## 19. Change Policy

The product vision may evolve as Casa Afeto learns from using the system.

Changes should be made deliberately.

A new idea should first be classified as one of:

* current requirement;
* future milestone;
* future backlog item;
* rejected or unnecessary complexity.

A future idea should not automatically become an implementation requirement.

When a significant change affects the product direction, this document should be updated so that it remains an accurate representation of the product's purpose and boundaries.

---

## 20. Current Product Direction

The immediate objective is to build the smallest useful version of the Casa Afeto management system and validate it through real business use.

The project will begin with:

**M1 — Products & Inventory**

and progressively evolve through:

```text
M1 Products & Inventory
        ↓
M2 Baskets & Basket Templates
        ↓
M3 Customers
        ↓
M4 Sales
        ↓
M5 Payments
```

Each milestone should be specified, implemented, tested, and validated before the project moves forward.

The system should grow from **real Casa Afeto needs**, rather than from assumptions about what a complete business-management platform might eventually require.

