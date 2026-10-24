
"""Deterministic, explainable rule-based surveillance alerts."""
import hashlib
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from matplotlib.pylab import identity

from app.contracts.alerts import SurveillanceAlert
from app.contracts.order import Order, OrderStatus
from app.contracts.trade import Trade
from app.surveillance.features import (
    account_order_activity,
    fill_ratio,
    order_notional_paise,
)



@dataclass(frozen=True)
class SurveillanceThresholds:
    """Configurable initial thresholds for simulation, not regulatory limits."""

    min_orders_for_activity: int = 3
    min_orders_for_cancellation_check: int = 3
    cancellation_ratio_limit: float = 0.5
    min_order_notional_paise: int = 1_000_000
    max_fill_ratio_for_large_order: float = 0.5

    def __post_init__(self):
        if (
            isinstance(self.min_orders_for_activity, bool)
            or not isinstance(self.min_orders_for_activity, int)
            or self.min_orders_for_activity < 1
        ):
            raise ValueError("min_orders_for_activity must be an integer >= 1")

        if (
            isinstance(self.min_orders_for_cancellation_check, bool)
            or not isinstance(self.min_orders_for_cancellation_check, int)
            or self.min_orders_for_cancellation_check < 1
        ):
            raise ValueError(
                "min_orders_for_cancellation_check must be an integer >= 1"
            )

        if (
            isinstance(self.min_order_notional_paise, bool)
            or not isinstance(self.min_order_notional_paise, int)
            or self.min_order_notional_paise < 1
        ):
            raise ValueError("min_order_notional_paise must be an integer >= 1")

        for name, value in (
            ("cancellation_ratio_limit", self.cancellation_ratio_limit),
            ("max_fill_ratio_for_large_order", self.max_fill_ratio_for_large_order),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
            ):
                raise ValueError(f"{name} must be between 0 and 1")



def detect_suspicious_activity(
    orders: Iterable[Order],
    trades: Iterable[Trade] = (),
    *,
    thresholds: SurveillanceThresholds | None = None,
) -> list[SurveillanceAlert]:
    """Return deterministic alerts based on the supplied orders and trades.

    This first version uses only data available in the current contracts.
    Alerts are investigation signals, not findings of misconduct.
    """
    orders = list(orders)
    trades = list(trades)
    limits = thresholds or SurveillanceThresholds()
    alerts: list[SurveillanceAlert] = []

    orders_by_account: dict[str, list[Order]] = defaultdict(list)
    orders_by_id: dict[str, Order] = {}

    for order in orders:
        orders_by_account[order.account_id].append(order)
        orders_by_id[order.order_id] = order

    def add_alert(
        account_id: str,
        rule: str,
        severity: str,
        evidence: str,
    ) -> None:
        # Stable IDs make repeated runs over the same inputs reproducible.
        identity = f"{rule}|{account_id}|{evidence}"
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
        alert_id = f"{rule}:{digest}"
        alerts.append(
            SurveillanceAlert(
                alert_id=alert_id,
                account_id=account_id,
                rule=rule,
                related_event_ids=[],
                severity=severity,
                explanation=evidence,
            )
        )

    # Rule 1: repeated order activity from one account in the supplied batch.
    activity = account_order_activity(orders)
    for account_id in sorted(activity):
        count = activity[account_id]
        if count >= limits.min_orders_for_activity:
            account_order_ids = sorted(
                order.order_id for order in orders_by_account[account_id]
            )
            add_alert(
                account_id,
                "SURV-001",
                "medium",
                f"Account submitted {count} orders in this observation batch. "
                f"Order IDs: {', '.join(account_order_ids)}. "
                "Review against the account's normal activity.",
            )

    # Rule 2: high cancellation ratio for accounts with enough observations.
    for account_id in sorted(orders_by_account):
        account_orders = orders_by_account[account_id]
        cancelled = [
            order for order in account_orders
            if order.status == OrderStatus.CANCELLED
        ]
        if len(account_orders) < limits.min_orders_for_cancellation_check:
            continue

        ratio = len(cancelled) / len(account_orders)
        if ratio >= limits.cancellation_ratio_limit and cancelled:
            add_alert(
                account_id,
                "SURV-002",
                "medium",
                f"{len(cancelled)} of {len(account_orders)} supplied orders "
                f"were cancelled (ratio {ratio:.2f}). "
                f"Cancelled order IDs: "
                f"{', '.join(sorted(o.order_id for o in cancelled))}. "
                "Cancellation patterns alone do not establish spoofing.",
            )

    # Rule 3: large orders with a low fill ratio.
    for account_id in sorted(orders_by_account):
        candidates = [
            order
            for order in orders_by_account[account_id]
            if order_notional_paise(order) >= limits.min_order_notional_paise
            and fill_ratio(order) <= limits.max_fill_ratio_for_large_order
            and order.remaining_quantity > 0
        ]
        if candidates:
            evidence = "; ".join(
                f"{order.order_id}: notional={order_notional_paise(order)} paise, "
                f"fill_ratio={fill_ratio(order):.2f}, "
                f"remaining={order.remaining_quantity}"
                for order in sorted(candidates, key=lambda o: o.order_id)
            )
            add_alert(
                account_id,
                "SURV-003",
                "medium",
                "Large orders remain substantially unfilled: "
                f"{evidence}. Review with order timing and cancellation history "
                "before inferring manipulative intent.",
            )

    # Rule 4: a trade where both sides map to the same account.
    # Missing order references are skipped; we never guess account ownership.
    self_trade_accounts: dict[str, set[str]] = defaultdict(set)
    for trade in trades:
        buy_order = orders_by_id.get(trade.buy_order_id)
        sell_order = orders_by_id.get(trade.sell_order_id)
        if buy_order is None or sell_order is None:
            continue
        if buy_order.account_id == sell_order.account_id:
            self_trade_accounts[buy_order.account_id].add(trade.trade_id)

    for account_id in sorted(self_trade_accounts):
        trade_ids = sorted(self_trade_accounts[account_id])
        add_alert(
            account_id,
            "SURV-004",
            "high",
            "Executed trade(s) have buy and sell orders mapped to the same "
            f"account. Trade IDs: {', '.join(trade_ids)}. "
            "Verify account relationships and execution records.",
        )

    return alerts
