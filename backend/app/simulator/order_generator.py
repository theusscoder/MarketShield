"""Create valid orders for repeatable simulation runs.

`generate_order` creates one explicitly specified order.
`generate_orders` creates a reproducible batch from a local random seed.
Neither function changes Python's global random-number state.
"""

import random
from collections.abc import Sequence

from app.contracts.order import Order, OrderStatus, Side


def generate_order(
    *,
    order_id: str,
    account_id: str,
    symbol: str,
    side: Side,
    limit_price_paise: int,
    quantity: int,
) -> Order:
    """Build a new, unsubmitted order with its full quantity available.

    The matching engine assigns the authoritative submission sequence.
    The shared Pydantic contract validates the order's fields.
    """
    return Order(
        order_id=order_id,
        account_id=account_id,
        symbol=symbol,
        side=side,
        limit_price_paise=limit_price_paise,
        quantity=quantity,
        remaining_quantity=quantity,
        sequence=0,
        status=OrderStatus.OPEN,
    )


def generate_orders(
    *,
    seed: int,
    count: int,
    symbols: Sequence[str] = ("MSFT", "AAPL"),
    account_count: int = 4,
) -> list[Order]:
    """Generate a deterministic batch of valid orders.

    Same seed and same arguments produce the same order fields and order
    sequence. A private `random.Random` keeps this function independent
    from unrelated random calls elsewhere in the application.

    Prices are integer paise and quantities are positive whole units.
    `count=0` is valid and returns an empty list.
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError("count must be a non-negative integer")
    if (
        isinstance(symbols, (str, bytes))
        or not isinstance(symbols, Sequence)
    ):
        raise ValueError("symbols must be a sequence of symbol strings")

    if not symbols:
        raise ValueError("symbols must contain at least one symbol")

    if any(not isinstance(symbol, str) or not symbol.strip() for symbol in symbols):
        raise ValueError("every symbol must be a non-empty string")
    if not isinstance(account_count, int) or isinstance(account_count, bool) or account_count < 1:
        raise ValueError("account_count must be a positive integer")

    rng = random.Random(seed)
    orders: list[Order] = []
    sides = (Side.BUY, Side.SELL)

    for index in range(1, count + 1):
        # Fixed ID format makes order identity reproducible as well.
        orders.append(
            generate_order(
                order_id=f"SIM-{index:06d}",
                account_id=f"ACCOUNT-{rng.randint(1, account_count):02d}",
                symbol=symbols[rng.randrange(len(symbols))],
                side=sides[rng.randrange(len(sides))],
                limit_price_paise=rng.randint(1_000, 50_000),
                quantity=rng.randint(1, 100),
            )
        )

    return orders
