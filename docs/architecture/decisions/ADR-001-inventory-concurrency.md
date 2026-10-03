# ADR-001: Inventory Concurrency & Absolute Non-Negative Inventory Invariant

**Status:** Approved
**Date:** 2026-10-02
**Deciders:** Product Owner, Architecture

---

## 1. Context

In Casa Afeto, physical inventory balance must never become negative (`INV-006`).

A naive check-then-write sequence:

```text
read balance
    ↓
check balance >= requested_quantity
    ↓
write movement
```

is vulnerable to race conditions under concurrent requests.

### Example Scenario

```text
Initial physical balance = 4 UN

Request A: adjustment -3 UN (concurrent)
Request B: adjustment -3 UN (concurrent)
```

If both requests execute concurrently without isolation:
1. Request A reads balance = 4 (validates: 4 - 3 = 1 >= 0).
2. Request B reads balance = 4 (validates: 4 - 3 = 1 >= 0).
3. Request A inserts an adjustment movement of `-3` and commits.
4. Request B inserts an adjustment movement of `-3` and commits.
5. The resulting physical balance becomes `4 - 3 - 3 = -2 UN`, violating `INV-006`.

Both requests cannot independently validate against a stale balance and commit successfully. `INV-006` is an absolute business invariant and must be guaranteed transactionally under concurrency.

---

## 2. Decision

All inventory operations that can affect the physical balance of a product (`ENTRY`, `ADJUSTMENT`, and future sale deductions) will execute within an atomic database transaction and serialize concurrent modifications for the same product's inventory state.

For the Casa Afeto technical stack (PostgreSQL + SQLAlchemy 2.x), the expected approach is row-level locking:

```text
BEGIN TRANSACTION;

-- Lock inventory state for the target product
SELECT ... FROM products WHERE id = :product_id FOR UPDATE;
-- (or lock a dedicated inventory anchor row if applicable)

-- Calculate current balance from existing movements
SELECT COALESCE(SUM(quantity), 0) FROM inventory_movements WHERE product_id = :product_id;

-- Validate resulting balance
IF current_balance + delta < 0 THEN
    ROLLBACK (or raise DomainException);
END IF;

-- Insert immutable movement
INSERT INTO inventory_movements (id, product_id, quantity, type, created_at)
VALUES (...);

COMMIT;
```

Any concurrent transaction attempting to modify inventory for the same product will wait until the active transaction commits or rolls back, ensuring it evaluates against the updated, authoritative balance.

---

## 3. Consequences

### Positive
* `INV-006` (No Negative Physical Inventory) remains strictly satisfied under concurrent operations.
* Inventory operations remain atomic and ACID-compliant.
* No speculative materialized balance table or cache synchronization is required for M1.
* Works natively with PostgreSQL and SQLAlchemy 2.x without external infrastructure.

### Trade-offs
* Concurrent inventory modifications targeting the exact same product will serialize, with subsequent requests briefly waiting on the lock. Given Casa Afeto's operational scale, lock contention for a single product across concurrent requests is expected to be minimal.

---

## 4. Explicit Non-Goals (Out of Scope for M1)

The following architectural patterns are explicitly rejected as unnecessary complexity for M1:
* Distributed locks (e.g., Redis Redlock);
* External message brokers / event buses (RabbitMQ, Kafka);
* Event sourcing frameworks;
* Materialized balance tables or caching layers created solely to solve concurrency;
* Separate microservices for inventory management.
