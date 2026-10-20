# MarketShield Matching Engine Test Plan

## A. Basic Matching

### A1. Exact match
- Resting SELL: 5 units at ?100.
- Incoming BUY: 5 units at ?100.
- Expected: one trade for 5 units at ?100; both orders FILLED.

### A2. No price crossing
- Resting SELL: 5 units at ?105.
- Incoming BUY: 5 units at ?104.
- Expected: no trade; both orders remain in their respective books.

### A3. Incoming BUY crosses an ask
- Resting SELL: 5 units at ?100.
- Incoming BUY: 5 units at ?105.
- Expected: one trade at ?100, the resting SELL price.

### A4. Incoming SELL crosses a bid
- Resting BUY: 5 units at ?105.
- Incoming SELL: 5 units at ?100.
- Expected: one trade at ?105, the resting BUY price.

## B. Price-Time Priority

### B1. Best ask first
- S1: 5 units at ?104.
- S2: 5 units at ?103.
- B1: 5 units at ?105.
- Expected: B1 matches S2 first.

### B2. Best bid first
- B1: 5 units at ?103.
- B2: 5 units at ?104.
- S1: 5 units at ?102.
- Expected: S1 matches B2 first.

### B3. FIFO at equal ask prices
- S1: 3 units at ?103, submitted first.
- S2: 3 units at ?103, submitted second.
- B1: 4 units at ?103.
- Expected: S1 fills 3 units, then S2 fills 1 unit.

### B4. FIFO at equal bid prices
- B1: 3 units at ?103, submitted first.
- B2: 3 units at ?103, submitted second.
- S1: 4 units at ?103.
- Expected: B1 fills 3 units, then B2 fills 1 unit.

## C. Partial Fills

### C1. Incoming order is partially filled
- S1: 3 units at ?100.
- B1: 5 units at ?100.
- Expected: trade for 3 units; B1 remains OPEN with 2 units.

### C2. One incoming order matches multiple orders
- S1: 2 units at ?100.
- S2: 4 units at ?101.
- B1: 5 units at ?105.
- Expected: two trades for 2 and 3 units.
- S1 FILLED; S2 PARTIALLY_FILLED with 1 remaining; B1 FILLED.

## D. Cancellation

### D1. Cancel an OPEN order
- Submit an unmatched SELL order and cancel it.
- Expected: CANCELLED and removed from the book.

### D2. Cancel a partially filled order
- Partially execute a resting order, then cancel its remainder.
- Expected: previous trades unchanged; remainder removed.

### D3. Repeat cancellation
- Cancel the same order twice.
- Expected: first succeeds; second safely fails.

### D4. Unknown order
- Cancel an unknown order ID.
- Expected: safe failure with no book mutation or trade.

## E. Validation and Isolation

### E1. Duplicate order ID
- Submit two orders with the same ID.
- Expected: reject the second order.

### E2. Invalid quantity
- Submit zero or negative quantity.
- Expected: reject.

### E3. Invalid price
- Submit zero or negative limit price.
- Expected: reject.

### E4. Different symbols
- Submit BUY and SELL orders for different symbols.
- Expected: no cross-symbol execution.

## F. Required Team Acceptance Scenario

- S1: SELL 6 units at ?103.
- S2: SELL 8 units at ?104.
- B1: BUY 10 units at ?105.

Expected results:
1. B1 buys 6 units from S1 at ?103.
2. B1 buys 4 units from S2 at ?104.
3. S1 is FILLED.
4. S2 has 4 units remaining and is PARTIALLY_FILLED.
5. B1 is FILLED.
6. Exactly two trades execute.
7. Total executed quantity is 10.
8. Total trade value is ?1,034 before fees.

## Test Completion Criteria

- Every case has automated assertions.
- No order has negative remaining quantity.
- Buy and sell quantities agree for every trade.
- Price-time priority is deterministic.
- The required team scenario passes.
