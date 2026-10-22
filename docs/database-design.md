# MarketShield — Database Design (Phase 1)

## 1. Objective

Design a relational database for the internal simulated stock exchange.

Phase 1 defines the schema and relationships. Phase 2 will implement persistence, virtual-money settlement, concurrency control and transaction recovery.

## 2. Core Entities

### Users

Stores registered user information.

- `user_id` — Primary Key
- `username` — Unique
- `email` — Unique
- `password_hash` — Securely hashed password
- `created_at` — Account creation timestamp

The existing authentication database must be reviewed before introducing any new user table.

### Trading Accounts

Stores trading-account ownership.

- `account_id` — Primary Key
- `user_id` — Foreign Key referencing users
- `account_status` — ACTIVE / SUSPENDED
- `created_at` — Creation timestamp

One user may have multiple trading accounts if supported by the application.

### Cash Balances

Stores virtual-money balances.

- `account_id` — Primary Key and Foreign Key referencing accounts
- `available_paise` — Available virtual cash
- `reserved_paise` — Cash reserved for accepted buy orders

Constraints:

- Available cash must be nonnegative.
- Reserved cash must be nonnegative.

### Positions

Stores virtual-share holdings.

- `account_id` — Foreign Key referencing accounts
- `symbol` — Fictitious or supported security symbol
- `available_quantity` — Shares available to sell
- `reserved_quantity` — Shares committed to open sell orders

Primary Key: (`account_id`, `symbol`).

### Orders

Stores submitted trading instructions.

- `order_id` — Primary Key
- `account_id` — Foreign Key referencing accounts
- `symbol` — Security symbol
- `side` — BUY / SELL
- `limit_price_paise` — Limit price
- `quantity` — Original requested quantity
- `remaining_quantity` — Unexecuted quantity
- `status` — OPEN / PARTIALLY_FILLED / FILLED / CANCELLED / REJECTED
- `sequence` — Server-assigned submission priority
- `created_at` — Order creation timestamp

Constraints:

- Price and quantity must be positive.
- Remaining quantity must be between zero and original quantity.
- An order ID must be unique.
- Submission sequence must have a defined uniqueness and ordering policy.

### Trades

Stores executed matches.

- `trade_id` — Primary Key
- `buy_order_id` — Foreign Key referencing orders
- `sell_order_id` — Foreign Key referencing orders
- `buyer_account_id` — Buyer trading account
- `seller_account_id` — Seller trading account
- `symbol` — Security symbol
- `price_paise` — Execution price
- `quantity` — Executed quantity
- `sequence` — Execution sequence
- `timestamp` — Execution timestamp in UTC

Constraints:

- Price and quantity must be positive.
- Referenced buy and sell orders must exist.
- Account and symbol values must agree with the referenced orders.

### Order Events

Stores lifecycle history.

- `event_id` — Primary Key
- `order_id` — Reference to an order, when applicable
- `trade_id` — Reference to a trade, when applicable
- `account_id` — Relevant account, when applicable
- `event_type` — Accepted, rejected, partially filled, filled, cancelled or trade executed
- `sequence` — Server-assigned event sequence
- `timestamp` — Event timestamp
- `reason` — Optional rejection or cancellation explanation

A rejected request may not have an accepted order ID, so the final event schema should support request correlation.

### Ledger Transactions and Entries

Stores virtual financial movements.

**Ledger Transactions**

- `transaction_id` — Primary Key
- `trade_id` — Unique reference when settling a trade
- `transaction_type` — Deposit / reservation / release / settlement / adjustment
- `created_at` — Timestamp

**Ledger Entries**

- `entry_id` — Primary Key
- `transaction_id` — Foreign Key referencing ledger transactions
- `account_id` — Affected account
- `asset_type` — CASH / SHARE
- `symbol` — Required for share movements
- `balance_bucket` — AVAILABLE / RESERVED
- `signed_amount` — Integer movement amount

Cash and share quantities must be reconciled separately.

The final ledger design must distinguish transfers between accounts from movements between available and reserved balances.

## 3. Relationships

- One User can own many Trading Accounts.
- One Trading Account has one Cash Balance.
- One Trading Account can have many Positions.
- One Trading Account can submit many Orders.
- One Order can participate in many Trades.
- One Order can have many Order Events.
- One Ledger Transaction contains multiple Ledger Entries.
- One Trade can be linked to at most one completed settlement transaction.

## 4. Financial Integrity Requirements

1. Prevent negative available or reserved balances.
2. Require sufficient cash or shares before accepting an order.
3. Preserve existing executions when cancelling remaining quantities.
4. Prevent duplicate trade settlement.
5. Maintain a complete, traceable event and ledger history.
6. Execute related financial updates atomically.
7. Prevent concurrent transactions from spending the same reserved or available assets twice.
8. Preserve cash and share conservation across internal transfers, accounting for explicitly modeled issuance or fees.

## 5. Implementation Plan

Phase 1:
- Agree on entities, keys, constraints and relationships.
- Review compatibility with the existing authentication schema.
- Keep exchange data models aligned with the shared Python contracts.

Phase 2:
- Implement the schema in PostgreSQL.
- Add repository/data-access operations.
- Add transactional reservations and settlement.
- Enforce idempotency and transaction isolation.
- Add database integrity and concurrent-execution tests.

## 6. Scope Boundary

This document is a design specification.

It does not claim that the tables are already implemented, populated or connected to the live FastAPI application.