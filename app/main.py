from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.v1.auth import router as auth_router
from app.api.v1.goods import router as goods_router
from app.api.v1.markets import router as markets_router
from app.api.v1.prices import router as prices_router
from app.api.v1.vendors import router as vendors_router

from .core.cache.redis import close_redis_connection, verify_redis_connection
from .core.db.database import dispose_engine, verify_database_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler for startup and shutdown tasks.
    """
    logger.info("Starting Viro application...")

    # 1. Verify Connectivity
    logger.info("Verifying database connectivity...")
    await verify_database_connection()

    logger.info("Verifying Redis connectivity...")
    await verify_redis_connection()

    logger.info("Viro application started successfully")

    yield

    # --- SHUTDOWN PHASE ---
    logger.info("Shutting down Viro application...")

    # 4. Close Infrastructure Connections
    await dispose_engine()
    await close_redis_connection()

    logger.info("All connections closed successfully")
    logger.info("Shutdown complete")


app = FastAPI(
    title="PriceGrid",
    description="Market price intelligence API",
    version="0.1.0",
    lifespan=lifespan,
)

_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=_PREFIX)
app.include_router(goods_router, prefix=_PREFIX)
app.include_router(vendors_router, prefix=_PREFIX)
app.include_router(markets_router, prefix=_PREFIX)
app.include_router(prices_router, prefix=_PREFIX)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Welcome to the PriceGrid API",
        "version": "0.1.0",
        "endpoints": [
            "/api/v1/auth",
            "/api/v1/goods",
            "/api/v1/vendors",
            "/api/v1/markets",
            "/api/v1/prices",
            "/health",
            "/docs",
        ],
    }
