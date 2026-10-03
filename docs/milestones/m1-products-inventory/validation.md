# Casa Afeto — M1 Manual Validation

**Milestone:** M1 — Products & Inventory
**Document:** Manual Validation
**Version:** 0.1
**Status:** Draft
**Depends on:** `specification.md`, `use-cases.md`, `acceptance-criteria.md`

---

## 1. Purpose

This document defines the manual validation procedure for M1 — Products & Inventory.

The purpose is to verify that the implemented system behaves correctly from the perspective of a Casa Afeto operator.

This document is intentionally operational.

It does not define new business rules. It provides a repeatable procedure for validating the rules already defined by:

* `docs/domain/business-contract.md`
* `docs/milestones/m1-products-inventory/specification.md`
* `docs/milestones/m1-products-inventory/use-cases.md`
* `docs/milestones/m1-products-inventory/acceptance-criteria.md`

---

## 2. Validation Principles

Manual validation must verify:

1. The expected business behavior works.
2. Invalid operations are rejected safely.
3. Inventory cannot become negative.
4. Historical inventory movements are preserved.
5. Product activation/deactivation behaves as specified.
6. No unrelated functionality is required to complete M1.
7. Rejected operations do not create unintended side effects.

The validator should test the system through its normal user interface whenever possible.

Database inspection may be used when necessary to investigate a failure, but database manipulation should not be used to make a validation scenario pass.

---

# 3. Preconditions

Before starting validation:

* The application is running.
* The database is available.
* The application can create and persist products.
* The application can create and persist inventory movements.
* No previous test data interferes with the validation.

If the environment contains existing data, use clearly identifiable test products.

Recommended test product:

> **Chocolate Test**

Base unit:

> **UN**

Optional second product:

> **Suco Test**

Base unit:

> **UN**

---

# 4. Validation Result Convention

Each scenario should be marked as:

* **PASS** — behavior matches the expected result.
* **FAIL** — behavior differs from the expected result.
* **BLOCKED** — validation cannot be performed because of an unrelated environment or implementation problem.

Record relevant observations when a scenario fails.

Do not change the expected result simply because the implementation behaves differently.

If the expected behavior itself appears incorrect or incomplete, stop and review the specification before changing the implementation.

---

# 5. Product Management

## VAL-M1-01 — Create Product

### Steps

1. Open the product management area.
2. Create a product named `Chocolate Test`.
3. Set the base unit to `UN`.
4. Save the product.

### Expected Result

* The product is created successfully.
* The product appears in the product list.
* The product is active by default, according to the current specification.
* The product has no inventory unless inventory is explicitly added.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-02 — Required Product Data

### Steps

Attempt to create a product without:

1. Name.
2. Base unit.

### Expected Result

The system rejects the invalid operation and clearly indicates the missing required information.

No incomplete product is created.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-03 — Edit Product

### Steps

1. Open `Chocolate Test`.
2. Change its name to `Chocolate Test Updated`.
3. Save.
4. Reopen the product.

### Expected Result

* The new name is persisted.
* The product remains the same product.
* Existing inventory is not changed by the name change.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-04 — Deactivate Product

### Steps

1. Deactivate `Chocolate Test Updated`.
2. Return to the product list.

### Expected Result

* The product becomes inactive.
* The product is not deleted.
* The product remains visible where historical/inactive products are expected to be visible.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-05 — Reactivate Product

### Steps

1. Reactivate the previously deactivated product.
2. Return to the product list.

### Expected Result

* The product becomes active again.
* Existing inventory is unchanged.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

# 6. Inventory Entry

## VAL-M1-06 — Add Initial Inventory

### Steps

1. Ensure `Chocolate Test Updated` is active.
2. Add `20 UN` to inventory.
3. Save the operation.
4. Open the inventory balance.

### Expected Result

The product balance is:

> **20 UN**

A corresponding inventory movement exists.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-07 — Add Additional Inventory

### Steps

1. Add another `10 UN`.
2. Save.
3. Check the balance.

### Expected Result

The balance becomes:

> **30 UN**

The previous movement remains preserved.

There should now be at least two inventory movements associated with the product.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

# 7. Inventory Adjustments

## VAL-M1-08 — Positive Adjustment

### Steps

1. Perform a positive inventory adjustment of `5 UN`.
2. Save.
3. Check the balance.

### Expected Result

The balance becomes:

> **35 UN**

A new adjustment movement is created.

Previous movements remain unchanged.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-09 — Negative Adjustment

### Steps

1. Perform a negative adjustment of `3 UN`.
2. Save.
3. Check the balance.

### Expected Result

The balance becomes:

> **32 UN**

A new adjustment movement is created.

Previous movements remain unchanged.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-10 — Adjustment Equal to Current Balance

### Steps

1. Record a negative adjustment equal to the current balance.
2. Save.
3. Check the balance.

### Expected Result

The operation is accepted.

The resulting balance is:

> **0 UN**

Zero inventory is valid.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-11 — Attempt to Create Negative Inventory

### Steps

Assuming the current balance is `0 UN`:

1. Attempt a negative adjustment of `1 UN`.
2. Submit the operation.

### Expected Result

The operation is rejected.

The inventory remains:

> **0 UN**

No movement representing the rejected operation is created.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

# 8. Inventory History

## VAL-M1-12 — Verify Movement History

### Steps

Open the inventory history for `Chocolate Test Updated`.

Review all movements created during the previous scenarios.

### Expected Result

The history shows the individual movements rather than only the current balance.

The sequence should reflect the operations performed.

For example:

| Operation           | Quantity |
| ------------------- | -------: |
| Initial entry       |      +20 |
| Additional entry    |      +10 |
| Positive adjustment |       +5 |
| Negative adjustment |       -3 |
| Balance adjustment  |      -32 |

The resulting balance should be:

> **0 UN**

The rejected negative operation must not appear as a valid inventory movement.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-13 — Historical Data Is Preserved

### Steps

1. Change the product name again.
2. Review inventory history.
3. Review the product's current balance.

### Expected Result

Changing product information does not delete or rewrite historical inventory movements.

The history remains available.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

# 9. Inventory Availability

## VAL-M1-14 — Sufficient Inventory

### Steps

1. Add `10 UN` to `Chocolate Test`.
2. Check availability for `5 UN`.

### Expected Result

The system reports that sufficient inventory is available.

Inventory remains:

> **10 UN**

Checking availability does not modify inventory.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-15 — Insufficient Inventory

### Steps

With `10 UN` available:

1. Check availability for `15 UN`.

### Expected Result

The system reports insufficient inventory.

The product remains valid.

Inventory remains:

> **10 UN**

No negative inventory is created.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

# 10. Product Deactivation and Inventory

## VAL-M1-16 — Deactivation Does Not Change Inventory

### Steps

1. Ensure `Chocolate Test` has `10 UN`.
2. Deactivate the product.
3. Check its inventory balance.

### Expected Result

The product becomes inactive, but its inventory remains:

> **10 UN**

Deactivation does not delete or modify inventory.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-17 — Inactive Product Behavior

### Steps

With the product inactive:

1. Attempt normal inventory entry.
2. Attempt normal inventory adjustment.

### Expected Result

The system follows the behavior defined by the current M1 specification for inactive products.

If the operation is rejected, no inventory movement is created.

If the implementation reveals that the business behavior for inactive products has not been sufficiently defined, stop the validation and flag the behavior for specification review rather than inventing a rule during validation.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

# 11. Rejected Operations and Side Effects

## VAL-M1-18 — Rejected Inventory Operation Has No Side Effects

### Steps

1. Record the current balance.
2. Attempt an invalid inventory operation.
3. Submit it.
4. Reload the inventory.
5. Review the movement history.

### Expected Result

* The operation is rejected.
* The balance is unchanged.
* No invalid movement is created.
* Existing historical movements remain unchanged.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

# 12. Complete M1 Operational Flow

## VAL-M1-19 — Product to Inventory Complete Flow

This scenario validates the main M1 flow as a single operational sequence.

### Steps

1. Create a new product:

   * Name: `Suco Test`
   * Base unit: `UN`
2. Add `20 UN`.
3. Verify balance = `20 UN`.
4. Add `10 UN`.
5. Verify balance = `30 UN`.
6. Perform adjustment `-5 UN`.
7. Verify balance = `25 UN`.
8. Check availability for `20 UN`.
9. Verify sufficient inventory.
10. Check availability for `30 UN`.
11. Verify insufficient inventory.
12. Review movement history.

### Expected Result

The system correctly maintains the inventory state throughout the complete flow.

Final balance:

> **25 UN**

The history contains all accepted movements.

Availability checks do not modify inventory.

No operation creates negative inventory.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

# 13. Regression Checks

After completing the validation scenarios, perform a basic regression check.

## VAL-M1-20 — Data Persistence

### Steps

1. Close or reload the application.
2. Return to the product list.
3. Open the test product.
4. Check inventory balance.
5. Check inventory history.

### Expected Result

All previously accepted data remains persisted.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

## VAL-M1-21 — No Unintended Data Changes

### Steps

Review the test products and their inventory after all scenarios.

### Expected Result

Only operations intentionally performed during validation affected the test data.

There are no unexpected inventory movements or product changes.

### Result

* [ ] PASS
* [ ] FAIL
* [ ] BLOCKED

Notes:

---

# 14. Scope Verification

The following functionality must **not** be required to complete M1:

* Purchase management
* Purchase items
* Suppliers
* Inventory lots
* Expiration dates
* FEFO selection
* Sales
* Baskets
* Basket templates
* Customers
* Payments
* Payment confirmation
* Inventory deduction from sales
* Reserved inventory
* Replenishment workflow
* Loss management
* Production/recipes
* Notifications
* Advanced dashboards
* Advanced analytics

If validation requires any of the above functionality, stop and determine whether:

1. M1 has been incorrectly implemented with a dependency on future functionality; or
2. The specification genuinely needs to change.

Do not solve the issue by silently expanding M1 scope.

---

# 15. Final Validation Checklist

Before accepting M1, confirm:

* [ ] Products can be created.
* [ ] Required product information is validated.
* [ ] Products can be edited.
* [ ] Products can be activated/deactivated.
* [ ] Deactivation does not delete historical information.
* [ ] Inventory can be added.
* [ ] Inventory can be positively adjusted.
* [ ] Inventory can be negatively adjusted when sufficient stock exists.
* [ ] Zero inventory is valid.
* [ ] Negative physical inventory cannot be created.
* [ ] Inventory movements are preserved.
* [ ] Inventory balance reflects the movement history.
* [ ] Availability can be checked without changing inventory.
* [ ] Insufficient inventory is reported without creating negative stock.
* [ ] Rejected operations do not create unintended side effects.
* [ ] Data persists after reload/restart.
* [ ] M1 can be operated without requiring future milestones.

---

# 16. Validation Summary

**Validation date:** __________________

**Environment:** __________________

**Application version / commit:** __________________

**Validator:** __________________

**Result:**

* [ ] ACCEPTED
* [ ] ACCEPTED WITH ISSUES
* [ ] REJECTED
* [ ] BLOCKED

### Issues found

| ID | Scenario | Description | Severity | Status |
| -- | -------- | ----------- | -------- | ------ |
|    |          |             |          |        |
|    |          |             |          |        |
|    |          |             |          |        |

---

# 17. Acceptance Decision

M1 should be considered complete only when:

1. The implementation satisfies the M1 acceptance criteria.
2. The manual validation scenarios pass or have explicitly reviewed exceptions.
3. No critical data-integrity issue remains.
4. Physical inventory cannot become negative.
5. Historical inventory movements remain preserved.
6. No unapproved scope expansion was introduced.
7. The operator can perform the complete M1 flow successfully.

The final acceptance decision belongs to the human product owner.

---

# 18. Traceability

The validation flow follows:

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
        ↓
Human Acceptance
```

Manual validation does not replace automated tests.

Automated tests verify implementation behavior consistently.

Manual validation verifies that the implemented behavior works correctly from the operator's perspective.

---

# 19. Guiding Principle

> Validate the business behavior, not the implementation.

The purpose of this document is not to prove that the code works internally.

The purpose is to verify that Casa Afeto can safely perform the operations defined for M1 — Products & Inventory.

If the system behaves differently from the specification, investigate the discrepancy before changing either the code or the specification.
