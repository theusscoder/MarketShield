# Initial Surveillance Feature Definitions

These deterministic features support basic review of order activity. They are descriptive indicators, not proof of manipulation or a standalone alerting model.

All monetary values use integer paise, matching the exchange contracts.

| Feature | Definition | Boundary behavior |
|---|---|---|
| Order notional | `limit_price_paise * quantity` | Integer paise; uses original order quantity. |
| Fill ratio | `(quantity - remaining_quantity) / quantity` | 0 for an untouched order; 1 for a fully executed order. |
| Remaining ratio | `remaining_quantity / quantity` | 1 for an untouched order; 0 for a fully executed order. |
| Account order activity | Count of supplied orders grouped by `account_id` | Empty input returns `{}`. Counts only the supplied dataset; it is not a time-windowed rate. |
| Cancellation ratio | Number of supplied orders with `CANCELLED` status divided by the number of supplied orders | Empty input returns `0.0`. A cancelled partially filled order still counts as one cancelled order. |

## Input and interpretation notes

- Functions operate only on the orders passed to them and do not mutate those orders.
- `Order` contracts require positive original quantity and non-negative remaining quantity no greater than original quantity, so ratio denominators are non-zero for valid contract instances.
- Features should be computed against a clearly defined observation window in a production surveillance pipeline. These helpers do not infer timestamps or fetch external data.
- High notional, low fill ratio, high remaining ratio, repeated orders, or cancellations may justify further review, but legitimate market activity can exhibit the same patterns. Do not treat any single feature as a conclusion about intent.
