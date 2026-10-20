
# MarketShield Matching Engine Design

## 1. Components

### OrderBook
Responsibilities:
- Store resting BUY orders and SELL orders by symbol.
- Return the best opposing order for an incoming order.
- Maintain price-time priority.
- Remove fully filled and cancelled orders.
- Expose read-only snapshots of bids and asks.

### MatchingEngine
Responsibilities:
- Validate new orders.
- Assign authoritative order sequence numbers.
- Find matching opposing orders.
- Calculate execution quantity and price.
- Update order quantities and statuses.
- Create Trade records.
- Assign execution sequence numbers.
- Support cancellation.

## 2. Order Book Ordering

BUY orders:
    Sort by (-limit_price_paise, sequence)

SELL orders:
    Sort by (limit_price_paise, sequence)

The negative buy price places higher bids first when using ascending sort.

## 3. Matching Algorithm

Input: incoming order

1. Validate the order.
2. Assign its engine sequence.
3. Find the best opposing order for the same symbol.
4. If no opposing order exists, stop matching.
5. Check whether the incoming and resting limit prices cross.
6. If prices do not cross, stop matching.
7. Calculate the smaller remaining quantity.
8. Determine which order is BUY and which is SELL.
9. Use the resting order's limit price as execution price.
10. Create a Trade record with an execution sequence.
11. Subtract the execution quantity from both orders.
12. Remove the resting order if fully filled.
13. Otherwise retain it as PARTIALLY_FILLED.
14. Repeat while the incoming order has remaining quantity and a match exists.
15. If the incoming order has remaining quantity, add it to the book.
16. Return the trades produced by this submission.

## 4. Cancellation Algorithm

1. Find the order by ID.
2. Reject cancellation if the order is unknown.
3. Reject cancellation if it is already FILLED or CANCELLED.
4. Confirm that it is still resting in the book.
5. Remove it from the book.
6. Mark it CANCELLED.
7. Preserve all previous trade records.

## 5. Complexity Notes

For a simple Python list-based order book:
- Inserting an order requires sorting, approximately O(n log n).
- Finding the best order is O(1) after sorting.
- Removing an order from a list is O(n).
- Searching all resting orders by ID is O(n).

This is acceptable for a small Phase 1 prototype. A heap, balanced tree, or indexed order book can be considered later if performance requires it.

## 6. Design Boundaries

- Use Member C's canonical Order and Trade classes.
- Do not create duplicate shared contracts.
- Keep the initial matching path sequential.
- Do not mix account balance settlement into the matching algorithm.
- Keep API and database concerns outside OrderBook.
- Do not add AI surveillance logic to MatchingEngine.
