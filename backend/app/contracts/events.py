from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class EventType(str, Enum):
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_PARTIALLY_FILLED = "ORDER_PARTIALLY_FILLED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    TRADE_EXECUTED = "TRADE_EXECUTED"


class OrderEvent(BaseModel):
    event_id: str
    event_type: EventType
    order_id: str | None = None
    trade_id: str | None = None
    account_id: str | None = None
    sequence: int = Field(ge=0)
    timestamp: datetime
    reason: str | None = None
