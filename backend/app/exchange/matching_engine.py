
from uuid import uuid4

from app.contracts.order import Order, OrderStatus, Side
from app.contracts.trade import Trade
from app.exchange.order_book import OrderBook


class MatchingEngine:
    """Sequential, in-memory limit-order matching engine."""

    def __init__(self) -> None:
        self.order_book = OrderBook()
        self._orders: dict[str, Order] = {}
        self._next_order_sequence = 1
        self._next_trade_sequence = 1
        self.trades: list[Trade] = []

    def submit_order(self, order: Order) -> list[Trade]:
        """Accept an order, match it, and return its resulting trades."""
        self._validate_new_order(order)

        # The engine, not the caller, determines submission priority.
        order.sequence = self._next_order_sequence
        self._next_order_sequence += 1

        self._orders[order.order_id] = order
        new_trades: list[Trade] = []

        while order.remaining_quantity > 0:
            resting = self.order_book.best_opposite(
                order.symbol,
                order.side,
            )

            if resting is None:
                break

            if not self._prices_cross(order, resting):
                break

            traded_quantity = min(
                order.remaining_quantity,
                resting.remaining_quantity,
            )

            # Execution price is set by the resting order.
            execution_price = resting.limit_price_paise

            if order.side == Side.BUY:
                buy_order = order
                sell_order = resting
            else:
                buy_order = resting
                sell_order = order

            order.remaining_quantity -= traded_quantity
            resting.remaining_quantity -= traded_quantity

            trade = Trade(
                trade_id=str(uuid4()),
                symbol=order.symbol,
                buy_order_id=buy_order.order_id,
                sell_order_id=sell_order.order_id,
                price_paise=execution_price,
                quantity=traded_quantity,
                sequence=self._next_trade_sequence,
            )

            self._next_trade_sequence += 1
            self.trades.append(trade)
            new_trades.append(trade)

            if resting.remaining_quantity == 0:
                resting.status = OrderStatus.FILLED
                self.order_book.remove(resting)
            else:
                resting.status = OrderStatus.PARTIALLY_FILLED

        # Set the incoming order's final status.
        if order.remaining_quantity == 0:
            order.status = OrderStatus.FILLED
        elif order.remaining_quantity < order.quantity:
            order.status = OrderStatus.PARTIALLY_FILLED
            self.order_book.add(order)
        else:
            order.status = OrderStatus.OPEN
            self.order_book.add(order)

        return new_trades

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a resting order without reversing executed trades."""
        order = self._orders.get(order_id)

        if order is None:
            return False

        if order.status not in (
            OrderStatus.OPEN,
            OrderStatus.PARTIALLY_FILLED,
        ):
            return False

        if not self.order_book.remove(order):
            return False

        order.status = OrderStatus.CANCELLED
        return True

    def get_order(self, order_id: str) -> Order | None:
        """Return a known order, including filled or cancelled orders."""
        return self._orders.get(order_id)

    @staticmethod
    def _prices_cross(incoming: Order, resting: Order) -> bool:
        if incoming.side == Side.BUY:
            return incoming.limit_price_paise >= resting.limit_price_paise

        return incoming.limit_price_paise <= resting.limit_price_paise

    def _validate_new_order(self, order: Order) -> None:
        if order.order_id in self._orders:
            raise ValueError(f"Duplicate order ID: {order.order_id}")

        if not order.order_id.strip():
            raise ValueError("Order ID must not be empty")

        if not order.account_id.strip():
            raise ValueError("Account ID must not be empty")

        if not order.symbol.strip():
            raise ValueError("Symbol must not be empty")

        if order.limit_price_paise <= 0:
            raise ValueError("Limit price must be positive")

        if order.quantity <= 0:
            raise ValueError("Order quantity must be positive")

        if order.remaining_quantity != order.quantity:
            raise ValueError(
                "A newly submitted order must start with full quantity"
            )

        if order.status != OrderStatus.OPEN:
            raise ValueError("A new order must start with OPEN status")
