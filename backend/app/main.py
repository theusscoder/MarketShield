from fastapi import FastAPI
from app.contracts.order import OrderRequest

app = FastAPI(
    title="MarketShield API",
    version="0.1.0"
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "marketshield"
    }


@app.post("/orders/validate")
def validate_order(order: OrderRequest):
    return {
        "valid": True,
        "order": order.model_dump()
    }