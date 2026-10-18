"""Seed dummy data so the frontend has something to show.

Run inside the API container (needs the DB migrated and Redis up):

    make seed

Safe to re-run: users, goods, markets and vendors are looked up before being
created, and price history is only generated while `pricerecord` is empty.
"""

import asyncio
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import bcrypt
from loguru import logger

from app.core.cache.redis import create_redis_client
from app.core.db.database import db_session, dispose_engine
from app.models.user import UserRole
from app.repositories.alert_repo import AlertRepository
from app.repositories.good_repo import GoodRepository
from app.repositories.market_repo import MarketRepository
from app.repositories.price_repo import PriceRepository
from app.repositories.user_repo import UserRepository
from app.repositories.vendor_repo import VendorRepository

PASSWORD = "password123"
CURRENCY = "NGN"
HISTORY_DAYS = 30
SPIKE_THRESHOLD_PCT = Decimal("20")

USERS = [
    ("admin@pricegrid.dev", UserRole.admin, None),
    ("vendor1@pricegrid.dev", UserRole.vendor, ("Mama Ngozi Provisions", "Mile 12")),
    ("vendor2@pricegrid.dev", UserRole.vendor, ("Alhaji Bello Foods", "Kano Central")),
    ("viewer@pricegrid.dev", UserRole.viewer, None),
]

# name, category, unit, base price in NGN
GOODS = [
    ("Rice (local, 50kg bag)", "Grains", "bag", 78000),
    ("Beans (brown, 1 derica)", "Grains", "derica", 2200),
    ("Garri (white, 1 derica)", "Grains", "derica", 900),
    ("Tomatoes (basket)", "Vegetables", "basket", 32000),
    ("Palm oil (25L)", "Oils", "jerrycan", 48000),
    ("Yam (medium tuber)", "Tubers", "tuber", 3500),
    ("Eggs (crate of 30)", "Poultry", "crate", 5200),
]

# name, city, region, price multiplier relative to the base
MARKETS = [
    ("Mile 12 Market", "Lagos", "South West", 1.00),
    ("Bodija Market", "Ibadan", "South West", 0.94),
    ("Kano Central Market", "Kano", "North West", 0.88),
    ("Ariaria Market", "Aba", "South East", 1.06),
    ("Wuse Market", "Abuja", "FCT", 1.12),
]


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def seed() -> None:
    rng = random.Random(42)
    users, goods, markets = UserRepository(), GoodRepository(), MarketRepository()
    vendors, prices, alerts = VendorRepository(), PriceRepository(), AlertRepository()

    async with db_session() as session:
        vendor_ids = []
        for email, role, profile in USERS:
            user = await users.get_by_email(session, email) or await users.create(
                session, email=email, hashed_password=_hash(PASSWORD), role=role
            )
            if profile:
                name, location = profile
                vendor = await vendors.get_by_user_id(
                    session, str(user.id)
                ) or await vendors.create(
                    session, name=name, location=location, user_id=user.id
                )
                vendor_ids.append(vendor.id)

        good_rows = []
        for name, category, unit, base in GOODS:
            good = await goods.get_by(session, name=name) or await goods.create(
                session, name=name, category=category, unit=unit
            )
            good_rows.append((good, base))

        market_rows = []
        for name, city, region, factor in MARKETS:
            market = await markets.get_by(session, name=name) or await markets.create(
                session, name=name, city=city, region=region
            )
            market_rows.append((market, factor))

        _, existing = await prices.list_filtered(session, page=1, limit=1)
        if existing:
            logger.info("Price records already present; skipping price history")
        else:
            now = datetime.now(UTC)
            spikes = 0
            for g_idx, (good, base) in enumerate(good_rows):
                for m_idx, (market, factor) in enumerate(market_rows):
                    # Two vendors per market, alternating by index.
                    vendor_id = vendor_ids[(g_idx + m_idx) % len(vendor_ids)]
                    price = Decimal(base * factor)
                    series: list[Decimal] = []
                    for day in range(HISTORY_DAYS, 0, -1):
                        # Small daily drift, +/-4%.
                        price *= Decimal(1 + rng.uniform(-0.04, 0.04))
                        series.append(price.quantize(Decimal("0.01")))
                        await prices.create(
                            session,
                            good_id=good.id,
                            vendor_id=vendor_id,
                            market_id=market.id,
                            price=series[-1],
                            currency=CURRENCY,
                            submitted_at=now
                            - timedelta(days=day, hours=rng.randint(0, 8)),
                        )

                    # A few pairs end with a spike that also gets an alert row.
                    if (g_idx + m_idx) % 7 == 0:
                        avg = sum(series, Decimal(0)) / len(series)
                        spike = (avg * Decimal("1.35")).quantize(Decimal("0.01"))
                        delta = ((spike - avg) / avg * 100).quantize(Decimal("0.0001"))
                        triggered = now - timedelta(hours=rng.randint(1, 6))
                        await prices.create(
                            session,
                            good_id=good.id,
                            vendor_id=vendor_id,
                            market_id=market.id,
                            price=spike,
                            currency=CURRENCY,
                            submitted_at=triggered,
                        )
                        await alerts.create(
                            session,
                            good_id=good.id,
                            market_id=market.id,
                            price=spike,
                            previous_avg=avg.quantize(Decimal("0.01")),
                            delta_pct=delta,
                            threshold_pct=SPIKE_THRESHOLD_PCT,
                            currency=CURRENCY,
                            triggered_at=triggered,
                        )
                        spikes += 1
            logger.info(
                "Seeded {} goods x {} markets x {} days, {} spikes",
                len(good_rows),
                len(market_rows),
                HISTORY_DAYS,
                spikes,
            )

    # Rows were written behind the services' backs, so drop their caches.
    redis = create_redis_client()
    keys = [k async for k in redis.scan_iter("price:current:*")] + ["goods:list"]
    await redis.delete(*keys)
    await redis.aclose()
    await dispose_engine()

    logger.info("Done. Sign in with any seeded account, password: {}", PASSWORD)
    for email, role, _ in USERS:
        logger.info("  {:<24} {}", email, role.value)


if __name__ == "__main__":
    asyncio.run(seed())
