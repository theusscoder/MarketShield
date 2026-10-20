from pydantic import BaseModel, Field


class SurveillanceAlert(BaseModel):
    alert_id: str
    account_id: str
    rule: str
    related_event_ids: list[str]
    severity: str
    explanation: str = Field(min_length=1)