# M1 — Products & Inventory Specification

**Document version:** 0.1
**Status:** Ready for implementation
**Milestone:** M1 — Products & Inventory
**Phase:** 1 — Core Operations

---

# 1. Purpose

M1 establishes the basic Product and Inventory capabilities required by the Casa Afeto system.

The milestone must allow Casa Afeto to:

* register products;
* manage product availability;
* maintain physical inventory;
* record inventory entries;
* record inventory adjustments;
* view current inventory balances;
* view inventory movement history;
* identify insufficient inventory.

M1 is the foundation for the Basket, Sale, and Payment milestones.

---

# 2. Scope

## 2.1 In Scope

M1 includes:

### Product

* create product;
* edit product;
* activate product;
* deactivate product;
* list products;
* search products;
* identify product inventory unit.

### Inventory

* record positive inventory entries;
* record inventory adjustments;
* calculate current inventory balance;
* display inventory availability;
* display inventory movement history;
* prevent negative physical inventory.

---

# 3. Explicitly Out of Scope

The following must not be implemented as part of M1:

* Purchase entity/workflow;
* PurchaseItem entity/workflow;
* Supplier management;
* InventoryLot;
* expiration dates;
* FEFO;
* automatic stock consumption;
* sale-related inventory deduction;
* basket-related inventory deduction;
* reserved inventory;
* replenishment requests;
* expiration alerts;
* loss management workflow;
* production;
* recipes;
* internal production;
* payment management;
* sales;
* baskets;
* customers;
* notifications;
* dashboards;
* advanced inventory analytics.

If implementation appears to require one of these capabilities, the agent must stop and determine whether the requirement is genuinely necessary for M1.

It must not silently expand the scope.

---

# 4. Dependencies

M1 depends on:

* `docs/product/vision.md`
* `docs/product/roadmap.md`
* `docs/domain/business-contract.md`
* `AGENTS.md`

No other milestone is required.

---

# 5. Domain Concepts

M1 introduces two primary concepts:

```text
Product
Inventory
```

Inventory is represented through movements rather than through an operation that simply overwrites a stock quantity.

Conceptually:

```text
Product
   │
   └── Inventory Movements
             │
             ├── Entry
             └── Adjustment
```

The current balance represents the resulting physical quantity.

---

# 6. Product

## 6.1 Product Definition

A Product represents an item that can be used by Casa Afeto in its operational processes.

Examples:

* Chocolate
* Juice
* Coffee
* Cereal Bar
* Mug
* Card
* Cake
* Packaging

M1 does not distinguish between purchased products and internally produced products.

That distinction belongs to future functionality.

---

# 7. Product Data Requirements

A product must contain, at minimum:

| Field       | Required | Description                                         |
| ----------- | -------: | --------------------------------------------------- |
| `id`        |      Yes | Unique product identifier                           |
| `name`      |      Yes | Product name                                        |
| `base_unit` |      Yes | Unit used to represent inventory quantity           |
| `active`    |      Yes | Whether the product is available for new operations |

The implementation may contain technical metadata such as:

* creation timestamp;
* update timestamp.

Such fields are implementation details and do not change the business model.

---

# 8. Product Name

Product name is required.

The system should reject a product without a meaningful name.

The exact validation rules for whitespace, maximum length, and allowed characters should follow the project's existing technical conventions unless a business requirement specifies otherwise.

The agent must not invent unnecessary restrictions.

---

# 9. Base Inventory Unit

Every product must have a base inventory unit.

Examples:

```text
Chocolate → UN
Juice     → UN
Coffee    → UN
```

The unit represents how physical inventory is counted.

M1 should support the minimum unit vocabulary required by the current business.

If the existing application has no established unit vocabulary, the implementation should use a simple explicit representation rather than introducing a generic unit-conversion framework.

Purchase-unit conversion belongs to future Purchase functionality.

---

# 10. Product Activation

Products may be active or inactive.

## Active

An active product may be selected by future operational features.

## Inactive

An inactive product should not be selectable for new operational operations.

Deactivation must not:

* delete the product;
* delete inventory;
* delete inventory movements;
* alter historical information.

Existing historical references to an inactive product must remain valid.

---

# 11. Product Editing

The user may edit product information.

Editing a product must not rewrite historical inventory movements.

For example, changing:

```text
Chocolate
```

to:

```text
Premium Chocolate
```

must not modify historical inventory movement records.

Historical movements continue to refer to the same product.

---

# 12. Product Listing

The system must provide a product listing.

The listing must allow the user to identify at least:

* product name;
* base inventory unit;
* active/inactive state;
* current inventory balance.

The exact UI representation is an implementation concern.

---

# 13. Product Search

The system must allow products to be searched by name.

Search behavior should remain simple.

M1 does not require:

* fuzzy search;
* full-text search infrastructure;
* relevance ranking;
* advanced filters;
* search indexing infrastructure.

If the existing technology stack provides a simple appropriate mechanism, use it.

---

# 14. Inventory Model

Inventory is represented as a sequence of movements.

Conceptually:

```text
Initial state
    ↓
Movement +20
    ↓
Balance = 20
    ↓
Movement -3
    ↓
Balance = 17
```

The system must preserve each movement.

The current balance must not require rewriting historical movements.

---

# 15. Inventory Movement

An inventory movement represents a change in physical product quantity.

M1 requires the following movement categories:

### Entry

Adds physical quantity.

Example:

```text
+20 Chocolate
```

### Adjustment

Corrects the recorded quantity.

An adjustment may be positive or negative.

Example:

```text
+3 Chocolate
```

or:

```text
-2 Chocolate
```

M1 does not implement sale, purchase, expiration, loss, or production movement types.

---

# 16. Inventory Movement Data

A movement must contain, at minimum:

| Field        | Required | Description                 |
| ------------ | -------: | --------------------------- |
| `id`         |      Yes | Unique movement identifier  |
| `product_id` |      Yes | Product affected            |
| `quantity`   |      Yes | Quantity change             |
| `type`       |      Yes | Movement category           |
| `created_at` |      Yes | Movement creation timestamp |

The movement quantity must preserve its sign or otherwise unambiguously represent the direction of the movement.

For example:

```text
ENTRY       +20
ADJUSTMENT   -3
```

The implementation must choose one consistent representation.

---

# 17. Movement Immutability

Once an inventory movement has been recorded, it must not be silently rewritten to change inventory history.

Historical inventory is important.

If an incorrect movement was recorded, the correction must be represented by another movement.

Example:

```text
Original:

+20

Correction:

-3

Current balance:

17
```

The original `+20` movement remains part of the history.

---

# 18. Inventory Balance

The inventory balance for a product is the resulting quantity from its inventory movements.

Conceptually:

```text
Balance =
sum(all applicable inventory movements)
```

Example:

```text
+20
-3
+5
-2

Balance = 20
```

The implementation may maintain a materialized/current balance for performance if necessary, but such an optimization must not replace the movement history as the source of truth.

For M1, the simplest correct implementation should be preferred.

---

# 19. Negative Inventory Policy

Physical inventory must never become negative.

Before creating a negative inventory movement, the system must verify that the resulting balance remains greater than or equal to zero.

Example:

```text
Current balance = 5

Adjustment = -3

Result = 2

Allowed
```

But:

```text
Current balance = 2

Adjustment = -3

Result = -1

Rejected
```

The rejected operation must not create a movement.

---

# 20. Insufficient Inventory

M1 must expose whether a product has insufficient inventory for a requested quantity.

Example:

```text
Available: 2
Required:  5

Shortage: 3
```

The system must be able to represent this state without modifying inventory.

This is important because future basket and sale functionality may need to register a requirement before inventory is available.

M1 must therefore not treat "insufficient inventory" as equivalent to "invalid product."

---

# 21. Inventory Entry

M1 must provide a way to manually add physical inventory.

Example:

```text
Product: Chocolate
Quantity: 20
```

Result:

```text
Inventory balance: 20
```

The operation creates an inventory movement.

The system must not simply overwrite the previous balance.

---

# 22. Inventory Adjustment

M1 must provide a way to correct physical inventory.

Example:

```text
Recorded:
20

Physical:
17

Adjustment:
-3

New balance:
17
```

Positive adjustments are also allowed:

```text
Recorded:
17

Physical:
19

Adjustment:
+2

New balance:
19
```

Adjustments must preserve movement history.

---

# 23. Inventory Movement History

The system must provide a way to inspect movements associated with a product.

At minimum, the history should allow the user to identify:

* date/time;
* movement type;
* quantity change;
* resulting balance, if practical;
* product.

The system should present movements in a clear chronological order.

The exact presentation is an implementation decision.

---

# 24. Inventory Transaction Integrity

Inventory changes must be atomic from the business perspective.

For an inventory operation:

```text
Validate
    ↓
Create movement
    ↓
Update/derive balance
```

The system must not leave a partially completed inventory operation.

For example, it must not be possible to create a movement record while failing to maintain the inventory state expected by the application.

The implementation mechanism depends on the persistence technology.

---

# 25. Product Deactivation and Inventory

Deactivating a product does not remove or alter its inventory.

Example:

```text
Chocolate
Inventory: 15

Deactivate product

Chocolate
Active: false
Inventory: 15
```

The inventory history remains intact.

Future business functionality may determine how inactive products are handled operationally.

M1 should only enforce that inactive products cannot be selected for new operations that require active products.

---

# 26. Business Rules Used by M1

M1 must implement the following rules from the Business Contract:

### INV-001 — Movement-Based Inventory

Inventory changes are represented through inventory movements.

### INV-002 — Historical Inventory Preservation

Inventory corrections preserve the original movement history.

### INV-006 — No Negative Physical Inventory

The system must not create an inventory movement that causes the available physical inventory balance of a product to become negative.

### INV-003 — Insufficient Stock May Be Selected

A product with insufficient inventory may be selected for future basket/sale operations, provided the shortage is clearly indicated.

M1 only needs to provide the inventory state and information required for later milestones to implement this behavior.

### Product Activation

An inactive product must not be selectable for new operations requiring active products.

---

# 27. Use Case Summary

M1 must support these primary use cases:

```text
UC-M1-01 Create Product
UC-M1-02 Edit Product
UC-M1-03 Activate Product
UC-M1-04 Deactivate Product
UC-M1-05 List Products
UC-M1-06 Search Products
UC-M1-07 Add Inventory
UC-M1-08 Adjust Inventory
UC-M1-09 View Inventory Balance
UC-M1-10 View Inventory History
UC-M1-11 Check Inventory Availability
```

Detailed user flows belong in `use-cases.md`.

---

# 28. Error Handling

The system must provide clear feedback for invalid operations.

At minimum:

### Product

* missing required product name;
* invalid base unit;
* attempt to use an inactive product where an active product is required.

### Inventory

* zero/invalid quantity where not allowed;
* inventory adjustment that would produce a negative balance;
* unknown product;
* invalid movement type.

Error messages should explain what prevented the operation.

The implementation should not expose unnecessary technical details to the user.

---

# 29. Data Integrity

The implementation must preserve the following invariants:

### Product invariant

Every inventory movement references an existing product.

### Quantity invariant

Inventory quantities must use a consistent unit representation.

### Negative inventory invariant

The resulting physical inventory balance must never be negative.

### Historical invariant

Existing inventory movements must not be silently rewritten or deleted as part of a normal correction.

### Activation invariant

Product deactivation does not remove historical information.

---

# 30. Testing Requirements

M1 must include automated tests for the established business behavior.

At minimum, tests must cover:

## Product

* create product;
* edit product;
* activate product;
* deactivate product;
* list products;
* search products.

## Inventory

* add inventory;
* calculate balance;
* create positive adjustment;
* create negative adjustment;
* preserve movement history;
* reject negative resulting balance;
* identify insufficient inventory;
* maintain inventory after product deactivation.

## Data integrity

* movement references a valid product;
* invalid inventory operation does not create a movement;
* rejected negative adjustment does not alter the balance.

Tests should focus on business behavior rather than implementation details.

---

# 31. Acceptance Boundary

M1 is complete when the following scenario works:

```text
1. Create Chocolate
2. Set base unit = UN
3. Verify product is active
4. Add 20 Chocolate units
5. Verify balance = 20
6. Add adjustment -3
7. Verify balance = 17
8. Verify both movements remain in history
9. Attempt adjustment -18
10. Operation is rejected
11. Verify balance remains 17
12. Verify no invalid movement was created
13. Check availability for 20 units
14. System reports insufficient inventory
15. Deactivate Chocolate
16. Verify historical inventory remains available
17. Verify inactive Chocolate cannot be selected for new operations
```

---

# 32. Implementation Constraints

The implementation must follow the project-level rules in `AGENTS.md`.

In particular:

* do not introduce speculative architecture;
* do not implement future milestones;
* do not create generic abstractions without a current need;
* do not introduce a repository/service/event architecture merely because it may be useful later;
* do not implement Purchase or InventoryLot;
* do not implement sale inventory deduction;
* do not implement negative inventory;
* do not invent additional business rules.

The simplest implementation that satisfies this specification is preferred.

---

# 33. Architecture Decisions

M1 does not prescribe:

* programming language/framework structure;
* exact database schema;
* ORM;
* API architecture;
* frontend component structure;
* repository pattern;
* service layer;
* dependency injection;
* caching;
* event systems.

These are implementation decisions.

The agent should use the project's existing technical conventions where they exist.

If a significant architectural decision becomes necessary, it must be presented explicitly and documented as an ADR when appropriate.

---

# 34. Implementation Sequence

The recommended implementation order is:

```text
1. Product model
       ↓
2. Product persistence
       ↓
3. Product operations
       ↓
4. Product activation/deactivation
       ↓
5. Inventory movement model
       ↓
6. Inventory balance
       ↓
7. Inventory entry
       ↓
8. Inventory adjustment
       ↓
9. Negative inventory protection
       ↓
10. Inventory history
       ↓
11. Availability check
       ↓
12. Automated tests
       ↓
13. Manual validation
```

The agent may adjust this sequence if the existing project architecture makes another order simpler, but it must not expand the business scope.

---

# 35. Completion Criteria

M1 can be considered complete only when:

* all in-scope functionality is implemented;
* all established M1 business rules are covered;
* automated tests pass;
* negative inventory is prevented;
* historical inventory movements are preserved;
* product activation/deactivation works;
* inventory availability can be identified;
* no M2+ functionality has been introduced;
* manual validation has been completed;
* the user has explicitly approved the milestone.

---

# 36. Next Documents

Before implementation begins, M1 should have the following supporting documents:

```text
docs/milestones/m1-products-inventory/
│
├── specification.md
├── use-cases.md
├── acceptance-criteria.md
└── validation.md
```

This document defines **what M1 must do**.

The other documents define:

* `use-cases.md` → how the user performs the operations;
* `acceptance-criteria.md` → objective conditions that determine whether each behavior is correct;
* `validation.md` → manual verification performed after implementation.

---

# 37. Traceability

M1 follows the project documentation chain:

```text
business-contract.md
        ↓
M1 specification.md
        ↓
use-cases.md
        ↓
acceptance-criteria.md
        ↓
implementation
        ↓
automated tests
        ↓
validation.md
```

The implementation must not introduce business behavior that cannot be traced to an established requirement or an explicitly approved technical decision.

---

# 38. M1 Guiding Principle

M1 should provide a reliable and simple foundation for the rest of the system.

It should answer three basic questions:

```text
What products do we have?
        ↓
How much physical inventory do we have?
        ↓
What happened to that inventory?
```

Nothing beyond what is necessary to answer those questions belongs in M1.
