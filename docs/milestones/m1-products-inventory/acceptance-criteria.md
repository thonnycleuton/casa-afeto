# M1 — Products & Inventory Acceptance Criteria

**Document version:** 0.1
**Status:** Ready for implementation
**Milestone:** M1 — Products & Inventory

---

# 1. Purpose

This document defines the objective acceptance criteria for M1 — Products & Inventory.

The criteria translate the M1 specification and use cases into observable, testable conditions.

A criterion is considered satisfied only when the expected behavior can be demonstrated through automated tests and/or manual validation.

The implementation must satisfy these criteria without introducing behavior outside the approved M1 scope.

---

# 2. Acceptance Rules

## AC-01 — Product Creation

**Given** no product exists with the submitted identity
**When** the operator creates a product with a valid name and base inventory unit
**Then** the system creates the product
**And** the product is active
**And** its inventory balance is zero
**And** no inventory movement is created.

---

## AC-02 — Product Name Is Required

**Given** the operator is creating a product
**When** the operator submits the product without a valid name
**Then** the system rejects the operation
**And** no product is created.

---

## AC-03 — Product Base Unit Is Required

**Given** the operator is creating a product
**When** the operator submits the product without a valid base inventory unit
**Then** the system rejects the operation
**And** no product is created.

---

## AC-04 — Product Editing

**Given** an existing product
**When** the operator changes valid editable product information
**Then** the product is updated
**And** its identity remains unchanged
**And** existing inventory movements remain associated with the same product.

---

## AC-05 — Product Activation

**Given** an inactive product
**When** the operator activates the product
**Then** the product becomes active
**And** its inventory balance remains unchanged
**And** its inventory history remains unchanged.

---

## AC-06 — Product Deactivation

**Given** an active product
**When** the operator deactivates the product
**Then** the product becomes inactive
**And** its inventory balance remains unchanged
**And** its inventory history remains unchanged
**And** the product is not available for new operations requiring an active product.

---

## AC-07 — Deactivation Does Not Delete Historical Data

**Given** a product with inventory history
**When** the product is deactivated
**Then** the product remains accessible in administrative/history contexts
**And** its inventory movements remain available
**And** its inventory balance remains unchanged.

---

# 3. Product Listing and Search

## AC-08 — Product Listing

**Given** multiple products exist
**When** the operator opens the product list
**Then** the system displays the products
**And** each product exposes at least its name, base unit, active state, and current inventory balance.

---

## AC-09 — Inactive Products Remain Visible

**Given** an inactive product exists
**When** the operator views the product management list
**Then** the inactive product remains visible
**And** its inactive state is identifiable.

---

## AC-10 — Product Search

**Given** products exist
**When** the operator searches using part or all of a product name
**Then** the system returns matching products according to the defined search behavior.

---

## AC-11 — Search With No Results

**Given** no product matches the submitted search
**When** the operator performs the search
**Then** the system returns an empty result
**And** the system does not report this as an application error.

---

# 4. Inventory Entry

## AC-12 — Add Inventory

**Given** an active product exists with a current balance
**When** the operator adds a valid positive quantity
**Then** an inventory entry movement is created
**And** the product balance increases by that quantity.

Example:

```text
Before: 5
Entry: +20
After: 25
```

---

## AC-13 — Add Inventory to Product With Zero Balance

**Given** an active product exists with no inventory
**When** the operator adds 20 units
**Then** the balance becomes 20
**And** exactly one corresponding inventory movement exists.

---

## AC-14 — Invalid Inventory Entry

**Given** an operator is adding inventory
**When** the submitted quantity is invalid
**Then** the operation is rejected
**And** no inventory movement is created
**And** the previous balance remains unchanged.

---

## AC-15 — Inventory Entry Requires an Existing Product

**Given** no product exists for the requested product reference
**When** the operator attempts to add inventory
**Then** the operation is rejected
**And** no inventory movement is created.

---

## AC-16 — Inactive Product Cannot Receive Normal Inventory Entry

**Given** a product is inactive
**When** the operator attempts to perform a normal inventory entry
**Then** the operation is rejected
**And** no inventory movement is created
**And** the existing inventory balance remains unchanged.

---

# 5. Inventory Adjustment

## AC-17 — Positive Inventory Adjustment

**Given** an active product has a current balance of 17
**When** the operator applies an adjustment of +2
**Then** an adjustment movement is created
**And** the resulting balance is 19.

---

## AC-18 — Negative Inventory Adjustment

**Given** an active product has a current balance of 20
**When** the operator applies an adjustment of -3
**Then** an adjustment movement is created
**And** the resulting balance is 17.

---

## AC-19 — Adjustment Cannot Create Negative Inventory

**Given** an active product has a current balance of 2
**When** the operator attempts an adjustment of -3
**Then** the operation is rejected
**And** no adjustment movement is created
**And** the balance remains 2.

---

## AC-20 — Adjustment Equal to Current Balance

**Given** an active product has a current balance of 5
**When** the operator applies an adjustment of -5
**Then** the operation is accepted
**And** an adjustment movement of -5 is created
**And** the resulting balance is 0.

Zero inventory is valid.

---

## AC-21 — Invalid Adjustment

**Given** an operator is performing an inventory adjustment
**When** the submitted adjustment is invalid
**Then** the operation is rejected
**And** no movement is created
**And** the existing balance remains unchanged.

---

## AC-22 — Adjustment Requires an Existing Product

**Given** no product exists for the requested product reference
**When** the operator attempts an inventory adjustment
**Then** the operation is rejected
**And** no inventory movement is created.

---

## AC-23 — Inactive Product Cannot Receive Normal Adjustment

**Given** a product is inactive
**When** the operator attempts a normal inventory adjustment
**Then** the operation is rejected
**And** no inventory movement is created
**And** the existing balance remains unchanged.

---

# 6. Inventory History

## AC-24 — Inventory Movement Is Preserved

**Given** a product has an inventory entry
**When** the operator views its inventory history
**Then** the entry is present
**And** its quantity and movement type are preserved.

---

## AC-25 — Multiple Movements Are Preserved

**Given** a product has the following movements:

```text
+20
-3
+5
```

**When** the operator views the inventory history
**Then** all three movements are present
**And** their quantities are unchanged
**And** their movement types are preserved.

---

## AC-26 — Corrections Create New Movements

**Given** a product has an existing inventory history
**When** the operator performs an inventory correction
**Then** a new adjustment movement is created
**And** previous movements remain unchanged.

---

## AC-27 — Inventory Balance Reflects Movement History

**Given** a product has movements:

```text
+20
-3
+5
-2
```

**When** the current inventory balance is calculated
**Then** the balance is 20.

---

# 7. Inventory Availability

## AC-28 — Product Is Available When Quantity Is Sufficient

**Given** a product has 10 units available
**When** availability is checked for 4 units
**Then** the system reports that the requested quantity is available
**And** the shortage is zero
**And** inventory is not modified.

---

## AC-29 — Product Is Insufficient When Quantity Is Not Sufficient

**Given** a product has 2 units available
**When** availability is checked for 5 units
**Then** the system reports insufficient inventory
**And** the shortage is 3 units
**And** inventory is not modified.

---

## AC-30 — Insufficient Inventory Does Not Create Negative Stock

**Given** a product has 2 units available
**When** availability is checked for 5 units
**Then** the system must not create a -3 inventory movement
**And** the inventory balance remains 2.

---

## AC-31 — Insufficient Inventory Does Not Invalidate the Product

**Given** an active product has zero inventory
**When** availability is checked for a positive quantity
**Then** the product remains valid
**And** the system reports insufficient inventory rather than treating the product as invalid.

---

# 8. Inventory Integrity

## AC-32 — Rejected Inventory Operation Has No Side Effects

**Given** an inventory operation is invalid
**When** the operation is rejected
**Then** no inventory movement is created
**And** the product balance remains unchanged
**And** existing inventory history remains unchanged.

---

## AC-33 — Inventory Balance Cannot Become Negative

**Given** any current inventory balance greater than or equal to zero
**When** an inventory operation would result in a negative balance
**Then** the operation is rejected
**And** the resulting balance remains non-negative.

---

## AC-34 — Zero Inventory Is Valid

**Given** a product has inventory
**When** the inventory is reduced exactly to zero
**Then** the operation is accepted
**And** the resulting balance is zero
**And** the product remains a valid active product.

---

## AC-35 — Historical Inventory Is Not Rewritten

**Given** a product has previous inventory movements
**When** a subsequent adjustment is performed
**Then** previous movements retain their original values
**And** the adjustment is represented by a new movement.

---

# 9. Product and Inventory Relationship

## AC-36 — Every Inventory Movement Belongs to a Product

**Given** an inventory movement is successfully created
**Then** it references an existing product
**And** the movement cannot exist without a valid product reference.

---

## AC-37 — Product Deactivation Does Not Change Inventory

**Given** an active product has a balance of 15
**When** the product is deactivated
**Then** the balance remains 15
**And** no inventory movement is created.

---

## AC-38 — Product Reactivation Does Not Change Inventory

**Given** an inactive product has a balance of 15
**When** the product is reactivated
**Then** the balance remains 15
**And** no inventory movement is created.

---

# 10. End-to-End Acceptance Scenario

## AC-39 — Complete M1 Operational Flow

**Given** the system has no Chocolate product

**When** the operator:

1. creates Chocolate with base unit `UN`;
2. adds 20 units;
3. applies an adjustment of -3;
4. checks the inventory balance;
5. checks availability for 20 units;
6. attempts an adjustment of -18;
7. views the movement history;
8. deactivates Chocolate;

**Then**:

```text
Product:
Chocolate
Active:
No

Inventory balance:
17 UN
```

**And** the history contains:

```text
ENTRY       +20
ADJUSTMENT   -3
```

**And** the rejected `-18` adjustment does not appear in history.

**And** the availability check for 20 units reports:

```text
Available: 17
Required: 20
Shortage: 3
```

**And** the product remains present in product management.

**And** the inventory remains 17.

---

# 11. Scope Acceptance

## AC-40 — No Future Inventory Features Are Required

M1 must not be considered incomplete because the system does not implement:

* purchases;
* purchase items;
* suppliers;
* inventory lots;
* expiration;
* FEFO;
* replenishment;
* loss management;
* production;
* reserved inventory;
* sales;
* payment;
* basket-related inventory deduction.

These features are explicitly outside the M1 scope.

---

# 12. Automated Test Expectations

Each acceptance criterion involving deterministic business behavior should be covered by automated tests where technically appropriate.

At minimum, automated tests must cover:

* product creation;
* product editing;
* activation/deactivation;
* inventory entry;
* positive adjustment;
* negative adjustment;
* zero balance;
* rejection of negative resulting inventory;
* movement history;
* balance calculation;
* availability checks;
* invalid operations having no side effects.

Tests should verify observable behavior rather than internal implementation structure.

---

# 13. Manual Validation Expectations

After automated tests pass, the operator must manually validate the main operational flow.

The manual validation must confirm:

* product creation;
* product visibility;
* inventory entry;
* inventory adjustment;
* inventory balance;
* movement history;
* insufficient inventory warning/state;
* negative inventory rejection;
* product deactivation;
* preservation of inventory after deactivation.

The detailed checklist belongs in:

```text
docs/milestones/m1-products-inventory/validation.md
```

---

# 14. Acceptance Decision

M1 is accepted only when:

1. All applicable acceptance criteria pass.
2. Automated tests pass.
3. No known regression is introduced.
4. Manual validation passes.
5. No unapproved business behavior has been introduced.
6. The implementation remains within M1 scope.
7. The user explicitly approves the milestone.

An implementation that merely compiles or passes its unit tests is not sufficient by itself.

The business behavior must also satisfy the acceptance criteria.

---

# 15. Traceability

The M1 documentation chain is:

```text
Business Contract
        ↓
M1 Specification
        ↓
M1 Use Cases
        ↓
M1 Acceptance Criteria
        ↓
Implementation
        ↓
Automated Tests
        ↓
Manual Validation
```

Every M1 business behavior should be traceable through this chain.

If implementation reveals a requirement that cannot be traced to an existing specification or approved decision, the agent must stop and clarify the requirement before expanding the scope.

---

# 16. Final Acceptance Principle

The implementation is correct when the documented business behavior is observable and verifiable.

> **If the acceptance criteria say it must happen, it must happen.**
>
> **If the acceptance criteria do not require it, M1 does not need to implement it.**
