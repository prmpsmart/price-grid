from pydantic_settings import BaseSettings, SettingsConfigDict

from .types.base import Environment


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    SERVICE_NAME: str = "PriceGrid"

    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    SPIKE_THRESHOLD_PCT: float = 20.0
    CACHE_TTL_SECONDS: int = 300

    # Redis Configuration
    REDIS_DECODE_RESPONSES: bool = True
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_MAX_CONNECTIONS: int = 20
    # SQLAlchemy Configuration
    SQL_ALCHEMY_ENGINE_POOL_SIZE: int = 15
    SQL_ALCHEMY_ENGINE_MAX_OVERFLOW: int = 5
    SQL_ALCHEMY_ENGINE_POOL_PRE_PING: bool = True
    SQL_ALCHEMY_ENGINE_POOL_RECYCLE: int = 1200


settings = Settings()  # type: ignore[call-arg]
