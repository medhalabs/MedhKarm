"""Password hashes with scrypt (Python's standard library): a random salt per password."""

import hashlib
import hmac
import secrets

N, R, P = 2**14, 8, 1  # scrypt's cost settings: about 16 MB and a few tens of ms per check


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=N, r=R, p=P)
    return f"scrypt${salt.hex()}${digest.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, digest = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=N, r=R, p=P)
    return hmac.compare_digest(actual.hex(), digest)
