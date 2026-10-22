
"""Runnable MarketShield Phase 1 integration demonstration."""
from app.simulator.runner import run_scenario
from app.simulator.scenarios import (
    required_two_trade_scenario,
    single_trade_partial_fill_scenario,
    non_crossing_scenario,
    best_bid_priority_scenario,
    unusual_activity_scenario,
    equal_price_fifo_scenario,
)


def display_scenario(scenario):
    print("\n" + "=" * 60)
    print(f"MARKETSHIELD SCENARIO: {scenario.name}")
    print("=" * 60)

    print("\nSUBMITTED ORDERS")

    for order in scenario.orders:
        print(
            f"{order.order_id}: "
            f"{order.side.value} "
            f"{order.quantity} shares of {order.symbol} "
            f"@ Rs.{order.limit_price_paise / 100:.2f}"
        )

    # Actual execution happens inside the existing runner.
    engine, trades = run_scenario(scenario)

    print("\nEXECUTED TRADES")

    if not trades:
        print("No trades executed.")

    for trade in trades:
        print(
            f"{trade.buy_order_id} buys "
            f"{trade.quantity} shares from "
            f"{trade.sell_order_id} "
            f"@ Rs.{trade.price_paise / 100:.2f}"
        )

    print("\nFINAL ORDER STATES")

    for expected in scenario.expected_orders:
        actual = engine.get_order(expected.order_id)

        assert actual is not None, (
            f"Missing order: {expected.order_id}"
        )

        print(
            f"{actual.order_id}: "
            f"{actual.status.value}, "
            f"remaining={actual.remaining_quantity}"
        )

        assert actual.status == expected.status, (
            f"Incorrect status: {actual.order_id}"
        )

        assert actual.remaining_quantity == expected.remaining_quantity, (
            f"Incorrect remaining quantity: {actual.order_id}"
        )

    assert len(trades) == len(scenario.expected_trades), (
        "Incorrect number of executed trades"
    )

    for actual, expected in zip(trades, scenario.expected_trades):
        assert actual.buy_order_id == expected.buy_order_id
        assert actual.sell_order_id == expected.sell_order_id
        assert actual.price_paise == expected.price_paise
        assert actual.quantity == expected.quantity

    print("\nRESULT: PASS")


def main():
    print("\nMARKETSHIELD - PHASE 1 INTEGRATION DEMO")

    scenarios = [
    required_two_trade_scenario(),
    single_trade_partial_fill_scenario(),
    non_crossing_scenario(),
    best_bid_priority_scenario(),
    unusual_activity_scenario(),
    equal_price_fifo_scenario(),
]

    for scenario in scenarios:
        display_scenario(scenario)

    print("\nALL PHASE 1 DEMO SCENARIOS PASSED")


if __name__ == "__main__":
    main()
