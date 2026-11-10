"""Small SQLite-backed account service for the local ShopFloor application."""

import base64
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import settings

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_TOKEN_LIFETIME_SECONDS = 12 * 60 * 60
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _connect():
    settings.auth_database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.auth_database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


@contextmanager
def _database():
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with _database() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_salt BLOB NOT NULL,
                password_hash BLOB NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if len(normalized) > 254 or not _EMAIL_RE.fullmatch(normalized):
        raise ValueError("Enter a valid email address.")
    return normalized


def _password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=64,
    )


def _public_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }


def find_user_by_id(user_id: str) -> dict | None:
    initialize_database()
    with _database() as connection:
        row = connection.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return _public_user(row) if row else None


def register_user(name: str, email: str, password: str) -> dict:
    initialize_database()
    normalized_email = normalize_email(email)
    clean_name = " ".join(name.split())
    if not 2 <= len(clean_name) <= 80:
        raise ValueError("Name must be between 2 and 80 characters.")
    if not 10 <= len(password) <= 128:
        raise ValueError("Password must be between 10 and 128 characters.")
    user_id = secrets.token_urlsafe(18)
    now = datetime.now(timezone.utc).isoformat()
    salt = secrets.token_bytes(16)
    hashed = _password_hash(password, salt)
    try:
        with _database() as connection:
            connection.execute(
                "INSERT INTO users (id, name, email, password_salt, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, clean_name, normalized_email, salt, hashed, now, now),
            )
            row = connection.execute(
                "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "An account with this email already exists. Log in instead."
        ) from exc
    return _public_user(row)


def authenticate_user(email: str, password: str) -> dict | None:
    initialize_database()
    try:
        normalized_email = normalize_email(email)
    except ValueError:
        normalized_email = email.strip().lower()
    with _database() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?", (normalized_email,)
        ).fetchone()
    if not row:
        return None
    candidate = _password_hash(password, row["password_salt"])
    if not hmac.compare_digest(candidate, row["password_hash"]):
        return None
    return _public_user(row)


def update_profile(user_id: str, name: str, email: str) -> dict:
    initialize_database()
    clean_name = " ".join(name.split())
    normalized_email = normalize_email(email)
    if not 2 <= len(clean_name) <= 80:
        raise ValueError("Name must be between 2 and 80 characters.")
    now = datetime.now(timezone.utc).isoformat()
    try:
        with _database() as connection:
            cursor = connection.execute(
                "UPDATE users SET name = ?, email = ?, updated_at = ? WHERE id = ?",
                (clean_name, normalized_email, now, user_id),
            )
            if cursor.rowcount != 1:
                return None
            row = connection.execute(
                "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise ValueError("That email is already used by another account.") from exc
    return _public_user(row) if row else None


def change_password(user_id: str, current_password: str, new_password: str):
    initialize_database()
    if not 10 <= len(new_password) <= 128:
        raise ValueError("New password must be between 10 and 128 characters.")
    with _database() as connection:
        row = connection.execute(
            "SELECT password_salt, password_hash FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row or not hmac.compare_digest(
            _password_hash(current_password, row["password_salt"]), row["password_hash"]
        ):
            raise ValueError("Current password is incorrect.")
        salt = secrets.token_bytes(16)
        hashed = _password_hash(new_password, salt)
        connection.execute(
            "UPDATE users SET password_salt = ?, password_hash = ?, updated_at = ? WHERE id = ?",
            (salt, hashed, datetime.now(timezone.utc).isoformat(), user_id),
        )


def _encode_segment(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def issue_access_token(user: dict) -> str:
    secret = settings.auth_secret_key.encode("utf-8")
    if len(secret) < 32:
        raise RuntimeError(
            "AUTH_SECRET_KEY must contain at least 32 characters. Set it in backend/.env and restart the backend."
        )
    header = _encode_segment({"alg": "HS256", "typ": "JWT"})
    payload = _encode_segment(
        {
            "sub": user["id"],
            "iat": int(time.time()),
            "exp": int(time.time()) + _TOKEN_LIFETIME_SECONDS,
        }
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{header}.{payload}.{encoded_signature}"


def verify_access_token(token: str) -> dict | None:
    secret = settings.auth_secret_key.encode("utf-8")
    if len(secret) < 32:
        return None
    try:
        header, payload, signature = token.split(".")
        expected = hmac.new(
            secret, f"{header}.{payload}".encode("ascii"), hashlib.sha256
        ).digest()
        supplied = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        if not hmac.compare_digest(expected, supplied):
            return None
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        claims = json.loads(decoded)
        if claims.get("exp", 0) <= int(time.time()) or not claims.get("sub"):
            return None
        return find_user_by_id(claims["sub"])
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return None
