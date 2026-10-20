import pytest
from pydantic import ValidationError

from app.contracts.order import OrderRequest


def test_valid_order():
    order = OrderRequest(
        symbol="DEMO",
        side="BUY",
        limit_price_paise=10500,
        quantity=10
    )

    assert order.quantity == 10


def test_negative_quantity():
    with pytest.raises(ValidationError):
        OrderRequest(
            symbol="DEMO",
            side="BUY",
            limit_price_paise=10500,
            quantity=-5
        )


def test_invalid_side():
    with pytest.raises(ValidationError):
        OrderRequest(
            symbol="DEMO",
            side="HOLD",
            limit_price_paise=10500,
            quantity=10
        )


def test_zero_price():
    with pytest.raises(ValidationError):
        OrderRequest(
            symbol="DEMO",
            side="SELL",
            limit_price_paise=0,
            quantity=5
        )