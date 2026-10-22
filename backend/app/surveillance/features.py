"""Transparent, deterministic surveillance features over supplied order data.

These features are indicators only; none establishes manipulative intent.
"""

from collections import Counter
from collections.abc import Iterable

from app.contracts.order import Order, OrderStatus


def order_notional_paise(order: Order) -> int:
    """Return limit-price notional in paise (limit price × original quantity)."""
    return order.limit_price_paise * order.quantity


def fill_ratio(order: Order) -> float:
    """Fraction of original quantity executed, in the inclusive range [0, 1]."""
    return (order.quantity - order.remaining_quantity) / order.quantity


def remaining_ratio(order: Order) -> float:
    """Fraction of original quantity still open/unexecuted, in [0, 1]."""
    return order.remaining_quantity / order.quantity


def account_order_activity(orders: Iterable[Order]) -> dict[str, int]:
    """Count supplied orders by account; empty input returns an empty mapping."""
    counts = Counter(order.account_id for order in orders)
    return dict(counts)


def cancellation_ratio(orders: Iterable[Order]) -> float:
    """Cancelled orders divided by all supplied orders; empty input returns 0.0."""
    order_list = list(orders)
    if not order_list:
        return 0.0
    cancelled = sum(order.status == OrderStatus.CANCELLED for order in order_list)
    return cancelled / len(order_list)
