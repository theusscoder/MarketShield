from enum import Enum
from pydantic import BaseModel, Field, model_validator


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    side: Side
    limit_price_paise: int = Field(gt=0)
    quantity: int = Field(gt=0)


class Order(OrderRequest):
    order_id: str
    account_id: str
    remaining_quantity: int = Field(ge=0)
    sequence: int = Field(ge=0)
    status: OrderStatus

    @model_validator(mode="after")
    def check_remaining(self):
        if self.remaining_quantity > self.quantity:
            raise ValueError("Remaining exceeds original quantity")
        return self