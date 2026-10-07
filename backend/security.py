"""Password hashing for Campus Customs accounts.

Design goals (the assignment asks for passwords no attacker, human or AI, can
recover):

- Passwords are never stored or logged in plaintext. Only a one-way hash is
  kept, so even a full dump of the database does not reveal any password.
- PBKDF2-HMAC-SHA256 with a high iteration count makes each guess expensive,
  so an offline brute-force against a stolen hash is impractical.
- Every account gets its own random salt, so identical passwords produce
  different hashes and precomputed ("rainbow table") attacks do not work.
- Verification uses a constant-time comparison, so timing does not leak how
  much of a hash matched.
- The stored string is self-describing: it embeds the algorithm, iteration
  count and salt. Verification reads the cost from the hash itself, so the
  parameters can be raised later without breaking existing accounts.

Stored format:  pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
"""

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
# OWASP's 2023 floor for PBKDF2-HMAC-SHA256. Raising this only affects new or
# re-saved hashes, because each hash records the count it was made with.
ITERATIONS = 600_000
SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    """Return a self-describing hash of ``password``. Never stores plaintext."""
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERATIONS
    )
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Check ``password`` against a stored hash in constant time.

    Returns False for any malformed or unrecognised hash rather than raising,
    so a bad row can never crash the login path.
    """
    try:
        algorithm, iterations_s, salt_hex, digest_hex = stored.split("$")
        if algorithm != ALGORITHM:
            return False
        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, AttributeError):
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(candidate, expected)
