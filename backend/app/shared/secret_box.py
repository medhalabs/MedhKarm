"""Encrypts secrets we store for founders (their API keys). Fernet: AES with an integrity check,
so a changed or foreign value is refused rather than read wrongly."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


class SecretBox:
    def __init__(self, secret: str) -> None:
        # Any long string works: it's hashed into Fernet's 32-byte key.
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
        self._fernet = Fernet(key)

    def seal(self, plain: str) -> str:
        return self._fernet.encrypt(plain.encode()).decode()

    def open(self, sealed: str) -> str | None:
        """The secret, or None when it was sealed with another key (the server's key changed)."""
        try:
            return self._fernet.decrypt(sealed.encode()).decode()
        except InvalidToken:
            return None
