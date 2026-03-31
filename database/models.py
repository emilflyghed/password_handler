import sqlite3
from datetime import datetime, timezone

from crypto.encryption import generate_salt, derive_key, encrypt, decrypt
from config import VERIFICATION_TOKEN, RATE_LIMIT_MAX_ATTEMPTS, RATE_LIMIT_BASE_SECONDS


class RateLimitError(Exception):
    """Raised when PIN verification is blocked by rate limiting."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after}s")


def setup_pin(conn: sqlite3.Connection, pin: str) -> bytearray:
    salt = generate_salt()
    key = derive_key(pin, salt)
    verifier = encrypt(VERIFICATION_TOKEN, key)
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('salt', ?)",
        (salt.hex(),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('pin_verifier', ?)",
        (verifier,),
    )
    conn.commit()
    return key


def check_rate_limit(conn: sqlite3.Connection) -> tuple[bool, int]:
    """Check if rate limiting is active. Returns (is_locked, seconds_remaining)."""
    row = conn.execute(
        "SELECT failed_attempts, lockout_until FROM rate_limit WHERE id = 1"
    ).fetchone()
    if row is None or row["lockout_until"] is None:
        return False, 0
    lockout_until = datetime.fromisoformat(row["lockout_until"])
    now = datetime.now(timezone.utc)
    if now < lockout_until:
        remaining = int((lockout_until - now).total_seconds()) + 1
        return True, remaining
    return False, 0


def _record_failed_attempt(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE rate_limit SET failed_attempts = failed_attempts + 1 WHERE id = 1"
    )
    row = conn.execute(
        "SELECT failed_attempts FROM rate_limit WHERE id = 1"
    ).fetchone()
    attempts = row["failed_attempts"]
    if attempts >= RATE_LIMIT_MAX_ATTEMPTS:
        lockout_secs = RATE_LIMIT_BASE_SECONDS * (attempts - RATE_LIMIT_MAX_ATTEMPTS + 1)
        lockout_until = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE rate_limit SET lockout_until = datetime(?, '+' || ? || ' seconds') WHERE id = 1",
            (lockout_until, lockout_secs),
        )
    conn.commit()


def _reset_rate_limit(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE rate_limit SET failed_attempts = 0, lockout_until = NULL WHERE id = 1"
    )
    conn.commit()


def verify_pin(conn: sqlite3.Connection, pin: str):
    is_locked, remaining = check_rate_limit(conn)
    if is_locked:
        raise RateLimitError(remaining)

    row = conn.execute(
        "SELECT value FROM config WHERE key = 'salt'"
    ).fetchone()
    if row is None:
        return None
    salt = bytes.fromhex(row["value"])

    row = conn.execute(
        "SELECT value FROM config WHERE key = 'pin_verifier'"
    ).fetchone()
    if row is None:
        return None

    key = derive_key(pin, salt)
    try:
        result = decrypt(row["value"], key)
        if result == VERIFICATION_TOKEN:
            _reset_rate_limit(conn)
            return key
    except Exception:
        pass
    _record_failed_attempt(conn)
    return None


def add_entry(
    conn: sqlite3.Connection, key: bytes,
    service: str, username: str, password: str,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO entries (service, username, password, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (encrypt(service, key), encrypt(username, key), encrypt(password, key), now, now),
    )
    conn.commit()
    return cursor.lastrowid


def get_all_entries(conn: sqlite3.Connection, key: bytes) -> list[dict]:
    rows = conn.execute(
        "SELECT id, service, username, password, created_at, updated_at "
        "FROM entries ORDER BY updated_at DESC"
    ).fetchall()
    return [_decrypt_row(row, key) for row in rows]


def get_entry(conn: sqlite3.Connection, key: bytes, entry_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id, service, username, password, created_at, updated_at "
        "FROM entries WHERE id = ?",
        (entry_id,),
    ).fetchone()
    if row is None:
        return None
    return _decrypt_row(row, key)


def update_entry(
    conn: sqlite3.Connection, key: bytes, entry_id: int,
    service: str, username: str, password: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE entries SET service=?, username=?, password=?, updated_at=? WHERE id=?",
        (encrypt(service, key), encrypt(username, key), encrypt(password, key), now, entry_id),
    )
    conn.commit()


def delete_entry(conn: sqlite3.Connection, entry_id: int) -> None:
    conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()


def search_entries(
    conn: sqlite3.Connection, key: bytes, query: str,
) -> list[dict]:
    all_entries = get_all_entries(conn, key)
    q = query.lower()
    return [
        e for e in all_entries
        if q in e["service"].lower() or q in e["username"].lower()
    ]


def set_config(conn: sqlite3.Connection, key_name: str, value: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        (key_name, value),
    )
    conn.commit()


def get_config(conn: sqlite3.Connection, key_name: str) -> str | None:
    row = conn.execute(
        "SELECT value FROM config WHERE key = ?", (key_name,)
    ).fetchone()
    return row["value"] if row else None


def _decrypt_row(row: sqlite3.Row, key: bytes) -> dict:
    return {
        "id": row["id"],
        "service": decrypt(row["service"], key),
        "username": decrypt(row["username"], key),
        "password": decrypt(row["password"], key),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
