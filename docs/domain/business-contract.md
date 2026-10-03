# Casa Afeto — Business Contract

**Document version:** 0.3
**Status:** Active

---

## 1. Purpose

This document describes the current business behavior of Casa Afeto that must guide the development of the Sales Management System.

It represents business decisions that have already been established.

It is not an implementation specification.

When implementation details are required, milestone specifications and architecture decisions should define them without changing the business behavior documented here.

---

# 2. Business Overview

Casa Afeto sells personalized breakfast baskets and gift baskets.

The operational flow is approximately:

```text
Customer contacts Casa Afeto
        ↓
Chooses a basket
        ↓
Basket is customized if necessary
        ↓
Delivery date is agreed
        ↓
Payment is received
        ↓
Basket is prepared
        ↓
Basket is delivered
```

The system will support this operation through:

* Products
* Inventory
* Basket Templates
* Baskets
* Customers
* Sales
* Payments

---

# 3. Customer

A **Customer** is the person who makes the purchase.

A customer may purchase one or more baskets over time.

The customer is associated with a Sale.

Recipient information does not need to be represented as a separate Customer or Person entity during the initial implementation.

---

# 4. Product

A **Product** is an item that can be used as part of a basket.

Examples include:

* cereal bars;
* chocolate;
* juice;
* cake;
* coffee;
* mugs;
* cards;
* packaging.

A product has a base inventory unit.

Examples:

```text
Chocolate → UN
Juice     → UN
Coffee    → UN
```

The purchase/commercial unit may differ from the inventory unit.

For example:

```text
Purchase:
1 box of cereal bars

Box:
24 units

Inventory:
+24 UN
```

The conversion factor may vary depending on the acquisition.

---

# 5. Product Activation

Products can be activated or deactivated.

A deactivated product should not be selectable for new operational activities where active products are required.

Deactivation does not delete historical information involving the product.

---

# 6. Product Cost

A product may be acquired at different prices over time.

Example:

```text
Normal acquisition:
Cereal bar = R$ 2.50 / unit

Special acquisition:
Cereal bar = R$ 1.80 / unit
```

Historical acquisition costs must not be overwritten.

Product cost therefore belongs to the acquisition/inventory context rather than being treated as a single permanent property of the Product.

The future inventory-lot model should allow different quantities of the same product to have different acquisition costs.

---

# 7. Purchase

A **Purchase** represents an acquisition of products by Casa Afeto.

A purchase contains one or more purchase items.

A purchase item may use a commercial unit different from the product's inventory unit.

Example:

```text
Purchase item:
1 box

Conversion:
1 box = 24 units

Inventory quantity:
24 units
```

The actual acquisition price must be preserved.

Purchase management is not part of the initial Phase 1 implementation.

---

# 8. Inventory

Inventory represents the physical stock available for products.

Conceptually, inventory is movement-based.

Examples of movements include:

```text
Purchase / Entry       +20
Sale / Consumption      -3
Adjustment              -2
```

The system must preserve inventory movement history.

The current balance can be derived from the relevant inventory movements.

---

# 9. Inventory Correction

Inventory may need to be corrected when the system's recorded quantity differs from the physical quantity.

Corrections must preserve historical information.

The system must not rewrite previous inventory movements to make the history appear different.

Instead, a new adjustment movement should represent the correction.

Example:

```text
Recorded balance: 20
Physical balance: 17

Adjustment:
-3
```

The original movements remain unchanged.

---

# 10. Inventory Availability

Inventory availability is relevant when products are used in baskets and sales.

A product may be selected for a basket even when the current available inventory is insufficient.

However, the shortage must be clearly visible to the user.

Example:

```text
Inventory:
Chocolate = 0

Basket:
Chocolate × 2

Result:
Allowed

Warning:
Insufficient inventory — 2 units required.
```

This allows Casa Afeto to register the customer's intended basket before replenishing the missing products.

---

# 11. Negative Inventory Policy

The system must **not allow physical inventory to become negative**.

An inventory movement must not be created if it would cause the available inventory balance of a product to become negative.

For example:

```text
Inventory:
Chocolate = 1

Required consumption:
Chocolate × 3
```

The system must not create:

```text
Chocolate = -2
```

Instead, the shortage must be identified.

The distinction between commercial planning and physical inventory is important.

### Basket/Sale composition

A basket or sale may contain a product for which there is insufficient inventory.

This represents a future requirement.

### Inventory movement

A physical inventory deduction may only occur when sufficient inventory exists.

Therefore:

```text
Basket creation
    ↓
May contain insufficient-stock product
    ↓
Warning shown
    ↓
Inventory remains unchanged
```

and:

```text
Sale confirmation
    ↓
Required inventory checked
    ↓
Sufficient stock?
    ├── Yes → deduct inventory
    └── No  → confirmation blocked
```

A sale cannot be confirmed while its required inventory cannot be fulfilled.

This policy does not require the system to implement automatic replenishment.

Future functionality may identify products that need to be purchased to fulfill pending sales.

---

# 12. Inventory Lots

The future inventory model should support multiple lots of the same product.

Different lots may have different:

* acquisition costs;
* quantities;
* expiration dates.

Example:

```text
Chocolate

Lot A
Quantity: 10
Unit cost: R$ 2.50
Expiration: 2026-11-10

Lot B
Quantity: 20
Unit cost: R$ 1.80
Expiration: 2026-10-20
```

The current provisional business policy is to prefer the lot with the nearest expiration when selecting stock for consumption.

This is conceptually similar to FEFO.

This policy is provisional and may be changed as the business evolves.

Lot management is not part of the initial Phase 1 implementation.

---

# 13. Basket Template

A **Basket Template** represents a reusable standard composition for a basket.

A template contains products and quantities.

Example:

```text
Breakfast Classic

Coffee × 1
Juice × 1
Chocolate × 2
Cake × 1
```

Templates can be activated or deactivated.

---

# 14. Basket

A **Basket** is a concrete basket prepared for a particular sale.

A basket may:

* be created from a template;
* be created without a template;
* have its composition customized;
* contain multiple quantities of the same product.

Example:

```text
Chocolate × 3
Juice × 1
Cake × 1
```

A basket is not required to maintain the same composition as its template.

---

# 15. Basket and Template Independence

When a basket is created from a template, the basket receives its own concrete composition.

Future changes to the template must not modify existing baskets.

Example:

```text
Template:
Chocolate × 2
Juice × 1

        ↓

Basket:
Chocolate × 2
Juice × 1

        ↓ template changes

Template:
Chocolate × 1
Juice × 2
```

The existing basket remains:

```text
Chocolate × 2
Juice × 1
```

---

# 16. Basket Customization

A concrete basket may be customized after creation.

Customization may include:

* adding a product;
* removing a product;
* changing quantity;
* substituting a product.

Customization may be required because of:

* customer preference;
* product availability;
* operational decisions.

A basket may contain a product even when the current inventory is insufficient, provided the shortage is visible.

---

# 17. Basket Without Template

A basket may be created without using a Basket Template.

This allows Casa Afeto to create personalized or exceptional baskets without first creating a reusable template.

---

# 18. Basket Cost

The cost of a basket is determined from the products and quantities composing it.

Because product acquisition costs may vary, the cost calculation should eventually consider the relevant inventory/acquisition context.

The detailed lot-selection and costing strategy will be specified when inventory lots are implemented.

---

# 19. Basket Pricing

Casa Afeto currently uses approximately 2× product cost as a common pricing reference.

This is a **suggestion**, not a mandatory pricing rule.

Conceptually:

```text
Basket Cost
    ↓
Suggested Price
    ↓
Final Selling Price
```

The user may manually define the final selling price.

Example:

```text
Cost:             R$ 85
Suggested price:  R$ 170

Possible final price:
R$ 155
R$ 170
R$ 185
```

The final selling price is controlled by the user.

If basket composition changes, cost and suggested price should be recalculated.

The final price may remain manually controlled/overridden.

---

# 20. Sale

A **Sale** represents a commercial transaction with a Customer.

A sale contains:

* one Customer;
* one or more Baskets;
* sale-level information;
* payment information associated with the sale.

A sale must contain at least one basket.

A sale may contain multiple baskets.

---

# 21. Basket Delivery Information

Each basket may have its own delivery/recipient information.

This includes, as required:

* recipient;
* delivery address;
* delivery date;
* relevant notes.

Multiple baskets in the same sale may share the same address.

The recipient does not need to be modeled as an independent Customer entity during the initial implementation.

---

# 22. Sale Lifecycle

The operational sale lifecycle is represented by statuses.

The initial status model is:

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

A sale may also become:

```text
CANCELLED
```

The exact implementation of status transitions belongs to the relevant milestone specification.

The statuses represent operational state and should not be confused with payment state.

---

# 23. Draft Sale

A draft sale represents a sale that is being prepared but has not yet been confirmed.

A draft sale may be changed.

Creating a draft sale does not deduct inventory.

---

# 24. Sale Confirmation

A sale is confirmed when the required business conditions are satisfied.

The payment requirement is:

> A sale is confirmed when at least 50% of its total value has been paid.

Example:

```text
Sale total: R$ 200

Paid:
R$ 100

Paid percentage:
50%

Result:
Sale may be confirmed.
```

Inventory availability is also required.

A sale cannot be confirmed if the required inventory cannot be fulfilled.

Therefore:

```text
Confirmation requirements

At least 50% paid
        AND
Required inventory available
        ↓
Sale may be confirmed
```

---

# 25. Inventory Deduction on Sale Confirmation

When a sale is confirmed, the required inventory is deducted.

Example:

```text
Before confirmation:

Chocolate = 20
Juice     = 8

Sale:

Chocolate × 2
Juice × 1

After confirmation:

Chocolate = 18
Juice     = 7
```

The deduction represents the physical consumption/commitment of inventory for the confirmed sale.

The system must never create a movement that causes physical inventory to become negative.

---

# 26. Changes After Confirmation

A confirmed sale may be modified.

When the basket composition changes after confirmation, inventory must be adjusted according to the difference between the original and new compositions.

Example:

```text
Original:

Chocolate × 2
Juice × 1

New:

Biscuit × 2
Juice × 1
```

Inventory adjustment:

```text
Chocolate +2
Biscuit   -2
```

The original inventory movement remains in history.

The system must not rewrite the original movement.

If the new composition cannot be fulfilled because inventory is insufficient, the system must not create a negative inventory movement.

---

# 27. Sale Cancellation

A confirmed sale may later be cancelled.

A cancelled sale must not be deleted.

Its historical information must remain available.

Cancellation does not automatically imply that 100% of the previously deducted inventory returns to stock.

The physical situation must determine what actually happened.

For example:

```text
Product returned physically
    → may be added back to inventory

Product consumed
    → remains consumed

Product lost/damaged
    → may require an adjustment
```

Detailed loss, return, and expiration behavior is outside the initial Phase 1 scope.

---

# 28. Payment

The system supports the following payment methods:

* PIX;
* Card.

A sale may have one or more payment records.

Payment information must be tracked separately from the operational sale status.

---

# 29. Payment Proof

A payment may have associated proof of payment.

The proof allows Casa Afeto to document the payment received.

The exact storage and file-handling behavior will be defined by the relevant implementation specification.

---

# 30. Payment and Sale Status Separation

Payment status and sale status are separate concepts.

For example:

```text
Sale:
CONFIRMED

Payment:
50% paid
50% outstanding
```

A sale can therefore be confirmed while still having an outstanding balance.

---

# 31. Delivery Payment Rule

The remaining balance must be fully paid before delivery.

Therefore:

```text
Confirmed
    ↓
Outstanding balance
    ↓
Remaining payment
    ↓
100% paid
    ↓
Delivery
```

A sale must not be delivered while an outstanding balance remains.

---

# 32. Individual Product Sales

Individual product sales are outside the initial scope.

The current sales model is centered on baskets.

The system should not implement a separate product-sale workflow unless a concrete business requirement is introduced.

---

# 33. Internally Produced Products

Casa Afeto may produce products internally, such as cakes.

The business does not currently have a sufficiently defined production process to formalize this area.

Future production functionality may involve:

* recipes;
* ingredients;
* production quantities;
* production costs;
* expiration;
* production inventory movements.

These capabilities are outside the initial scope.

The current architecture should not prematurely implement them.

---

# 34. Losses, Breakage, Expiration, and Internal Use

Products may eventually be:

* lost;
* damaged;
* expired;
* consumed internally;
* used for reasons other than a sale.

The business rules for these situations are not yet fully defined.

The inventory model should allow future movement types to represent these situations.

Detailed workflows should be introduced only when the corresponding business requirements are defined.

---

# 35. Affective Dates

Casa Afeto intends to eventually maintain relevant dates associated with customers or recipients.

Examples:

* birthday;
* wedding anniversary;
* other important dates.

A future feature may use these dates to support proactive customer contact and reminders.

This functionality is outside the initial Phase 1 scope.

---

# 36. Established Business Rules

The following rules have been explicitly established.

### BASKET-001 — Basket Creation

A basket may be created from a template or without a template.

### BASKET-002 — Multiple Product Quantities

A basket may contain multiple quantities of the same product.

### BASKET-003 — Basket/Template Independence

Changing a Basket Template must not modify existing baskets created from that template.

### BASKET-004 — Basket Customization

A concrete basket may be customized after creation.

### SALE-001 — Sale Basket Requirement

A sale must contain at least one basket.

### SALE-002 — Multiple Baskets per Sale

A sale may contain multiple baskets.

### SALE-003 — Confirmed Sale Modification

A confirmed sale may be modified.

### SALE-004 — Cancelled Sale Preservation

A cancelled sale must be preserved and not deleted.

### SALE-005 — Inventory Delta After Confirmation

Changes to a confirmed sale must adjust inventory according to the composition delta.

### PAY-001 — Supported Payment Methods

The supported payment methods are PIX and Card.

### PAY-002 — Sale Confirmation Threshold

A sale may be confirmed when at least 50% of its total value has been paid.

### PAY-003 — Full Payment Before Delivery

A sale must be fully paid before delivery.

### INV-001 — Movement-Based Inventory

Inventory changes are represented through inventory movements.

### INV-002 — Historical Inventory Preservation

Inventory corrections must preserve the original movement history.

### INV-003 — Insufficient Stock May Be Selected

A product with insufficient inventory may be selected for a basket or sale before confirmation, provided the shortage is clearly indicated.

### INV-004 — Inventory Deduction on Confirmation

A confirmed sale generates the required inventory deductions.

### INV-005 — Inventory Delta for Confirmed Sale Changes

Changes to a confirmed sale generate inventory adjustments based on the composition delta.

### INV-006 — No Negative Physical Inventory

The system must not create an inventory movement that causes the available physical inventory balance of a product to become negative.

### INV-007 — Confirmation Requires Available Inventory

A sale cannot be confirmed while its required inventory cannot be fulfilled.

---

# 37. Open Business Decisions

The following topics remain intentionally unresolved and should not be converted into assumptions by the implementation.

### Inventory Cost/Lot Selection

The provisional strategy is to prefer the lot with the nearest expiration when consuming inventory.

The exact costing implementation will be defined when lot management is introduced.

### Purchase Management

Detailed purchase workflows, supplier information, purchase documents, and related fields have not yet been defined.

### Internal Production

The production process for internally made products has not yet been defined.

### Loss and Expiration Handling

Detailed workflows for loss, damage, expiration, and internal consumption have not yet been defined.

---

# 38. Future Business Opportunities

The following capabilities may be considered after the core operational system is stable:

* purchase management;
* inventory lots;
* expiration tracking;
* FEFO-based inventory consumption;
* expiration warnings;
* replenishment management;
* affective dates;
* customer reminders;
* communication integrations;
* internal production;
* recipes;
* advanced pricing;
* customer relationship management;
* operational dashboards;
* advanced reporting.

These opportunities must not be implemented merely because they appear in this document.

Each future capability requires its own business decision and implementation scope.

---

# 39. Change Policy

This document represents the current business understanding.

Business rules may change as Casa Afeto uses the system and discovers new requirements.

When a business rule changes:

1. The change must be explicitly identified.
2. This document must be updated.
3. Affected milestone specifications must be reviewed.
4. Existing implementation must be evaluated for impact.
5. Tests must be updated where necessary.
6. Historical data must be considered before destructive changes are introduced.

The agent must not silently change business behavior based on assumptions.

---

# 40. Guiding Business Principle

The system exists to support the real operation of Casa Afeto.

Therefore:

> **Business behavior must be explicit, historical information must be preserved, and the system should remain simple enough to evolve as the business learns.**

The system should model what Casa Afeto has decided to do today without prematurely implementing everything Casa Afeto may want to do in the future.
