
from app.contracts.order import OrderStatus, Side
from app.contracts.trade import Trade
from app.simulator.order_generator import generate_order
from app.surveillance.rules import (
    SurveillanceThresholds,
    detect_suspicious_activity,
)
from app.simulator.scenarios import (
    non_crossing_scenario,
    required_two_trade_scenario,
    single_trade_partial_fill_scenario,
    unusual_activity_scenario,
)
from app.simulator.runner import run_scenario

import pytest


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_orders_for_activity": 0},
        {"min_orders_for_activity": -1},
        {"min_orders_for_cancellation_check": 0},
        {"min_order_notional_paise": 0},
        {"cancellation_ratio_limit": -0.1},
        {"cancellation_ratio_limit": 1.1},
        {"max_fill_ratio_for_large_order": -0.1},
        {"max_fill_ratio_for_large_order": 1.1},
    ],
)
def test_invalid_surveillance_thresholds_are_rejected(kwargs):
    with pytest.raises(ValueError):
        SurveillanceThresholds(**kwargs)


def make_order(order_id, account_id, side=Side.BUY, quantity=10,
               price=100, status=OrderStatus.OPEN, remaining=None):
    order = generate_order(
        order_id=order_id,
        account_id=account_id,
        symbol="MSFT",
        side=side,
        limit_price_paise=price,
        quantity=quantity,
    )
    order.status = status
    if remaining is not None:
        order.remaining_quantity = remaining
    return order


def test_high_account_activity_triggers_alert():
    orders = [
        make_order("O1", "A"),
        make_order("O2", "A"),
        make_order("O3", "A"),
    ]

    alerts = detect_suspicious_activity(orders)

    assert any(
        alert.rule == "SURV-001" and alert.account_id == "A"
        for alert in alerts
    )


def test_high_cancellation_ratio_triggers_alert():
    orders = [
        make_order("O1", "A", status=OrderStatus.CANCELLED),
        make_order("O2", "A", status=OrderStatus.CANCELLED),
        make_order("O3", "A"),
    ]

    alerts = detect_suspicious_activity(orders)

    assert any(
        alert.rule == "SURV-002" and alert.account_id == "A"
        for alert in alerts
    )


def test_large_mostly_unfilled_order_triggers_alert():
    orders = [
        make_order(
            "O1",
            "A",
            quantity=100,
            price=20_000,
            remaining=80,
            status=OrderStatus.PARTIALLY_FILLED,
        )
    ]

    alerts = detect_suspicious_activity(orders)

    assert any(
        alert.rule == "SURV-003" and alert.account_id == "A"
        for alert in alerts
    )


def test_same_account_buy_and_sell_trade_triggers_alert():
    buy = make_order("B1", "A", side=Side.BUY)
    sell = make_order("S1", "A", side=Side.SELL)

    trade = Trade(
        trade_id="T1",
        symbol="MSFT",
        buy_order_id="B1",
        sell_order_id="S1",
        price_paise=100,
        quantity=5,
        sequence=1,
    )

    alerts = detect_suspicious_activity([buy, sell], [trade])

    assert any(
        alert.rule == "SURV-004" and alert.account_id == "A"
        for alert in alerts
    )


def test_normal_activity_does_not_trigger_alerts():
    orders = [
        make_order("O1", "A", quantity=2, price=100),
        make_order("O2", "B", quantity=2, price=100),
    ]

    assert detect_suspicious_activity(orders) == []


def test_empty_inputs_return_no_alerts():
    assert detect_suspicious_activity([]) == []
    assert detect_suspicious_activity([], []) == []


def test_detector_is_reproducible():
    orders = [
        make_order("O1", "A"),
        make_order("O2", "A"),
        make_order("O3", "A"),
    ]

    first = detect_suspicious_activity(orders)
    second = detect_suspicious_activity(orders)

    assert [alert.model_dump() for alert in first] == [
        alert.model_dump() for alert in second
    ]


def test_required_two_trade_scenario_does_not_trigger_suspicious_alerts():
    scenario = required_two_trade_scenario()
    _, trades = run_scenario(scenario)

    alerts = detect_suspicious_activity(scenario.orders, trades)

    assert not any(
        alert.rule == "SURV-004"
        for alert in alerts
    )


def test_non_crossing_scenario_does_not_trigger_suspicious_alerts():
    scenario = non_crossing_scenario()
    _, trades = run_scenario(scenario)

    alerts = detect_suspicious_activity(scenario.orders, trades)

    assert not any(
        alert.rule == "SURV-004"
        for alert in alerts
    )


def test_single_partial_fill_scenario_does_not_trigger_self_trade_alert():
    scenario = single_trade_partial_fill_scenario()
    _, trades = run_scenario(scenario)

    alerts = detect_suspicious_activity(scenario.orders, trades)

    assert not any(
        alert.rule == "SURV-004"
        for alert in alerts
    )


def test_unusual_activity_scenario_flags_high_activity_account():
    scenario = unusual_activity_scenario()

    alerts = detect_suspicious_activity(scenario.orders)

    assert any(
        alert.account_id == "HighActivityAccount"
        and alert.rule == "SURV-001"
        for alert in alerts
    )


def test_alert_ids_are_stable_when_input_order_changes():
    orders = [
        make_order("O1", "A"),
        make_order("O2", "A"),
        make_order("O3", "A"),
    ]

    first = detect_suspicious_activity(orders)
    second = detect_suspicious_activity(list(reversed(orders)))

    assert sorted(alert.alert_id for alert in first) == sorted(
        alert.alert_id for alert in second
    )
