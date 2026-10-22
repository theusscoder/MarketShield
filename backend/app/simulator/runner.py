"""Run a scenario through the shared contracts and matching engine."""

from app.contracts.trade import Trade
from app.exchange.matching_engine import MatchingEngine
from app.simulator.scenarios import Scenario


def run_scenario(scenario: Scenario) -> tuple[MatchingEngine, list[Trade]]:
    """Run a fresh copy of each input order and return engine plus trades.

    Orders are mutable because matching changes their remaining quantities
    and statuses. Deep-copying them prevents one run from corrupting the
    reusable scenario definition or changing the next run's result.
    """
    engine = MatchingEngine()
    trades: list[Trade] = []

    for template_order in scenario.orders:
        order = template_order.model_copy(deep=True)
        trades.extend(engine.submit_order(order))

    return engine, trades
