import pytest
from pydantic import ValidationError

from app.contracts.order import OrderStatus, Side
from app.exchange.matching_engine import MatchingEngine
from app.simulator.order_generator import generate_order, generate_orders
from app.simulator.runner import run_scenario
from app.simulator.scenarios import non_crossing_scenario, required_two_trade_scenario
from app.surveillance.features import (
    account_order_activity,
    cancellation_ratio,
    fill_ratio,
    order_notional_paise,
    remaining_ratio,
)


def trade_signature(trades):
    # Trade IDs are UUIDs; business outcomes, not random IDs, must reproduce.
    return [
        (t.buy_order_id, t.sell_order_id, t.price_paise, t.quantity, t.sequence)
        for t in trades
    ]


def test_required_scenario_produces_expected_two_trades_and_remaining_quantities():
    scenario = required_two_trade_scenario()
    engine, trades = run_scenario(scenario)

    assert trade_signature(trades) == [
        (expected.buy_order_id, expected.sell_order_id,
         expected.price_paise, expected.quantity, index)
        for index, expected in enumerate(scenario.expected_trades, start=1)
    ]
    assert len(trades) == 2
    assert sum(trade.quantity for trade in trades) == 10
    assert sum(trade.price_paise * trade.quantity for trade in trades) == 103_400

    for expected in scenario.expected_orders:
        actual = engine.get_order(expected.order_id)
        assert actual is not None
        assert actual.status == expected.status
        assert actual.remaining_quantity == expected.remaining_quantity
        assert 0 <= actual.remaining_quantity <= actual.quantity

    assert [order.order_id for order in engine.order_book.get_asks("MSFT")] == ["S2"]
    assert engine.order_book.get_asks("MSFT")[0].remaining_quantity == 4
    assert engine.order_book.get_bids("MSFT") == []


def test_scenario_reproducibility_across_fresh_runs():
    first_engine, first_trades = run_scenario(required_two_trade_scenario())
    second_engine, second_trades = run_scenario(required_two_trade_scenario())

    assert trade_signature(first_trades) == trade_signature(second_trades)
    for order_id in ("S1", "S2", "B1"):
        first = first_engine.get_order(order_id)
        second = second_engine.get_order(order_id)
        assert (first.status, first.remaining_quantity) == (
            second.status, second.remaining_quantity
        )


def test_non_crossing_scenario_leaves_both_orders_open_and_creates_no_trades():
    scenario = non_crossing_scenario()
    engine, trades = run_scenario(scenario)

    assert trades == []
    for expected in scenario.expected_orders:
        actual = engine.get_order(expected.order_id)
        assert actual.status == expected.status
        assert actual.remaining_quantity == expected.remaining_quantity
    assert [order.order_id for order in engine.order_book.get_asks("MSFT")] == ["S1"]
    assert [order.order_id for order in engine.order_book.get_bids("MSFT")] == ["B1"]


def test_generator_creates_fresh_valid_order_each_time():
    kwargs = dict(
        order_id="B1", account_id="BuyerA", symbol="MSFT", side=Side.BUY,
        limit_price_paise=10500, quantity=10,
    )
    first = generate_order(**kwargs)
    second = generate_order(**kwargs)
    assert first is not second
    assert first.model_dump() == second.model_dump()
    assert first.remaining_quantity == first.quantity == 10
    assert first.sequence == 0
    assert first.status == OrderStatus.OPEN


@pytest.mark.parametrize("price,quantity", [(0, 1), (-1, 1), (100, 0), (100, -1)])
def test_generator_rejects_non_positive_price_or_quantity(price, quantity):
    with pytest.raises(ValidationError):
        generate_order(
            order_id="O1", account_id="A1", symbol="MSFT", side=Side.BUY,
            limit_price_paise=price, quantity=quantity,
        )


def test_generator_rejects_invalid_side():
    with pytest.raises(ValidationError):
        generate_order(
            order_id="O1", account_id="A1", symbol="MSFT", side="HOLD",
            limit_price_paise=100, quantity=1,
        )


def test_surveillance_order_features_for_unfilled_and_partial_orders():
    unfilled = generate_order(
        order_id="S1", account_id="A", symbol="MSFT", side=Side.SELL,
        limit_price_paise=10300, quantity=6,
    )
    partial = generate_order(
        order_id="S2", account_id="A", symbol="MSFT", side=Side.SELL,
        limit_price_paise=10400, quantity=8,
    )
    partial.remaining_quantity = 4
    partial.status = OrderStatus.PARTIALLY_FILLED

    assert order_notional_paise(unfilled) == 61_800
    assert fill_ratio(unfilled) == 0.0
    assert remaining_ratio(unfilled) == 1.0
    assert order_notional_paise(partial) == 83_200
    assert fill_ratio(partial) == 0.5
    assert remaining_ratio(partial) == 0.5
    assert account_order_activity([unfilled, partial]) == {"A": 2}
    assert cancellation_ratio([unfilled, partial]) == 0.0


def test_surveillance_cancellation_ratio_and_empty_inputs():
    active = generate_order(
        order_id="O1", account_id="A", symbol="MSFT", side=Side.BUY,
        limit_price_paise=100, quantity=1,
    )
    cancelled = generate_order(
        order_id="O2", account_id="B", symbol="MSFT", side=Side.SELL,
        limit_price_paise=100, quantity=1,
    )
    cancelled.status = OrderStatus.CANCELLED

    assert cancellation_ratio([active, cancelled]) == 0.5
    assert cancellation_ratio([]) == 0.0
    assert account_order_activity([]) == {}


def test_surveillance_features_cover_fully_filled_and_cancelled_partial_orders():
    filled = generate_order(
        order_id="F1", account_id="A", symbol="MSFT", side=Side.BUY,
        limit_price_paise=250, quantity=4,
    )
    filled.remaining_quantity = 0
    filled.status = OrderStatus.FILLED

    cancelled_partial = generate_order(
        order_id="C1", account_id="B", symbol="MSFT", side=Side.SELL,
        limit_price_paise=300, quantity=10,
    )
    cancelled_partial.remaining_quantity = 7
    cancelled_partial.status = OrderStatus.CANCELLED

    assert fill_ratio(filled) == 1.0
    assert remaining_ratio(filled) == 0.0
    assert fill_ratio(cancelled_partial) == 0.3
    assert remaining_ratio(cancelled_partial) == 0.7
    assert cancellation_ratio([filled, cancelled_partial]) == 0.5
    assert account_order_activity([filled, cancelled_partial]) == {"A": 1, "B": 1}


def test_seeded_generator_reproduces_all_order_fields():
    first = generate_orders(seed=2026, count=25)
    second = generate_orders(seed=2026, count=25)

    assert [order.model_dump() for order in first] == [
        order.model_dump() for order in second
    ]
    assert [order.order_id for order in first] == [
        f"SIM-{index:06d}" for index in range(1, 26)
    ]


def test_seeded_generator_changes_sequence_when_seed_changes():
    first = generate_orders(seed=10, count=10)
    second = generate_orders(seed=11, count=10)

    assert [order.model_dump() for order in first] != [
        order.model_dump() for order in second
    ]


def test_seeded_generator_handles_zero_orders():
    assert generate_orders(seed=1, count=0) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": 1, "count": -1},
        {"seed": 1, "count": 1, "symbols": ()},
        {"seed": 1, "count": 1, "symbols": ("",)},
        {"seed": 1, "count": 1, "account_count": 0},
    ],
)
def test_seeded_generator_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        generate_orders(**kwargs)


def test_same_scenario_object_can_be_run_repeatedly_without_mutation():
    scenario = required_two_trade_scenario()
    original_orders = [order.model_dump() for order in scenario.orders]

    first_engine, first_trades = run_scenario(scenario)
    second_engine, second_trades = run_scenario(scenario)

    assert trade_signature(first_trades) == trade_signature(second_trades)
    assert [order.model_dump() for order in scenario.orders] == original_orders
    assert first_engine.get_order("S2").remaining_quantity == 4
    assert second_engine.get_order("S2").remaining_quantity == 4


def test_non_crossing_scenario_matches_declared_expectations():
    scenario = non_crossing_scenario()
    engine, trades = run_scenario(scenario)

    assert trades == []
    assert len(trades) == len(scenario.expected_trades)
    for expected in scenario.expected_orders:
        actual = engine.get_order(expected.order_id)
        assert actual.status == expected.status
        assert actual.remaining_quantity == expected.remaining_quantity
