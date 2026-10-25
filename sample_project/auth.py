"""Authentication and Access Control Service."""

import hashlib
import os
import time
from typing import Dict, Any, Optional
from sample_project.config import load_settings, setup_logger
from sample_project.database import DatabaseClient

logger = setup_logger("auth")


def hash_password(password: str) -> str:
    """Hash password with a randomly generated cryptographic salt."""
    salt = os.urandom(16).hex()
    pwd_hash = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify raw password against salt and stored SHA-256 hash."""
    try:
        salt, expected_hash = stored_hash.split("$")
    except ValueError:
        return False
    candidate_hash = hashlib.sha256((plain_password + salt).encode("utf-8")).hexdigest()
    return candidate_hash == expected_hash


def generate_jwt_token(user_id: int, username: str, role: str) -> str:
    """Generate mock signed token containing user identity and expiry."""
    settings = load_settings()
    secret = settings["jwt_secret"]
    timestamp = int(time.time())
    payload = f"{user_id}:{username}:{role}:{timestamp + 3600}"
    signature = hashlib.sha256((payload + secret).encode("utf-8")).hexdigest()[:16]
    return f"{payload}:{signature}"


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate token signature and check expiration timestamp."""
    settings = load_settings()
    secret = settings["jwt_secret"]
    parts = token.split(":")
    if len(parts) != 5:
        return None
    user_id, username, role, expiry_str, signature = parts
    payload = f"{user_id}:{username}:{role}:{expiry_str}"
    expected_sig = hashlib.sha256((payload + secret).encode("utf-8")).hexdigest()[:16]

    if signature != expected_sig:
        logger.warning(f"Invalid token signature for user {username}")
        return None
    if int(expiry_str) < time.time():
        logger.warning(f"Expired token presented for user {username}")
        return None

    return {"user_id": int(user_id), "username": username, "role": role}


def authenticate_user(db: DatabaseClient, username: str, password: str) -> Optional[str]:
    """Authenticate user credentials and return signed session token."""
    user = db.get_user_by_username(username)
    if not user:
        logger.info(f"Failed authentication attempt: user {username} not found")
        return None

    if not verify_password(password, user["password_hash"]):
        logger.info(f"Failed authentication attempt: invalid password for {username}")
        return None

    token = generate_jwt_token(user["id"], user["username"], user["role"])
    logger.info(f"User {username} successfully logged in")
    return token
