import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from loguru import logger

from ..settings import settings
from ..types.token import TokenCodecConfig, TokenPair, TokenType
from .exceptions import TokenExpiredError, TokenInvalidError

_JWT_RESERVED = frozenset({"jti", "type", "iat", "exp", "iss", "aud"})


class TokenCodec:
    def __init__(self, config: TokenCodecConfig) -> None:
        self.config = config

    def generate_pair(self, claims: dict[str, Any]) -> TokenPair:
        """
        Generate access and refresh tokens in one call.

        Raises:
            KeyError: if a reserved JWT key (jti, type, iat, exp, iss, aud) is
                present in claims and conflicts with payload construction.
        """
        access_token, access_expires_at = self.generate(
            claims=claims,
            token_type=TokenType.ACCESS,
        )
        refresh_token, refresh_expires_at = self.generate(
            claims=claims,
            token_type=TokenType.REFRESH,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )

    def generate(
        self,
        claims: dict[str, Any],
        token_type: TokenType,
    ) -> tuple[str, datetime]:
        """
        Generate a single token. Returns (token, expires_at).

        Does not raise application exceptions — encoding failures surface as
        raw jwt.PyJWTError and indicate a misconfigured secret or algorithm.
        """
        now = datetime.now(UTC)
        ttl = (
            self.config.access_token_ttl
            if token_type == TokenType.ACCESS
            else self.config.refresh_token_ttl
        )
        expires_at = now + ttl

        payload = {
            **claims,
            "jti": str(uuid.uuid4()),
            "type": token_type,
            "iat": now,
            "exp": expires_at,
            "iss": self.config.issuer,
            "aud": self.config.audience,
        }

        token = jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.algorithm
        )
        return token, expires_at

    def refresh_access_token(self, refresh_token: str) -> tuple[str, datetime]:
        """
        Validate a refresh token and issue a new access token.
        Claims are forwarded from the refresh token — JWT reserved keys are stripped.

        Raises:
            TokenExpiredError: if the refresh token has expired.
            TokenInvalidError: if the token fails signature/structure validation,
                or if the token type is not refresh.
        """
        payload = self.decode(refresh_token)

        if payload.get("type") != TokenType.REFRESH:
            raise TokenInvalidError("Expected a refresh token")

        claims = {k: v for k, v in payload.items() if k not in _JWT_RESERVED}
        return self.generate(claims=claims, token_type=TokenType.ACCESS)

    def decode(self, token: str) -> dict[str, Any]:
        """
        Fully validate token (signature, expiry, issuer, audience) and return claims.

        Raises:
            TokenExpiredError: if the token's exp claim is in the past.
            TokenInvalidError: if signature verification fails, the issuer/audience
                doesn't match, or the token is malformed.
        """
        try:
            return jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer,
            )
        except jwt.ExpiredSignatureError:
            logger.warning("JWT expired")
            raise TokenExpiredError from None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT invalid: {e}")
            raise TokenInvalidError from None

    def extract_jti(self, token: str) -> str:
        """
        Extract JTI without signature verification.
        Used in step 1 of the auth flow — fast path before any crypto.

        Raises:
            KeyError: if the token has no jti claim (should never happen for
                tokens issued by this codec).
            jwt.PyJWTError: if the token is not valid JWT structure (not a
                base64-encoded header.payload.signature string).
        """
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=[self.config.algorithm],
        )
        return payload["jti"]

    def extract_expiry(self, token: str) -> datetime:
        """
        Extract expiry without signature verification.
        Used in logout flow to record BlacklistedToken.expires_at.

        Raises:
            KeyError: if the token has no exp claim.
            JWTError: if the token is not valid JWT structure.
        """
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=[self.config.algorithm],
        )
        return datetime.fromtimestamp(payload["exp"], tz=UTC)


# Global instance to be called app wide
token_codec = TokenCodec(
    TokenCodecConfig(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE,
        access_token_ttl=timedelta(days=1),
        refresh_token_ttl=timedelta(days=24),
    )
)
