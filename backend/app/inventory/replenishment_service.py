"""Service de reposição de estoque — cálculo em tempo real (REP-008)."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.baskets.models import BasketTemplate, BasketTemplateItem
from app.inventory.models import StockBatch
from app.inventory.replenishment_schemas import (
    ReplenishmentItemRead,
    ReplenishmentListRead,
)
from app.products.models import Product
from app.sales.models import Sale, SaleBasket, SaleBasketItem


def _calculate_stock_by_product(db: Session) -> dict[int, Decimal]:
    """REP-001: Estoque atual = soma dos lotes ativos por produto."""
    stmt = (
        select(StockBatch.product_id, func.coalesce(func.sum(StockBatch.quantity_remaining), 0))
        .where(StockBatch.status == "ACTIVE")
        .group_by(StockBatch.product_id)
    )
    return {row[0]: row[1] for row in db.execute(stmt).all()}


def _calculate_estimated_need_by_product(db: Session) -> dict[int, Decimal]:
    """REP-002: Necessidade estimada = soma dos templates ativos por produto.

    REP-007: Template inativo não gera necessidade.
    """
    stmt = (
        select(BasketTemplateItem.product_id, func.coalesce(func.sum(BasketTemplateItem.quantity), 0))
        .join(BasketTemplate)
        .where(BasketTemplate.active == True)  # noqa: E712
        .group_by(BasketTemplateItem.product_id)
    )
    return {row[0]: row[1] for row in db.execute(stmt).all()}


def _calculate_urgent_need_by_product(db: Session) -> dict[int, Decimal]:
    """REP-003: Necessidade urgente = vendas CONFIRMADA/EM_PREPARAÇÃO/PRONTA.

    REP-005: Venda CANCELADA não gera necessidade.
    REP-006: Venda ENTREGUE não gera necessidade.
    """
    urgent_statuses = ("CONFIRMADA", "EM PREPARAÇÃO", "PRONTA")
    stmt = (
        select(SaleBasketItem.product_id, func.coalesce(func.sum(SaleBasketItem.quantity), 0))
        .join(SaleBasket, SaleBasketItem.sale_basket_id == SaleBasket.id)
        .join(Sale, SaleBasket.sale_id == Sale.id)
        .where(Sale.status.in_(urgent_statuses))
        .group_by(SaleBasketItem.product_id)
    )
    return {row[0]: row[1] for row in db.execute(stmt).all()}


def _classify_status(
    stock_quantity: Decimal, estimated_need: Decimal, urgent_need: Decimal
) -> str:
    """REP-004: Classificar status do produto.

    OK: stock >= total_need
    BAIXO: stock < total_need e urgent_need = 0
    CRÍTICO: urgent_need > 0 e stock < urgent_need
    """
    total_need = estimated_need + urgent_need

    if urgent_need > 0 and stock_quantity < urgent_need:
        return "CRÍTICO"
    if stock_quantity < total_need:
        return "BAIXO"
    return "OK"


def get_replenishment_list(
    db: Session,
    status_filter: str | None = None,
    product_id_filter: int | None = None,
) -> ReplenishmentListRead:
    """Calcular a lista de reposição em tempo real.

    REP-008: Lista de reposição é cálculo em tempo real.
    REP-009: Produto sem estoque é BAIXO ou CRÍTICO.
    REP-010: Produto sem necessidade é OK.
    """
    stock_by_product = _calculate_stock_by_product(db)
    estimated_need_by_product = _calculate_estimated_need_by_product(db)
    urgent_need_by_product = _calculate_urgent_need_by_product(db)

    # Coletar todos os product_ids que aparecem em qualquer cálculo
    all_product_ids = set()
    all_product_ids.update(stock_by_product.keys())
    all_product_ids.update(estimated_need_by_product.keys())
    all_product_ids.update(urgent_need_by_product.keys())

    # Buscar nomes dos produtos
    product_names: dict[int, str] = {}
    if all_product_ids:
        stmt = select(Product.id, Product.name).where(Product.id.in_(all_product_ids))
        for row in db.execute(stmt).all():
            product_names[row[0]] = row[1]

    items: list[ReplenishmentItemRead] = []
    for pid in sorted(all_product_ids):
        stock = stock_by_product.get(pid, Decimal("0"))
        estimated = estimated_need_by_product.get(pid, Decimal("0"))
        urgent = urgent_need_by_product.get(pid, Decimal("0"))
        total = estimated + urgent
        shortage = max(total - stock, Decimal("0"))
        status = _classify_status(stock, estimated, urgent)

        # REP-010: Produto sem necessidade é OK
        if total == 0:
            status = "OK"

        # Aplicar filtros
        if status_filter and status != status_filter:
            continue
        if product_id_filter and pid != product_id_filter:
            continue

        items.append(
            ReplenishmentItemRead(
                product_id=pid,
                product_name=product_names.get(pid, f"Produto {pid}"),
                stock_quantity=stock,
                estimated_need=estimated,
                urgent_need=urgent,
                total_need=total,
                shortage=shortage,
                status=status,
            )
        )

    return ReplenishmentListRead(items=items, total=len(items))
