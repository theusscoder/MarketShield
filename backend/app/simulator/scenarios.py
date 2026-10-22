"""Deterministic input scenarios and their expected matching outcomes."""

from dataclasses import dataclass

from app.contracts.order import Order, OrderStatus, Side
from app.simulator.order_generator import generate_order


@dataclass(frozen=True)
class ExpectedTrade:
    buy_order_id: str
    sell_order_id: str
    price_paise: int
    quantity: int


@dataclass(frozen=True)
class ExpectedOrderState:
    order_id: str
    status: OrderStatus
    remaining_quantity: int


@dataclass(frozen=True)
class Scenario:
    name: str
    orders: tuple[Order, ...]
    expected_trades: tuple[ExpectedTrade, ...]
    expected_orders: tuple[ExpectedOrderState, ...]


def required_two_trade_scenario() -> Scenario:
    """The team acceptance case: one buyer matches two resting sellers."""
    return Scenario(
        name="required_two_trade_partial_fill",
        orders=(
            generate_order(
                order_id="S1", account_id="SellerA", symbol="MSFT",
                side=Side.SELL, limit_price_paise=10300, quantity=6,
            ),
            generate_order(
                order_id="S2", account_id="SellerB", symbol="MSFT",
                side=Side.SELL, limit_price_paise=10400, quantity=8,
            ),
            generate_order(
                order_id="B1", account_id="BuyerA", symbol="MSFT",
                side=Side.BUY, limit_price_paise=10500, quantity=10,
            ),
        ),
        expected_trades=(
            ExpectedTrade("B1", "S1", 10300, 6),
            ExpectedTrade("B1", "S2", 10400, 4),
        ),
        expected_orders=(
            ExpectedOrderState("S1", OrderStatus.FILLED, 0),
            ExpectedOrderState("S2", OrderStatus.PARTIALLY_FILLED, 4),
            ExpectedOrderState("B1", OrderStatus.FILLED, 0),
        ),
    )

def single_trade_partial_fill_scenario() -> Scenario:
    """One buyer partially fills a resting sell order."""
    return Scenario(
        name="single_trade_partial_fill",
        orders=(
            generate_order(
                order_id="S1",
                account_id="SellerA",
                symbol="MSFT",
                side=Side.SELL,
                limit_price_paise=10000,
                quantity=5,
            ),
            generate_order(
                order_id="B1",
                account_id="BuyerA",
                symbol="MSFT",
                side=Side.BUY,
                limit_price_paise=10000,
                quantity=3,
            ),
        ),
        expected_trades=(
            ExpectedTrade("B1", "S1", 10000, 3),
        ),
        expected_orders=(
            ExpectedOrderState(
                "S1", OrderStatus.PARTIALLY_FILLED, 2
            ),
            ExpectedOrderState(
                "B1", OrderStatus.FILLED, 0
            ),
        ),
    )

def non_crossing_scenario() -> Scenario:
    """A bid below the ask must rest without generating a trade."""
    return Scenario(
        name="non_crossing_orders",
        orders=(
            generate_order(
                order_id="S1", account_id="SellerA", symbol="MSFT",
                side=Side.SELL, limit_price_paise=10500, quantity=5,
            ),
            generate_order(
                order_id="B1", account_id="BuyerA", symbol="MSFT",
                side=Side.BUY, limit_price_paise=10400, quantity=5,
            ),
        ),
        expected_trades=(),
        expected_orders=(
            ExpectedOrderState("S1", OrderStatus.OPEN, 5),
            ExpectedOrderState("B1", OrderStatus.OPEN, 5),
        ),
    )
