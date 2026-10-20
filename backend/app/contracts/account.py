from pydantic import BaseModel, Field


class CashBalance(BaseModel):
    account_id: str
    available_paise: int = Field(ge=0)
    reserved_paise: int = Field(ge=0)


class Position(BaseModel):
    account_id: str
    symbol: str
    available_quantity: int = Field(ge=0)
    reserved_quantity: int = Field(ge=0)