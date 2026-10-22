# MarketShield

MarketShield is a simulation-only limit-order exchange. It does not execute real trades or settle real money.

## Run the test suite

Install the Python dependencies, then run from this repository directory:

```bash
python -m pip install -r requirements.txt
python -m pytest
```

## Simulation engine

The Member B simulation pipeline is:

`order_generator.py` → `scenarios.py` → `runner.py` → shared `Order`/`Trade` contracts → `MatchingEngine`

- `backend/app/simulator/order_generator.py`: creates valid orders and reproducible seeded batches.
- `backend/app/simulator/scenarios.py`: declares fixed scenarios and expected trades/order states.
- `backend/app/simulator/runner.py`: runs scenarios using copies of input orders so repeated runs do not mutate the scenario definition.
- `backend/app/surveillance/features.py`: calculates transparent descriptive indicators from order data.
- `docs/simulation-engine.md`: explains the data flow and required two-trade acceptance scenario.
- `tests/`: contract, matching-engine, scenario, reproducibility, surveillance, and edge-case tests.

## Required acceptance result

The required partial-fill scenario should produce two trades:

- B1 buys 6 units from S1 at 10,300 paise.
- B1 buys 4 units from S2 at 10,400 paise.

Final remaining quantities: S1 = 0 (FILLED), S2 = 4 (PARTIALLY_FILLED), B1 = 0 (FILLED).
