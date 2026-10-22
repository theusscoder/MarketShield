
"""Run and display a deterministic MarketShield exchange demo."""

from app.simulator.runner import run_scenario
from app.simulator.scenarios import equal_price_fifo_scenario


def main() -> None:
    scenario = equal_price_fifo_scenario()
    engine, trades = run_scenario(scenario)

    print("=" * 60)
    print("MARKETSHIELD - EXCHANGE SIMULATION DEMO")
    print("=" * 60)
    print(f"Scenario: {scenario.name}")
    print(f"Submitted orders: {len(scenario.orders)}")
    print(f"Executed trades: {len(trades)}")

    print("\nTRADE HISTORY")
    print("-" * 60)

    if not trades:
        print("No trades executed.")
    else:
        for trade in trades:
            print(
                f"Trade #{trade.sequence}: "
                f"Buyer={trade.buyer_account_id}, "
                f"Seller={trade.seller_account_id}, "
                f"Symbol={trade.symbol}, "
                f"Quantity={trade.quantity}, "
                f"Price=Rs.{trade.price_paise / 100:.2f}"
            )

    print("\nFINAL ORDER STATES")
    print("-" * 60)

    for expected in scenario.expected_orders:
        order = engine.get_order(expected.order_id)
        if order is None:
            print(f"{expected.order_id}: not resting in the book")
            continue

        print(
            f"Order={order.order_id}, "
            f"Side={order.side.value}, "
            f"Status={order.status.value}, "
            f"Original quantity={order.quantity}, "
            f"Remaining quantity={order.remaining_quantity}"
        )

    print("\nREMAINING SELL ORDERS")
    print("-" * 60)

    asks = engine.order_book.get_asks("MSFT")
    if not asks:
        print("No resting sell orders.")
    else:
        for order in asks:
            print(
                f"{order.order_id}: "
                f"Price=Rs.{order.limit_price_paise / 100:.2f}, "
                f"Remaining={order.remaining_quantity}"
            )

    print("\nDEMO COMPLETE")


if __name__ == "__main__":
    main()
