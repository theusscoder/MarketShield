import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

from app.auth.router import router as auth_router
from app.auth.router import init_auth_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_auth_database()
    yield


app = FastAPI(
    title="MarketShield API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "MarketShield API is running."}


@app.get("/health")
def health():
    return {"status": "ok"}