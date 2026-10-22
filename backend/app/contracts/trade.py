
from datetime import datetime

from pydantic import BaseModel, Field


class Trade(BaseModel):
    trade_id: str
    symbol: str
    buy_order_id: str
    sell_order_id: str
    buyer_account_id: str
    seller_account_id: str
    price_paise: int = Field(gt=0)
    quantity: int = Field(gt=0)
    sequence: int = Field(ge=0)
    timestamp: datetime
