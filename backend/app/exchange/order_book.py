
from collections import defaultdict

from app.contracts.order import Order, Side


class OrderBook:
    """In-memory order book with price-time priority."""

    def __init__(self) -> None:
        self._bids: dict[str, list[Order]] = defaultdict(list)
        self._asks: dict[str, list[Order]] = defaultdict(list)

    def add(self, order: Order) -> None:
        """Add a resting order in the correct priority position."""
        if order.remaining_quantity <= 0:
            raise ValueError("Cannot add an order with no remaining quantity")

        if order.side == Side.BUY:
            orders = self._bids[order.symbol]
            orders.append(order)
            orders.sort(
                key=lambda item: (
                    -item.limit_price_paise,
                    item.sequence,
                )
            )
        else:
            orders = self._asks[order.symbol]
            orders.append(order)
            orders.sort(
                key=lambda item: (
                    item.limit_price_paise,
                    item.sequence,
                )
            )

    def best_opposite(
        self,
        symbol: str,
        incoming_side: Side,
    ) -> Order | None:
        """Get the highest bid or lowest ask opposing the incoming order."""
        if incoming_side == Side.BUY:
            orders = self._asks.get(symbol, [])
        else:
            orders = self._bids.get(symbol, [])

        return orders[0] if orders else None

    def remove(self, order: Order) -> bool:
        """Remove an order from the book; return False if it isn't present."""
        if order.side == Side.BUY:
            orders = self._bids.get(order.symbol, [])
        else:
            orders = self._asks.get(order.symbol, [])

        try:
            orders.remove(order)
            return True
        except ValueError:
            return False

    def get_bids(self, symbol: str) -> list[Order]:
        """Return a snapshot of bids in price-time priority order."""
        return list(self._bids.get(symbol, []))

    def get_asks(self, symbol: str) -> list[Order]:
        """Return a snapshot of asks in price-time priority order."""
        return list(self._asks.get(symbol, []))

    def get_order(self, order_id: str) -> Order | None:
        """Find an order currently resting in the book."""
        for orders in self._bids.values():
            for order in orders:
                if order.order_id == order_id:
                    return order

        for orders in self._asks.values():
            for order in orders:
                if order.order_id == order_id:
                    return order

        return None
