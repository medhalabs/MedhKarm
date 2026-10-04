"""Session tokens: signed JWTs (HS256) with the user and company. The API stays stateless:
any process with the same secret can check a token."""

from datetime import UTC, datetime, timedelta

import jwt

from app.features.auth.schemas import CurrentUser

ALGORITHM = "HS256"


class TokenIssuer:
    def __init__(self, secret: str, days: int = 30) -> None:
        self._secret = secret
        self._days = days

    def issue(self, user_id: str, company_id: str, now: datetime | None = None) -> str:
        issued = now or datetime.now(UTC)
        claims = {
            "sub": user_id,
            "company": company_id,
            "iat": issued,
            "exp": issued + timedelta(days=self._days),
        }
        return jwt.encode(claims, self._secret, algorithm=ALGORITHM)

    def read(self, token: str) -> CurrentUser | None:
        """Who the token is for; None when it's forged, damaged or expired."""
        try:
            claims = jwt.decode(token, self._secret, algorithms=[ALGORITHM])
        except jwt.PyJWTError:
            return None
        if not claims.get("sub") or not claims.get("company"):
            return None
        return CurrentUser(user_id=str(claims["sub"]), company_id=str(claims["company"]))
