# MarketShield Financial Integrity Rules

## 1. Purpose

The financial ledger manages virtual cash and share holdings
for the internal simulated exchange.

The matching engine decides which orders trade.
The ledger records the resulting financial transfers.

## 2. Balance Representation

Each trading account has:

- Available cash
- Reserved cash
- Available shares per symbol
- Reserved shares per symbol

All cash values are represented as integer paise.

## 3. Cash Reservation

Before accepting a BUY order:

Required cash = limit_price_paise * quantity

Reject the order if available cash is insufficient.

Otherwise:

available_cash -= required_cash
reserved_cash += required_cash

## 4. Share Reservation

Before accepting a SELL order:

Reject if available shares < order quantity.

Otherwise:

available_shares -= quantity
reserved_shares += quantity

## 5. Trade Settlement

When a trade executes:

Trade value = execution_price_paise * executed_quantity

Buyer:
- Receives executed shares
- Pays the actual trade value
- Releases the corresponding reservation
- Receives any excess reserved cash back

Seller:
- Receives the trade value
- Transfers executed shares from reserved holdings

## 6. Partial Fills

When only part of an order executes:

- Settle only the executed quantity.
- Keep sufficient assets reserved for the remaining open quantity.
- Do not refund reservations required for the unfilled portion.

## 7. Cancellation

Cancelling an order:

- Does not reverse completed trades.
- Releases only the reservation associated with its remaining quantity.
- Must not release assets more than once.

## 8. Invariants

1. Available balances cannot be negative.
2. Reserved balances cannot be negative.
3. An order cannot commit assets the account does not own.
4. A trade is settled at most once.
5. Each financial movement is traceable to an order or trade.
6. Reservations must be consistent with open order obligations.
7. Internal trades conserve total virtual cash and shares,
   excluding explicitly modeled fees or issuance.
8. Financial operations must be atomic.

## 9. Phase 2 Implementation

Implement these rules using PostgreSQL transactions,
database constraints, unique settlement IDs, row-level
locking where required, and append-only ledger entries.