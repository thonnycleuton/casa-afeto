from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.payments.models import Payment
from app.sales.models import Sale


def _sale_or_raise(db: Session, sale_id: int, *, lock: bool = False) -> Sale:
    """Fetch a sale by ID, optionally with row-level lock.

    Follows the same pattern as sales/service.py _sale_or_raise().
    When lock=True, uses SELECT ... FOR UPDATE to serialize concurrent
    payment operations on the same sale.
    """
    stmt = select(Sale).where(Sale.id == sale_id)
    if lock:
        stmt = stmt.with_for_update()
    sale = db.scalar(stmt)
    if sale is None:
        raise ResourceNotFoundError("Venda não encontrada.")
    return sale


def record_payment(
    db: Session,
    sale_id: int,
    amount: Decimal,
    method: str,
    idempotency_key: str,
) -> Payment:
    """Record a payment with idempotency and excess protection.

    Transaction flow (all within the same DB transaction managed by get_db()):
    1. Lock the sale row (SELECT FOR UPDATE) to serialize concurrent payments.
    2. Check idempotency: if key exists, return existing or reject conflict.
    3. Validate excess: reject if total_paid + amount > sale.total.
    4. Insert new payment (ON CONFLICT DO NOTHING as residual defense).
    5. Return the new payment.

    The commit is performed by the API layer (api/v1/payments.py).
    If BusinessRuleError is raised, the transaction is rolled back by get_db().
    """
    # 1. Lock the sale to serialize concurrent payment operations
    sale = _sale_or_raise(db, sale_id, lock=True)

    # 2. Check idempotency before inserting
    existing = db.scalar(
        select(Payment).where(
            Payment.sale_id == sale_id,
            Payment.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        # Key already exists — check if values match
        if existing.amount != amount or existing.method != method:
            raise BusinessRuleError(
                f"Chave de idempotência já usada com valores diferentes "
                f"(R${existing.amount} {existing.method})."
            )
        # Idempotent retry — same key, same values
        return existing

    # 3. Validate excess: new payment must not exceed sale total
    total_paid = get_total_paid(db, sale_id)
    remaining = sale.total - total_paid
    if amount > remaining:
        raise BusinessRuleError(
            f"O pagamento de R${amount} excede o valor restante de R${remaining}. "
            f"Total da venda: R${sale.total}. Total pago: R${total_paid}."
        )

    # 4. Insert new payment (ON CONFLICT DO NOTHING as residual defense)
    insert_stmt = text("""
        INSERT INTO payments (sale_id, amount, method, idempotency_key)
        VALUES (:sale_id, :amount, :method, :idempotency_key)
        ON CONFLICT (sale_id, idempotency_key) DO NOTHING
    """)
    result = db.execute(insert_stmt, {
        "sale_id": sale_id,
        "amount": amount,
        "method": method,
        "idempotency_key": idempotency_key,
    })

    if result.rowcount == 1:
        # New payment inserted — flush to assign id, then return it.
        db.flush()
        payment = db.scalar(
            select(Payment).where(
                Payment.sale_id == sale_id,
                Payment.idempotency_key == idempotency_key,
            )
        )
        return payment

    # rowcount == 0: race condition — another transaction inserted first.
    # Fetch and return the existing payment.
    existing = db.scalar(
        select(Payment).where(
            Payment.sale_id == sale_id,
            Payment.idempotency_key == idempotency_key,
        )
    )
    if existing is None:
        raise BusinessRuleError(
            "Erro interno ao verificar pagamento. Tente novamente."
        )
    return existing


def get_total_paid(db: Session, sale_id: int) -> Decimal:
    """Returns the sum of all payments for a sale."""
    from sqlalchemy import func
    value = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.sale_id == sale_id
        )
    )
    return Decimal(value)


def get_payments_for_sale(db: Session, sale_id: int) -> list[Payment]:
    """Returns all payments for a sale, ordered by creation time."""
    _sale_or_raise(db, sale_id)
    return list(
        db.scalars(
            select(Payment)
            .where(Payment.sale_id == sale_id)
            .order_by(Payment.created_at, Payment.id)
        ).all()
    )
