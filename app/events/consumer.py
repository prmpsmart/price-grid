import asyncio
import json
from decimal import Decimal

from loguru import logger

from ..core.cache.redis import create_redis_client
from ..core.db.database import db_session
from ..events.publisher import SPIKE_CHANNEL
from ..repositories.alert_repo import AlertRepository


async def run_spike_consumer() -> None:
    redis = create_redis_client()
    repo = AlertRepository()
    pubsub = redis.pubsub()
    await pubsub.subscribe(SPIKE_CHANNEL)
    logger.info(f"Spike consumer subscribed to channel: {SPIKE_CHANNEL}")
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                async with db_session() as session:
                    await repo.create(
                        session,
                        good_id=data["good_id"],
                        market_id=data["market_id"],
                        price=Decimal(data["price"]),
                        previous_avg=Decimal(data["previous_avg"]),
                        delta_pct=Decimal(data["delta_pct"]),
                        threshold_pct=Decimal(data["threshold_pct"]),
                        currency=data["currency"],
                    )
                logger.info(
                    "Spike alert recorded: good={} delta={}%",
                    data["good_id"],
                    data["delta_pct"],
                )
            except Exception as exc:
                logger.error("Failed to process spike event: {}", exc)
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(SPIKE_CHANNEL)
        await redis.aclose()
