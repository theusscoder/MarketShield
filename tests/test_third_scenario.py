
from app.simulator.runner import run_scenario
from app.simulator.scenarios import best_bid_priority_scenario


def execution_details(trades):
    return [
        (
            trade.buy_order_id,
            trade.sell_order_id,
            trade.price_paise,
            trade.quantity,
            trade.sequence,
        )
        for trade in trades
    ]


def test_best_bid_priority_scenario():
    scenario = best_bid_priority_scenario()
    engine, trades = run_scenario(scenario)

    assert len(trades) == len(scenario.expected_trades)

    for actual, expected in zip(
        trades, scenario.expected_trades
    ):
        assert actual.buy_order_id == expected.buy_order_id
        assert actual.sell_order_id == expected.sell_order_id
        assert actual.price_paise == expected.price_paise
        assert actual.quantity == expected.quantity

    for expected in scenario.expected_orders:
        actual = engine.get_order(expected.order_id)

        assert actual is not None
        assert actual.status == expected.status
        assert actual.remaining_quantity == expected.remaining_quantity


def test_best_bid_priority_scenario_is_repeatable():
    scenario = best_bid_priority_scenario()

    _, first_trades = run_scenario(scenario)
    _, second_trades = run_scenario(scenario)

    assert execution_details(first_trades) == execution_details(
        second_trades
    )
