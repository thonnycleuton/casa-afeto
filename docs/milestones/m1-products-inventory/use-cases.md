# M1 — Products & Inventory Use Cases

**Document version:** 0.1
**Status:** Ready for implementation
**Milestone:** M1 — Products & Inventory

---

# 1. Purpose

This document describes the user-facing use cases for M1 — Products & Inventory.

It translates the M1 specification into concrete operational flows.

These use cases describe:

* who performs an operation;
* what the user wants to accomplish;
* the normal flow;
* relevant alternative flows;
* expected business behavior.

They do not prescribe:

* API endpoints;
* database implementation;
* frontend architecture;
* framework-specific behavior;
* internal service structure.

Those are implementation concerns.

---

# 2. Actors

M1 has one primary actor:

### Casa Afeto Operator

The person responsible for managing products and physical inventory.

The operator may:

* register products;
* maintain product information;
* activate/deactivate products;
* register inventory entries;
* correct inventory;
* inspect inventory;
* inspect inventory history.

No separate roles or permission model are required by M1.

---

# 3. Use Case Overview

```text
Product Management
│
├── UC-M1-01 Create Product
├── UC-M1-02 Edit Product
├── UC-M1-03 Activate Product
├── UC-M1-04 Deactivate Product
├── UC-M1-05 List Products
└── UC-M1-06 Search Products

Inventory Management
│
├── UC-M1-07 Add Inventory
├── UC-M1-08 Adjust Inventory
├── UC-M1-09 View Inventory Balance
├── UC-M1-10 View Inventory History
└── UC-M1-11 Check Inventory Availability
```

---

# 4. UC-M1-01 — Create Product

## Goal

Allow the operator to register a new product.

## Preconditions

None.

## Main Flow

1. The operator opens the product management area.
2. The operator chooses to create a product.
3. The system requests the product information.
4. The operator enters the product name.
5. The operator selects or enters the base inventory unit.
6. The operator submits the product.
7. The system validates the required information.
8. The system creates the product.
9. The product is initially active.
10. The system confirms successful creation.

## Example

```text
Name: Chocolate
Base unit: UN
```

Result:

```text
Product: Chocolate
Unit: UN
Active: Yes
```

## Alternative Flows

### A1 — Missing name

If the operator does not provide a product name:

1. The system rejects the operation.
2. The system indicates that the product name is required.
3. No product is created.

### A2 — Invalid unit

If the base inventory unit is invalid:

1. The system rejects the operation.
2. The system informs the operator.
3. No product is created.

## Postconditions

A new active product exists.

No inventory movement is created.

---

# 5. UC-M1-02 — Edit Product

## Goal

Allow the operator to update product information.

## Preconditions

* The product exists.

## Main Flow

1. The operator opens the product.
2. The system displays its current information.
3. The operator changes editable information.
4. The operator saves the changes.
5. The system validates the changes.
6. The system persists the updated product.
7. The system confirms the update.

## Example

```text
Before:
Chocolate

After:
Premium Chocolate
```

## Alternative Flows

### A1 — Product does not exist

The system reports that the requested product could not be found.

No changes are made.

### A2 — Invalid information

The system rejects the change and explains the validation problem.

The previous product information remains unchanged.

## Important Behavior

Editing a product must not alter its historical inventory movements.

For example:

```text
Inventory history:

+20 Chocolate
-3 Chocolate

Rename:
Chocolate → Premium Chocolate

History remains associated with the same product.
```

---

# 6. UC-M1-03 — Activate Product

## Goal

Make an inactive product available for new operations.

## Preconditions

* The product exists.
* The product is currently inactive.

## Main Flow

1. The operator opens the inactive product.
2. The operator chooses to activate it.
3. The system changes the product state to active.
4. The system confirms the operation.

## Postconditions

The product is active.

Its inventory and historical movements remain unchanged.

---

# 7. UC-M1-04 — Deactivate Product

## Goal

Prevent a product from being selected for new operational activities.

## Preconditions

* The product exists.
* The product is currently active.

## Main Flow

1. The operator opens the product.
2. The operator chooses to deactivate it.
3. The system changes the product state to inactive.
4. The system confirms the operation.

## Important Behavior

Deactivation does not:

* delete the product;
* delete inventory;
* delete inventory movements;
* change the inventory balance.

Example:

```text
Chocolate
Active: Yes
Inventory: 15

Deactivate

Chocolate
Active: No
Inventory: 15
```

## Postconditions

The product is inactive.

Future operations requiring an active product must not allow it to be selected.

---

# 8. UC-M1-05 — List Products

## Goal

Allow the operator to view registered products.

## Preconditions

None.

## Main Flow

1. The operator opens the product list.
2. The system retrieves the available products.
3. The system displays each product.
4. The operator can identify at least:

   * name;
   * base unit;
   * active/inactive state;
   * current inventory balance.

## Important Behavior

Inactive products remain visible in product management.

Deactivation does not remove them from historical or administrative views.

## Empty State

If no products exist, the system should clearly indicate that no products have been registered.

---

# 9. UC-M1-06 — Search Products

## Goal

Allow the operator to find a product by name.

## Preconditions

None.

## Main Flow

1. The operator opens the product list.
2. The operator enters a search term.
3. The system searches product names.
4. The system displays matching products.

## Example

Search:

```text
choc
```

Possible result:

```text
Chocolate
Chocolate Premium
Chocolate Branco
```

## Alternative Flow

### A1 — No results

The system informs the operator that no matching products were found.

No error is generated merely because the search has no matches.

---

# 10. UC-M1-07 — Add Inventory

## Goal

Record a positive physical inventory entry.

## Preconditions

* The product exists.
* The product is active.

## Main Flow

1. The operator selects a product.
2. The system displays the current inventory balance.
3. The operator chooses to add inventory.
4. The operator enters the quantity.
5. The operator submits the operation.
6. The system validates the quantity.
7. The system creates an inventory entry movement.
8. The system updates or derives the inventory balance.
9. The system displays the resulting balance.

## Example

Current:

```text
Chocolate = 5 UN
```

Operator enters:

```text
+20 UN
```

Result:

```text
Chocolate = 25 UN
```

Movement history contains:

```text
ENTRY +20
```

## Alternative Flows

### A1 — Invalid quantity

If the quantity is invalid:

1. The system rejects the operation.
2. No movement is created.
3. The inventory remains unchanged.

### A2 — Product not found

The system rejects the operation.

No movement is created.

### A3 — Inactive product

The system does not allow a normal inventory entry for an inactive product.

The operation is rejected without creating a movement.

## Postconditions

A new positive inventory movement exists.

The product's inventory balance has increased by the specified quantity.

---

# 11. UC-M1-08 — Adjust Inventory

## Goal

Correct the recorded inventory to match the physical quantity.

## Preconditions

* The product exists.
* The product is active.

## Main Flow

1. The operator selects a product.
2. The system displays the current balance.
3. The operator chooses to adjust inventory.
4. The operator specifies the quantity adjustment.
5. The operator submits the adjustment.
6. The system calculates the resulting balance.
7. The system verifies that the resulting balance will not be negative.
8. The system creates an adjustment movement.
9. The system updates or derives the balance.
10. The system displays the resulting balance.

## Positive Adjustment Example

Current:

```text
Chocolate = 17
```

Physical count:

```text
Chocolate = 19
```

Adjustment:

```text
+2
```

Result:

```text
Chocolate = 19
```

## Negative Adjustment Example

Current:

```text
Chocolate = 20
```

Physical count:

```text
Chocolate = 17
```

Adjustment:

```text
-3
```

Result:

```text
Chocolate = 17
```

## Alternative Flows

### A1 — Adjustment would create negative inventory

Current:

```text
Chocolate = 2
```

Requested adjustment:

```text
-3
```

The system must:

1. reject the adjustment;
2. inform the operator that the resulting inventory would be negative;
3. create no movement;
4. preserve the current balance.

Result:

```text
Chocolate = 2
```

### A2 — Invalid quantity

The system rejects the operation.

No movement is created.

### A3 — Product not found

The system rejects the operation.

No movement is created.

### A4 — Inactive product

The system does not allow the normal adjustment operation for an inactive product.

No movement is created.

## Important Behavior

An adjustment never rewrites an earlier inventory movement.

Example:

```text
History:

+20
-3
```

If another correction of `-2` is required:

```text
History:

+20
-3
-2
```

The existing movements remain unchanged.

---

# 12. UC-M1-09 — View Inventory Balance

## Goal

Allow the operator to see the current physical inventory of a product.

## Preconditions

* The product exists.

## Main Flow

1. The operator selects a product.
2. The system calculates or retrieves its current balance.
3. The system displays:

   * product;
   * base unit;
   * current quantity.

## Example

```text
Product: Chocolate
Unit: UN
Available inventory: 17
```

## Empty Inventory

If no inventory movement exists:

```text
Available inventory: 0
```

The absence of inventory must not be treated as an error.

---

# 13. UC-M1-10 — View Inventory History

## Goal

Allow the operator to understand how the current inventory balance was formed.

## Preconditions

* The product exists.

## Main Flow

1. The operator selects a product.
2. The operator opens inventory history.
3. The system retrieves the product's inventory movements.
4. The system displays the movements chronologically.
5. The operator can identify the effect of each movement.

## Example

```text
Chocolate

Date        Type          Quantity
-----------------------------------
10/09       ENTRY          +20
11/09       ADJUSTMENT      -3
12/09       ADJUSTMENT      +2
```

Current balance:

```text
19
```

## Important Behavior

Historical movements must not disappear because of later corrections.

The system must preserve the auditability of inventory changes.

---

# 14. UC-M1-11 — Check Inventory Availability

## Goal

Determine whether a product has sufficient inventory for a requested quantity.

## Preconditions

* The product exists.

## Main Flow

1. A future operation requests a quantity for a product.
2. The system obtains the current inventory balance.
3. The system compares available quantity with requested quantity.
4. The system reports the result.

## Example — Available

```text
Available: 10
Required:  4

Result:
Available
Shortage: 0
```

## Example — Insufficient

```text
Available: 2
Required: 5

Result:
Insufficient inventory
Shortage: 3
```

## Important Behavior

An insufficient inventory result does not modify inventory.

It does not create a negative movement.

It does not prevent the product from being included in a future basket or draft sale.

The future sale confirmation process will determine whether the required inventory exists before deducting it.

---

# 15. Cross-Use-Case Business Rules

The following rules apply across multiple use cases.

## 15.1 No Negative Physical Inventory

No use case may create an inventory movement that produces a negative physical balance.

```text
Current = 2
Requested decrease = 3

Result:
Rejected
```

---

## 15.2 Historical Movements Are Preserved

No normal product or inventory operation may rewrite previous inventory movements.

Corrections are represented by new movements.

---

## 15.3 Product Deactivation Is Non-Destructive

Deactivating a product does not:

* delete the product;
* delete inventory;
* delete history;
* change the current balance.

---

## 15.4 Insufficient Inventory Is Not the Same as Invalid Product

A product with insufficient inventory remains a valid product.

Example:

```text
Product exists: Yes
Active: Yes
Inventory: 0
```

The product is still valid.

Its availability simply indicates:

```text
Insufficient inventory
```

---

## 15.5 Inventory Is Not Reserved

M1 does not reserve inventory.

Checking availability does not alter inventory.

Creating a product does not alter inventory.

The future sale confirmation operation will be responsible for the actual deduction.

---

# 16. Common Operational Scenario

The following scenario combines the main M1 use cases.

## Scenario

Casa Afeto starts with no Chocolate inventory.

### Step 1 — Create Product

```text
Chocolate
Unit: UN
```

Inventory:

```text
0
```

### Step 2 — Add Inventory

Operator receives 20 units.

```text
+20
```

Inventory:

```text
20
```

### Step 3 — Physical Correction

Operator counts the inventory and finds only 17 units.

```text
-3
```

Inventory:

```text
17
```

History:

```text
+20
-3
```

### Step 4 — Check Availability

A future basket requires:

```text
20 Chocolate
```

System reports:

```text
Available: 17
Required: 20
Shortage: 3
```

Inventory remains:

```text
17
```

### Step 5 — Replenish

Operator receives 10 additional units.

```text
+10
```

Inventory:

```text
27
```

### Step 6 — Check Again

Required:

```text
20
```

Available:

```text
27
```

Result:

```text
Available
```

### Step 7 — Deactivate Product

Operator decides the product should no longer be used.

Product:

```text
Active: No
```

Inventory remains:

```text
27
```

History remains intact.

---

# 17. Invalid Operation Example

The following operation must never be allowed.

Current:

```text
Inventory = 5
```

Operator requests:

```text
Adjustment = -8
```

The system calculates:

```text
5 - 8 = -3
```

Because physical inventory cannot become negative:

```text
Operation = Rejected
```

The resulting state remains:

```text
Inventory = 5
```

No `-8` movement is created.

---

# 18. Interaction With Future Milestones

M1 establishes inventory behavior used by later milestones.

### M2 — Baskets

M2 may:

* select products;
* inspect availability;
* warn about insufficient inventory.

M2 must not deduct inventory.

### M4 — Sales

M4 may create draft sales containing products with insufficient inventory.

M4 must not deduct inventory merely because a sale exists.

### M5 — Payments

M5 will use the M1 inventory behavior when confirming sales.

Before confirmation:

```text
Check availability
```

If sufficient:

```text
Deduct inventory
```

If insufficient:

```text
Do not create negative inventory
Confirmation cannot proceed
```

M1 itself does not implement these future workflows.

---

# 19. Error Behavior Principles

Errors should be presented in business terms.

Prefer:

```text
"Insufficient inventory. Available: 2 UN. Required: 5 UN."
```

over:

```text
"Constraint violation: inventory_balance >= 0"
```

Technical details should be logged or handled internally when appropriate.

The user should receive enough information to understand what action is required.

---

# 20. Use Case Traceability

| Use Case                              | Specification Section  | Business Rules               |
| ------------------------------------- | ---------------------- | ---------------------------- |
| UC-M1-01 Create Product               | Product                | Product requirements         |
| UC-M1-02 Edit Product                 | Product Editing        | Historical preservation      |
| UC-M1-03 Activate Product             | Product Activation     | Product activation           |
| UC-M1-04 Deactivate Product           | Product Activation     | Non-destructive deactivation |
| UC-M1-05 List Products                | Product Listing        | —                            |
| UC-M1-06 Search Products              | Product Search         | —                            |
| UC-M1-07 Add Inventory                | Inventory Entry        | INV-001                      |
| UC-M1-08 Adjust Inventory             | Inventory Adjustment   | INV-001, INV-002, INV-006    |
| UC-M1-09 View Inventory Balance       | Inventory Balance      | INV-001                      |
| UC-M1-10 View Inventory History       | Movement History       | INV-002                      |
| UC-M1-11 Check Inventory Availability | Inventory Availability | INV-003, INV-006             |

---

# 21. Implementation Boundary

These use cases define observable business behavior.

They do not require a particular technical implementation.

The implementation must not introduce additional business behavior simply because a technical framework makes it convenient.

If a technical decision changes one of these behaviors, the agent must identify the conflict before implementation.

---

# 22. M1 Use Case Completion

The use-case documentation is complete when all in-scope M1 operations have:

* a defined actor;
* a defined goal;
* defined preconditions where applicable;
* a normal flow;
* relevant alternative/error flows;
* defined postconditions where applicable;
* traceability to the M1 specification.

The next artifact is:

```text
docs/milestones/m1-products-inventory/acceptance-criteria.md
```

Acceptance criteria will translate these use cases into objective, testable conditions that determine whether the implementation is correct.
