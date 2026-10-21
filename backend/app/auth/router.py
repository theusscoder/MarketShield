
import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation
from fastapi import APIRouter, HTTPException, Request, Response, status

from .schemas import (
    AuthResponse,
    LoginRequest,
    SignupRequest,
    UserResponse,
)
from .security import (
    create_session_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

APP_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = APP_DIR / "database" / "schema.sql"

COOKIE_NAME = "marketshield_session"
SESSION_DAYS = 7


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Check backend/.env."
        )

    return psycopg.connect(
        database_url,
        row_factory=dict_row,
        connect_timeout=10,
    )


def init_auth_database():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with get_connection() as connection:
        connection.execute(schema)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user_response(row) -> UserResponse:
    return UserResponse(
        id=row["id"],
        name=row["name"],
        email=row["email"],
    )


def issue_session(user_id: int, response: Response):
    token = create_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=SESSION_DAYS
    )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO sessions (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, token_digest(token), expires_at),
        )

    is_production = os.getenv("MARKETSHIELD_ENV") == "production"

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 60 * 60,
        path="/",
    )


def get_current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in.",
        )

    now = datetime.now(timezone.utc)

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT users.id, users.name, users.email
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = %s
              AND sessions.expires_at > %s
            """,
            (token_digest(token), now),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please sign in again.",
        )

    return row


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(data: SignupRequest, response: Response):
    name = data.name.strip()
    email = str(data.email).strip().lower()

    if len(name) < 2:
        raise HTTPException(
            status_code=422,
            detail="Please enter a valid name.",
        )

    password_hash = hash_password(data.password)

    try:
        with get_connection() as connection:
            user = connection.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, name, email
                """,
                (name, email, password_hash),
            ).fetchone()

    except UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    issue_session(user["id"], response)

    return AuthResponse(
        message="Account created successfully.",
        user=create_user_response(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, response: Response):
    email = str(data.email).strip().lower()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, email, password_hash
            FROM users
            WHERE email = %s
            """,
            (email,),
        ).fetchone()

    if row is None or not verify_password(
        data.password, row["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    issue_session(row["id"], response)

    return AuthResponse(
        message="Signed in successfully.",
        user=create_user_response(row),
    )


@router.get("/me", response_model=UserResponse)
def me(request: Request):
    return create_user_response(get_current_user(request))


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE_NAME)

    if token:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE token_hash = %s",
                (token_digest(token),),
            )

    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=os.getenv("MARKETSHIELD_ENV") == "production",
        samesite="lax",
        path="/",
    )

    return {"message": "Signed out successfully."}
