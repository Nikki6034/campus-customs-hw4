"""One-time: re-hash the seeded test user into the current secure format.

The seeded test user's hash does not record its PBKDF2 iteration count, so it
cannot be verified by the login code. This re-hashes the known test password
under security.hash_password so the test account works under the new,
self-describing scheme. Idempotent: safe to run more than once.

    python -m scripts.reseed_test_user
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import connect_rw, ensure_phone_column  # noqa: E402
from security import hash_password, verify_password  # noqa: E402

TEST_EMAIL = "test@campuscustoms.yale.edu"
TEST_PASSWORD = "password"


def main() -> None:
    ensure_phone_column()
    new_hash = hash_password(TEST_PASSWORD)
    with connect_rw() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE LOWER(email) = ?", (TEST_EMAIL,)
        ).fetchone()
        if row is None:
            print(f"Test user {TEST_EMAIL} not found; nothing to do.")
            return
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, row["id"]),
        )
        conn.commit()
        check = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (row["id"],)
        ).fetchone()["password_hash"]

    ok = verify_password(TEST_PASSWORD, check)
    print(f"Re-hashed {TEST_EMAIL}: verify={'OK' if ok else 'FAILED'}")


if __name__ == "__main__":
    main()
