from datetime import timedelta

from app.contracts.order import Order, OrderStatus, Side
from app.exchange.matching_engine import MatchingEngine


def test_trade_records_account_ids_and_timestamp():
    engine = MatchingEngine()

    seller = Order(
        order_id="S-META",
        account_id="seller-123",
        symbol="DEMO",
        side=Side.SELL,
        limit_price_paise=10300,
        quantity=6,
        remaining_quantity=6,
        sequence=0,
        status=OrderStatus.OPEN,
    )

    buyer = Order(
        order_id="B-META",
        account_id="buyer-456",
        symbol="DEMO",
        side=Side.BUY,
        limit_price_paise=10500,
        quantity=6,
        remaining_quantity=6,
        sequence=0,
        status=OrderStatus.OPEN,
    )

    assert engine.submit_order(seller) == []

    trades = engine.submit_order(buyer)

    assert len(trades) == 1

    trade = trades[0]

    assert trade.buy_order_id == "B-META"
    assert trade.sell_order_id == "S-META"

    assert trade.buyer_account_id == "buyer-456"
    assert trade.seller_account_id == "seller-123"

    assert trade.quantity == 6
    assert trade.price_paise == 10300

    assert trade.timestamp.tzinfo is not None
    assert trade.timestamp.utcoffset() == timedelta(0)