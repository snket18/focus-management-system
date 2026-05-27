import hashlib
import os
from database import db

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2 with SHA-256 and a random salt."""
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return f"{salt.hex()}:{hash_bytes.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a password against the stored salt and hash."""
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return computed_hash == expected_hash
    except Exception:
        return False

async def username_exists(username: str) -> bool:
    """Checks if a username is already taken."""
    user = await db.user.find_unique(where={"username": username})
    return user is not None

async def authenticate_user(username: str, password: str):
    """Authenticates a user. Returns the User record or None."""
    user = await db.user.find_unique(where={"username": username})
    if not user:
        return None
    if verify_password(password, user.password):
        return user
    return None

async def create_user(username: str, password: str):
    """Creates a new user and registers a default Setting configuration."""
    hashed = hash_password(password)
    user = await db.user.create(
        data={
            "username": username,
            "password": hashed,
            "setting": {
                "create": {
                    "focus_preset": 25,
                    "short_break": 5,
                    "long_break": 15,
                    "daily_goal_hours": 2.0,
                    "dark_mode": False,
                    "sound_enabled": True
                }
            }
        }
    )
    return user
