
from app.demo import main


def test_phase1_demo(capsys):
    main()

    output = capsys.readouterr().out

    expected_scenarios = [
        "required_two_trade_partial_fill",
        "single_trade_partial_fill",
        "non_crossing_orders",
        "best_bid_priority",
        "unusual_large_order_activity",
        "equal_price_fifo_partial_fill",
    ]

    for scenario in expected_scenarios:
        assert scenario in output

    assert output.count("RESULT: PASS") == len(expected_scenarios)
    assert "ALL PHASE 1 DEMO SCENARIOS PASSED" in output
