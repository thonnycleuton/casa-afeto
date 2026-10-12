# ADR-002: M5 Architecture — Payments, Stock Reservations and Sale Concurrency

**Status:** Approved
**Date:** 2026-10-12
**Deciders:** Product Owner, Architecture

---

## 1. Context

M5 (Payments and Stock Reservations) extends the Casa Afeto system with financial tracking, atomic stock reservation on sale confirmation, physical write-offs on preparation, and inspection-based reintegration on cancellation.

The approved business rules (RES-001 through RES-012 in `business-contract.md` §37) require:

- Atomic confirmation + reservation (RES-001).
- Physical write-off only at preparation start (RES-005).
- Reductions release only unconsumed reserved quantities (RES-007).
- Reopening a sale must not repeat physical write-offs (RES-009).
- Cancellation after preparation triggers inspection and selective reintegration (RES-011).

These rules demand a data model and concurrency strategy that go beyond the simple inventory operations of M1 (ADR-001).

---

## 2. Decisions

### D-1: Three-Counter Model for Stock Reservations

**Decision:** Table `sale_stock_reservations` uses three independent counters per (sale, product): `current_quantity`, `reserved_quantity`, and `consumed_quantity`, with the invariant `consumed_quantity <= reserved_quantity`.

**Rationale:** A two-counter model (`reserved_quantity` + `consumed_quantity`) violates invariants when composition is reduced after full consumption. The three-counter model allows `current_quantity` and `consumed_quantity` to diverge, supporting the mixed state (partially consumed + partially unconsumed) required by RES-007.

**Alternatives considered:**
- Two counters (rejected — invariant violations).
- Per-basket granularity (rejected — unnecessary complexity for current contract).
- Materialized balance table (rejected — violates ADR-001 principle).

---

### D-2: MovementType.OUTPUT and sale_id in InventoryMovements

**Decision:** Added `OUTPUT` to `MovementType` enum and nullable `sale_id` (FK → sales.id, SET NULL) to `inventory_movements`. OUTPUT records physical write-offs with negative quantity, linked to the originating sale.

**Rationale:** RES-005 requires "physical write-off registered as inventory movement". OUTPUT semantically distinguishes a sale-driven output from a manual adjustment. `sale_id` enables traceability: which sale consumed which stock.

**Alternatives considered:**
- Use ADJUSTMENT for output (rejected — loses traceability and semantics).
- Separate table for sale outputs (rejected — breaks unified movement pattern).
- Omit `sale_id` (rejected — loses traceability).

---

### D-3: Lock Hierarchy for Deadlock Prevention

**Decision:** All sale-related flows acquire row-level locks in a strict global order:

1. Sale row
2. Reservation rows
3. Inspection rows
4. Product rows (ordered by `product_id`)

**Rationale:** Eliminates deadlocks by construction: a deadlock requires a cycle in the wait-for graph, but the strict hierarchy prevents cycles. The technical design proves formally that none of the 10 sale flows violates this hierarchy.

**Alternatives considered:**
- No hierarchy (rejected — deadlock risk).
- Table-level locks (rejected — excessive serialization).
- Timeout + retry (rejected — masks the problem).
- PostgreSQL advisory locks (rejected — row locks are sufficient).

---

### D-4: Payment Idempotency via INSERT ON CONFLICT DO NOTHING

**Decision:** Payment registration uses `INSERT ... ON CONFLICT DO NOTHING` with a unique constraint on `(sale_id, idempotency_key)`, checking `rowcount` to distinguish new inserts from idempotent retries.

**Rationale:** This approach is atomic, does not raise `IntegrityError` for unique constraint conflicts, does not invalidate the SQLAlchemy session, and works correctly under concurrency. Alternatives like `try/except IntegrityError` are fragile (cannot distinguish constraint types) and may invalidate the session.

**Excess protection:** Before inserting, the sale row is locked (`SELECT FOR UPDATE`), the total paid is recalculated, and the new payment is rejected if `total_paid + amount > sale.total`. This validation is always performed, including on retries — if the payment already exists (`rowcount == 0`), the existing record is returned without error.

---

### D-5: Sale Cancellation Inspection Table

**Decision:** Table `sale_cancellation_inspection` tracks the inspection lifecycle for each product in a canceled sale that was already prepared. It records `consumed_quantity`, `inspected_quantity`, `reusable_quantity`, and `reintegrated_quantity`, with states `PENDING`, `INSPECTED`, `REINTEGRATED`, and `DISCARDED`.

**Rationale:** RES-011 requires that cancellation after preparation does not assume all items return physically. The inspection table provides the structure for the operator to record what was found and reintegrate only the reusable portion.

---

## 3. Consequences

### Positive

- RES-001 through RES-012 are fully implemented and testable.
- The three-counter model supports mixed consumed/unconsumed states without invariant violations.
- Lock hierarchy eliminates deadlocks by construction.
- Payment idempotency and excess protection are guaranteed under concurrency.
- OUTPUT movements provide full traceability from sale to stock consumption.
- Inspection table enables the full cancellation → inspection → reintegration cycle.

### Trade-offs

- Reservation and inspection tables add complexity to the sale cancellation flow.
- Concurrent payment operations on the same sale serialize on the sale row lock.
- The three-counter model requires understanding of the `consumed_quantity <= reserved_quantity` invariant.

---

## 4. Explicit Non-Goals

The following patterns are explicitly rejected as unnecessary for M5:

- Distributed locks or external concurrency infrastructure;
- Event sourcing or CQRS for payments or reservations;
- Generic repository or service frameworks;
- Separate microservices for payment processing;
- Automatic bank or payment gateway integration (out of scope for M5).

---

## 5. Related Decisions

- **ADR-001:** Inventory concurrency and non-negative invariant. M5 extends ADR-001's `SELECT FOR UPDATE` pattern to the sale domain with a multi-level lock hierarchy.
