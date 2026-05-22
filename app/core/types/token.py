from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import TypedDict


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"


@dataclass
class TokenCodecConfig:
    secret_key: str
    algorithm: str
    issuer: str
    audience: str
    access_token_ttl: timedelta
    refresh_token_ttl: timedelta


class TokenPair(TypedDict):
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
