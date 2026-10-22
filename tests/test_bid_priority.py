from app.contracts.order import Order, OrderStatus, Side
from app.exchange.matching_engine import MatchingEngine


def make_order(order_id, side, price, quantity):
    return Order(
        order_id=order_id,
        account_id=f"account-{order_id}",
        symbol="MSFT",
        side=side,
        limit_price_paise=price,
        quantity=quantity,
        remaining_quantity=quantity,
        sequence=0,
        status=OrderStatus.OPEN,
    )


def test_highest_bid_executes_first():
    engine = MatchingEngine()

    engine.submit_order(make_order("B1", Side.BUY, 10500, 5))
    engine.submit_order(make_order("B2", Side.BUY, 10700, 5))

    trades = engine.submit_order(
        make_order("S1", Side.SELL, 10400, 5)
    )

    assert len(trades) == 1
    assert trades[0].buy_order_id == "B2"
    assert trades[0].price_paise == 10700

    assert engine.get_order("B1").remaining_quantity == 5
    assert engine.get_order("B2").status == OrderStatus.FILLED


def test_equal_price_bids_follow_fifo():
    engine = MatchingEngine()

    engine.submit_order(make_order("B1", Side.BUY, 10500, 5))
    engine.submit_order(make_order("B2", Side.BUY, 10500, 5))

    trades = engine.submit_order(
        make_order("S1", Side.SELL, 10400, 7)
    )

    assert len(trades) == 2

    assert trades[0].buy_order_id == "B1"
    assert trades[0].quantity == 5

    assert trades[1].buy_order_id == "B2"
    assert trades[1].quantity == 2

    assert engine.get_order("B1").status == OrderStatus.FILLED
    assert engine.get_order("B2").status == OrderStatus.PARTIALLY_FILLED
    assert engine.get_order("B2").remaining_quantity == 3