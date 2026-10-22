from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class Trade(BaseModel):
    trade_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)

    buy_order_id: str = Field(min_length=1)
    sell_order_id: str = Field(min_length=1)

    buyer_account_id: str = Field(min_length=1)
    seller_account_id: str = Field(min_length=1)

    price_paise: int = Field(gt=0)
    quantity: int = Field(gt=0)
    sequence: int = Field(ge=0)

    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Trade timestamp must be timezone-aware")
        return value