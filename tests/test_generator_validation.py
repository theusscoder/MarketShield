
import pytest

from app.simulator.order_generator import generate_orders


@pytest.mark.parametrize(
    "invalid_symbols",
    [
        "MSFT",
        123,
        None,
        [],
        ["MSFT", ""],
        ["MSFT", 42],
    ],
)
def test_rejects_invalid_symbols(invalid_symbols):
    with pytest.raises(ValueError):
        generate_orders(
            seed=1,
            count=3,
            symbols=invalid_symbols,
        )


def test_valid_symbols_still_work():
    orders = generate_orders(
        seed=42,
        count=5,
        symbols=("MSFT", "AAPL"),
    )

    assert len(orders) == 5

    assert all(
        order.symbol in ("MSFT", "AAPL")
        for order in orders
    )


def test_same_seed_produces_same_orders():
    first = generate_orders(seed=42, count=5)
    second = generate_orders(seed=42, count=5)

    assert [
        order.model_dump() for order in first
    ] == [
        order.model_dump() for order in second
    ]
