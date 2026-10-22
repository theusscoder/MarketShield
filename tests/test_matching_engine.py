
import pytest
from pydantic import ValidationError

from app.contracts.order import Order, OrderStatus, Side
from app.exchange.matching_engine import MatchingEngine


def make_order(
    order_id: str,
    account_id: str,
    side: Side,
    price_rupees: int,
    quantity: int,
    
    symbol: str = "MSFT",
) -> Order:
    return Order(
        order_id=order_id,
        account_id=account_id,
        symbol=symbol,
        side=side,
        limit_price_paise=price_rupees * 100,
        quantity=quantity,
        remaining_quantity=quantity,
        sequence=0,
        status=OrderStatus.OPEN,
    )


def test_required_partial_fill_scenario():
    engine = MatchingEngine()

    engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 103, 6)
    )
    engine.submit_order(
        make_order("S2", "SellerB", Side.SELL, 104, 8)
    )

    buyer = make_order("B1", "BuyerA", Side.BUY, 105, 10)
    trades = engine.submit_order(buyer)

    assert len(trades) == 2

    assert [
        (
            trade.buy_order_id,
            trade.sell_order_id,
            trade.price_paise,
            trade.quantity,
        )
        for trade in trades
    ] == [
        ("B1", "S1", 10300, 6),
        ("B1", "S2", 10400, 4),
    ]

    assert engine.get_order("S1").remaining_quantity == 0
    assert engine.get_order("S1").status == OrderStatus.FILLED

    assert engine.get_order("S2").remaining_quantity == 4
    assert (
        engine.get_order("S2").status
        == OrderStatus.PARTIALLY_FILLED
    )

    assert buyer.remaining_quantity == 0
    assert buyer.status == OrderStatus.FILLED

    assert sum(trade.quantity for trade in trades) == 10

    total_value_paise = sum(
        trade.price_paise * trade.quantity for trade in trades
    )
    assert total_value_paise == 103400

    assert [o.order_id for o in engine.order_book.get_asks("MSFT")] == [
        "S2"
    ]


def test_best_price_has_priority():
    engine = MatchingEngine()

    engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 104, 5)
    )
    engine.submit_order(
        make_order("S2", "SellerB", Side.SELL, 103, 5)
    )

    trades = engine.submit_order(
        make_order("B1", "BuyerA", Side.BUY, 105, 5)
    )

    assert len(trades) == 1
    assert trades[0].sell_order_id == "S2"
    assert trades[0].price_paise == 10300


def test_equal_price_uses_fifo():
    engine = MatchingEngine()

    engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 103, 3)
    )
    engine.submit_order(
        make_order("S2", "SellerB", Side.SELL, 103, 3)
    )

    trades = engine.submit_order(
        make_order("B1", "BuyerA", Side.BUY, 103, 4)
    )

    assert [t.sell_order_id for t in trades] == ["S1", "S2"]
    assert [t.quantity for t in trades] == [3, 1]


def test_non_crossing_orders_do_not_trade():
    engine = MatchingEngine()

    engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 105, 5)
    )
    trades = engine.submit_order(
        make_order("B1", "BuyerA", Side.BUY, 104, 5)
    )

    assert trades == []
    assert [o.order_id for o in engine.order_book.get_asks("MSFT")] == [
        "S1"
    ]
    assert [o.order_id for o in engine.order_book.get_bids("MSFT")] == [
        "B1"
    ]


def test_sell_matches_best_resting_bid():
    engine = MatchingEngine()

    engine.submit_order(
        make_order("B1", "BuyerA", Side.BUY, 105, 5)
    )
    trades = engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 100, 5)
    )

    assert len(trades) == 1
    assert trades[0].buy_order_id == "B1"
    assert trades[0].sell_order_id == "S1"
    assert trades[0].price_paise == 10500


def test_cancel_open_order():
    engine = MatchingEngine()

    engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 103, 5)
    )

    assert engine.cancel_order("S1") is True
    assert engine.get_order("S1").status == OrderStatus.CANCELLED
    assert engine.order_book.get_asks("MSFT") == []
    assert engine.cancel_order("S1") is False


def test_cancel_partially_filled_order():
    engine = MatchingEngine()

    engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 103, 5)
    )
    engine.submit_order(
        make_order("B1", "BuyerA", Side.BUY, 103, 2)
    )

    assert engine.get_order("S1").remaining_quantity == 3
    assert engine.get_order("S1").status == OrderStatus.PARTIALLY_FILLED

    previous_trades = list(engine.trades)

    assert engine.cancel_order("S1") is True
    assert engine.get_order("S1").status == OrderStatus.CANCELLED
    assert engine.get_order("S1").remaining_quantity == 3
    assert engine.trades == previous_trades
    assert engine.order_book.get_asks("MSFT") == []


def test_duplicate_order_id_is_rejected():
    engine = MatchingEngine()

    engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 103, 5)
    )

    with pytest.raises(ValueError, match="Duplicate order ID"):
        engine.submit_order(
            make_order("S1", "SellerB", Side.SELL, 104, 5)
        )


def test_order_contract_rejects_non_positive_price():
    with pytest.raises(ValidationError):
        make_order("S1", "SellerA", Side.SELL, 0, 5)


def test_order_contract_rejects_non_positive_quantity():
    with pytest.raises(ValidationError):
        make_order("S1", "SellerA", Side.SELL, 103, 0)


def test_different_symbols_never_match():
    engine = MatchingEngine()

    engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 100, 5, symbol="MSFT")
    )
    trades = engine.submit_order(
        make_order("B1", "BuyerA", Side.BUY, 110, 5, symbol="AAPL")
    )

    assert trades == []
    assert len(engine.order_book.get_asks("MSFT")) == 1
    assert len(engine.order_book.get_bids("AAPL")) == 1


def test_incoming_order_can_be_partially_filled_and_rest_in_book():
    engine = MatchingEngine()
    engine.submit_order(make_order("S1", "SellerA", Side.SELL, 103, 6))

    buyer = make_order("B1", "BuyerA", Side.BUY, 105, 10)
    trades = engine.submit_order(buyer)

    assert [(trade.sell_order_id, trade.quantity) for trade in trades] == [
        ("S1", 6)
    ]
    assert buyer.remaining_quantity == 4
    assert buyer.status == OrderStatus.PARTIALLY_FILLED
    assert [order.order_id for order in engine.order_book.get_bids("MSFT")] == ["B1"]


def test_exact_price_match_executes_trade():
    engine = MatchingEngine()
    engine.submit_order(make_order("S1", "SellerA", Side.SELL, 103, 2))
    trades = engine.submit_order(make_order("B1", "BuyerA", Side.BUY, 103, 2))

    assert len(trades) == 1
    assert trades[0].price_paise == 10300
    assert trades[0].quantity == 2


def test_filled_order_cannot_be_cancelled():
    engine = MatchingEngine()
    engine.submit_order(make_order("S1", "SellerA", Side.SELL, 103, 2))
    engine.submit_order(make_order("B1", "BuyerA", Side.BUY, 103, 2))

    assert engine.get_order("S1").status == OrderStatus.FILLED
    assert engine.cancel_order("S1") is False


def test_unknown_order_cannot_be_cancelled():
    assert MatchingEngine().cancel_order("missing") is False


def test_whitespace_only_account_or_symbol_is_rejected():
    engine = MatchingEngine()
    with pytest.raises(ValueError, match="Account ID"):
        engine.submit_order(make_order("S1", "   ", Side.SELL, 103, 2))

    with pytest.raises(ValueError, match="Symbol"):
        engine.submit_order(
            make_order("S2", "SellerA", Side.SELL, 103, 2, symbol="   ")
        )


def test_invalid_new_order_state_is_rejected_without_recording_order():
    engine = MatchingEngine()
    invalid = make_order("S1", "SellerA", Side.SELL, 103, 2)
    invalid.status = OrderStatus.FILLED

    with pytest.raises(ValueError, match="OPEN status"):
        engine.submit_order(invalid)

    assert engine.get_order("S1") is None
    assert engine.trades == []


def test_order_from_different_symbol_does_not_consume_resting_quantity():
    engine = MatchingEngine()
    engine.submit_order(make_order("S1", "SellerA", Side.SELL, 100, 7, symbol="MSFT"))
    trades = engine.submit_order(make_order("B1", "BuyerA", Side.BUY, 110, 7, symbol="AAPL"))

    assert trades == []
    assert engine.get_order("S1").remaining_quantity == 7
    assert engine.get_order("B1").remaining_quantity == 7

def test_best_bid_has_priority():
    engine = MatchingEngine()

    # Submit the lower-priced buy order first.
    engine.submit_order(
        make_order("B1", "BuyerA", Side.BUY, 100, 5)
    )
    # Submit the higher-priced buy order second.
    engine.submit_order(
        make_order("B2", "BuyerB", Side.BUY, 105, 5)
    )

    # An incoming sell order should match the highest bid first.
    trades = engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 95, 5)
    )

    assert len(trades) == 1
    assert trades[0].buy_order_id == "B2"
    assert trades[0].sell_order_id == "S1"
    assert trades[0].price_paise == 10500


def test_equal_price_bids_use_fifo():
    engine = MatchingEngine()

    # B1 arrives before B2 at the same bid price.
    engine.submit_order(
        make_order("B1", "BuyerA", Side.BUY, 100, 3)
    )
    engine.submit_order(
        make_order("B2", "BuyerB", Side.BUY, 100, 3)
    )

    # This sell order can fill both bids, but only partially fills B2.
    trades = engine.submit_order(
        make_order("S1", "SellerA", Side.SELL, 100, 4)
    )

    assert [trade.buy_order_id for trade in trades] == ["B1", "B2"]
    assert [trade.quantity for trade in trades] == [3, 1]

    assert engine.get_order("B1").status == OrderStatus.FILLED
    assert engine.get_order("B2").status == OrderStatus.PARTIALLY_FILLED
    assert engine.get_order("B2").remaining_quantity == 2
