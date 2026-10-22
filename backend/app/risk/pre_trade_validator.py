
from datetime import datetime, timedelta
from typing import Literal, Sequence

from pydantic import BaseModel, Field

from app.contracts.order import Order


class AccountState(BaseModel):
    """Account information required for pre-trade checks."""

    account_id: str = Field(min_length=1)
    status: Literal["ACTIVE", "SUSPENDED", "CLOSED"]
    available_cash_paise: int = Field(ge=0)
    holdings: dict[str, int] = Field(default_factory=dict)

    def available_holding(self, symbol: str) -> int:
        return self.holdings.get(symbol, 0)


class RiskLimits(BaseModel):
    """Configurable limits for an individual order and account activity."""

    max_order_quantity: int = Field(gt=0)
    max_order_value_paise: int = Field(gt=0)
    max_orders_per_minute: int = Field(gt=0)
    max_order_age_seconds: int = Field(gt=0)


class ValidationResult(BaseModel):
    accepted: bool
    reasons: list[str] = Field(default_factory=list)


def _is_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def validate_order(
    order: Order,
    account: AccountState | None,
    created_at: datetime,
    current_time: datetime,
    limits: RiskLimits,
    recent_submission_times: Sequence[datetime] = (),
    existing_order_ids: set[str] | None = None,
) -> ValidationResult:
    """
    Validate an order before it reaches the matching engine.

    This function does not mutate account balances, holdings, order history,
    or the matching engine. Reservations must be handled separately.
    """
    reasons: list[str] = []

    # Time must be timezone-aware to avoid ambiguous comparisons.
    if not _is_aware(created_at) or not _is_aware(current_time):
        return ValidationResult(
            accepted=False,
            reasons=["TIMESTAMP_MUST_INCLUDE_TIMEZONE"],
        )

    if created_at > current_time:
        reasons.append("ORDER_TIMESTAMP_IN_FUTURE")
    elif current_time - created_at > timedelta(
        seconds=limits.max_order_age_seconds
    ):
        reasons.append("ORDER_EXPIRED")

    # Basic order identity and duplicate checks.
    if not order.order_id.strip():
        reasons.append("INVALID_ORDER_ID")

    if existing_order_ids and order.order_id in existing_order_ids:
        reasons.append("DUPLICATE_ORDER_ID")

    if not order.symbol.strip():
        reasons.append("INVALID_SYMBOL")

    # Account checks.
    if account is None:
        reasons.append("ACCOUNT_NOT_FOUND")
    else:
        if not account.account_id.strip():
            reasons.append("INVALID_ACCOUNT_ID")
        elif account.account_id != order.account_id:
            reasons.append("ACCOUNT_ID_MISMATCH")

        if account.status != "ACTIVE":
            reasons.append("ACCOUNT_NOT_ACTIVE")

    # Quantity and value limits.
    if order.quantity > limits.max_order_quantity:
        reasons.append("ORDER_QUANTITY_LIMIT_EXCEEDED")

    order_value = order.limit_price_paise * order.quantity

    if order_value > limits.max_order_value_paise:
        reasons.append("ORDER_VALUE_LIMIT_EXCEEDED")

    # Available resources. Use the limit price for conservative buy checks.
    if account is not None and account.status == "ACTIVE":
        if order.side.value == "BUY":
            if account.available_cash_paise < order_value:
                reasons.append("INSUFFICIENT_FUNDS")

        elif order.side.value == "SELL":
            available = account.available_holding(order.symbol)

            if available < order.quantity:
                reasons.append("INSUFFICIENT_HOLDINGS")

    # Rate-limit check: count previous submissions within the last minute.
    window_start = current_time - timedelta(minutes=1)
    recent_count = 0

    for timestamp in recent_submission_times:
        if not _is_aware(timestamp):
            reasons.append("INVALID_HISTORY_TIMESTAMP")
            break

        if window_start <= timestamp <= current_time:
            recent_count += 1

    if recent_count >= limits.max_orders_per_minute:
        reasons.append("ORDER_RATE_LIMIT_EXCEEDED")

    # Keep the result predictable if multiple checks fail.
    reasons = list(dict.fromkeys(reasons))

    return ValidationResult(
        accepted=len(reasons) == 0,
        reasons=reasons,
    )
