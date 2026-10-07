"""Account creation and login.

Security posture:
- Passwords are hashed with PBKDF2-HMAC-SHA256 (see security.py) before they
  ever touch the database; plaintext is never stored or logged.
- The password hash is never returned by any endpoint. Responses use the
  PublicUser model, which has no hash field.
- Login returns the same generic error whether the email is unknown or the
  password is wrong, so the endpoint cannot be used to discover which emails
  have accounts (no user enumeration).
- A dummy verify runs even when the email is unknown, so a failed login takes
  about the same time either way and cannot be timed to reveal valid emails.
- Email uniqueness is enforced by the database's UNIQUE constraint, caught and
  reported as a clean 409 rather than a 500.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from db import connect_rw
from models import LoginRequest, PublicUser, SignupRequest
from security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

# A valid hash of a random value, used to spend verification time on logins for
# unknown emails so their response time matches real accounts.
_DUMMY_HASH = hash_password("dummy-password-for-timing-equalisation")


def _to_public(row: sqlite3.Row) -> PublicUser:
    keys = row.keys()
    return PublicUser(
        id=row["id"],
        first_name=row["first_name"] if "first_name" in keys else None,
        last_name=row["last_name"] if "last_name" in keys else None,
        email=row["email"],
        phone=row["phone"] if "phone" in keys else None,
    )


@router.post("/signup", response_model=PublicUser, status_code=201)
async def signup(request: SignupRequest) -> PublicUser:
    # Pydantic has already checked the fields and that the passwords match.
    password_hash = hash_password(request.password)
    full_name = f"{request.first_name} {request.last_name}".strip()
    email = request.email.lower()

    try:
        with connect_rw() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users
                    (name, email, password_hash, first_name, last_name, phone)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    full_name,
                    email,
                    password_hash,
                    request.first_name,
                    request.last_name,
                    request.phone,
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
    except sqlite3.IntegrityError:
        # UNIQUE(email) violation.
        raise HTTPException(
            status_code=409, detail="An account with that email already exists."
        )

    return _to_public(row)


@router.post("/login", response_model=PublicUser)
async def login(request: LoginRequest) -> PublicUser:
    email = request.email.lower()
    with connect_rw() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(email) = ?", (email,)
        ).fetchone()

    # Always run a verification so timing does not reveal whether the email
    # exists. The result for an unknown email is discarded.
    stored_hash = row["password_hash"] if row is not None else _DUMMY_HASH
    valid = verify_password(request.password, stored_hash)

    if row is None or not valid:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return _to_public(row)
