
from app.demo import main


def test_phase1_demo(capsys):
    main()

    output = capsys.readouterr().out

    assert "required_two_trade_partial_fill" in output
    assert "non_crossing_orders" in output
    assert "best_bid_priority" in output

    assert output.count("RESULT: PASS") == 3
    assert "ALL PHASE 1 DEMO SCENARIOS PASSED" in output
