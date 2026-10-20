
# MarketShield Exchange Rules

## 1. Scope

MarketShield is a simulation-only limit-order exchange. It does not execute real
financial transactions or settle real money.

## 2. Order Fields

Each accepted order must identify:
- order ID
- account ID
- stock symbol
- side: BUY or SELL
- limit price in integer paise
- original quantity
- remaining quantity
- engine-assigned submission sequence
- current order status

The shared contract maintained by Member C is the source of truth for field
names and types.

## 3. Price-Time Priority

### Buy orders (bids)
1. Highest limit price has priority.
2. If prices are equal, the earliest accepted order has priority.

### Sell orders (asks)
1. Lowest limit price has priority.
2. If prices are equal, the earliest accepted order has priority.

The engine assigns submission sequence numbers. Client-provided timestamps
must not determine priority.

## 4. Matching Conditions

An incoming BUY order can match the best SELL order when:

    buy_limit_price >= sell_limit_price

An incoming SELL order can match the best BUY order when:

    sell_limit_price <= buy_limit_price

Matching continues until the incoming order is filled or no compatible
opposing order remains.

## 5. Execution Price

The execution price is the limit price of the resting order.

Prices are represented in integer paise. For example:

    ₹103 = 10300 paise

Floating-point prices must not be used for exchange calculations.

## 6. Partial Fills

Trade quantity is:

    min(incoming_remaining_quantity, resting_remaining_quantity)

The executed quantity is subtracted from both orders.

An order with zero remaining quantity is FILLED. An order that has executed
some quantity but still has a remainder is PARTIALLY_FILLED.

An unexecuted resting order is OPEN.

## 7. Cancellation

Only an OPEN or PARTIALLY_FILLED order still resting in the order book can
be cancelled.

Cancellation removes its remaining quantity from the book. It does not
reverse trades that have already executed.

Repeated cancellation and cancellation of unknown or filled orders must
not create trades or alter existing executions.

## 8. Trade Records

Each execution records:
- trade ID
- symbol
- buy order ID
- sell order ID
- buyer account ID
- seller account ID
- execution price in paise
- execution quantity
- engine-assigned execution sequence
- timestamp

Each trade must have a positive price and positive quantity.

## 9. Core Invariants

- Remaining quantity is never negative.
- Remaining quantity never exceeds original quantity.
- A trade cannot execute more quantity than either order has remaining.
- Buy and sell quantities for each trade are equal.
- Each accepted order has a unique ID.
- Execution sequence numbers increase monotonically.
- Orders from different symbols must never match.
- Cancelled orders must never execute again.

## 10. Phase 1 Non-Goals

- Real-money settlement
- Brokerage or fees
- Live market data
- Persistent order-book recovery
- Concurrent matching
- Authentication and authorization
- Advanced order types
- Production exchange compliance
