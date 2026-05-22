import json

import redis.asyncio as aioredis

from ..core.settings import settings

SPIKE_CHANNEL = "price:spikes"
_THRESHOLD_KEY = "spike:threshold:{good_id}:{market_id}"


async def get_spike_threshold(
    redis: aioredis.Redis, good_id: str, market_id: str
) -> float:
    raw = await redis.get(_THRESHOLD_KEY.format(good_id=good_id, market_id=market_id))
    return float(raw) if raw else settings.SPIKE_THRESHOLD_PCT


async def publish_spike_event(redis: aioredis.Redis, event_data: dict) -> None:
    await redis.publish(SPIKE_CHANNEL, json.dumps(event_data))
