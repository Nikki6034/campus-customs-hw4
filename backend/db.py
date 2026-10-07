"""Read-only access to campus_customs.db.

Problem 3 only serves data, so every connection is opened read-only. That is
enforced by the sqlite URI rather than by convention, so a stray INSERT fails
loudly instead of quietly mutating the dataset.
"""

import sqlite3
from pathlib import Path

from config import DB_PATH


def connect() -> sqlite3.Connection:
    """Open a read-only connection with dict-like rows."""
    path = Path(DB_PATH).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Database not found at {path}")

    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    # Declared foreign keys are not enforced by default; turn them on.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def connect_rw() -> sqlite3.Connection:
    """Open a read-write connection, used only by the auth flow.

    Product serving stays read-only via connect(); writes are confined to the
    users table so the catalogue and inventory data cannot be mutated here.
    """
    path = Path(DB_PATH).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Database not found at {path}")

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_phone_column() -> None:
    """Add the optional users.phone column if it is not already present.

    Shoppers may provide a phone number for shipping; the seeded schema has no
    such column, so add it once, idempotently.
    """
    with connect_rw() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
        if "phone" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            conn.commit()
