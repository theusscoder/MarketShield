import pytest
from pydantic import ValidationError

from app.contracts.order import Order, OrderRequest, OrderStatus, Side


def test_valid_order_request():
    order = OrderRequest(
        symbol="DEMO",
        side=Side.BUY,
        limit_price_paise=10500,
        quantity=10,
    )
    assert order.quantity == 10


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_request_rejects_non_positive_quantity(quantity):
    with pytest.raises(ValidationError):
        OrderRequest(
            symbol="DEMO",
            side=Side.BUY,
            limit_price_paise=10500,
            quantity=quantity,
        )


@pytest.mark.parametrize("price", [0, -1])
def test_order_request_rejects_non_positive_price(price):
    with pytest.raises(ValidationError):
        OrderRequest(
            symbol="DEMO",
            side=Side.SELL,
            limit_price_paise=price,
            quantity=1,
        )


def test_order_request_rejects_invalid_side():
    with pytest.raises(ValidationError):
        OrderRequest(
            symbol="DEMO",
            side="HOLD",
            limit_price_paise=10500,
            quantity=1,
        )


@pytest.mark.parametrize("symbol", ["", "A" * 21])
def test_order_request_rejects_invalid_symbol_length(symbol):
    with pytest.raises(ValidationError):
        OrderRequest(
            symbol=symbol,
            side=Side.BUY,
            limit_price_paise=100,
            quantity=1,
        )


def test_order_rejects_remaining_quantity_above_original_quantity():
    with pytest.raises(ValidationError):
        Order(
            order_id="O1",
            account_id="A1",
            symbol="DEMO",
            side=Side.BUY,
            limit_price_paise=100,
            quantity=3,
            remaining_quantity=4,
            sequence=0,
            status=OrderStatus.OPEN,
        )


def test_order_rejects_negative_remaining_quantity():
    with pytest.raises(ValidationError):
        Order(
            order_id="O1",
            account_id="A1",
            symbol="DEMO",
            side=Side.BUY,
            limit_price_paise=100,
            quantity=3,
            remaining_quantity=-1,
            sequence=0,
            status=OrderStatus.OPEN,
        )
