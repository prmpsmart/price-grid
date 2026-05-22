# CLAUDE.md — PriceGrid

This file tells Claude how to work in this codebase. Read it fully before making any changes.

---

## What This Project Is

PriceGrid is a market price intelligence REST API. It tracks prices of goods across vendors and markets, detects price spikes, and exposes comparison and trend data. It is a self-contained backend — no third-party APIs, no external services beyond PostgreSQL and Redis.

---

## Tech Stack

| Layer           | Tool                        |
| --------------- | --------------------------- |
| Language        | Python 3.13                 |
| Framework       | FastAPI                     |
| ORM             | SQLAlchemy 2.0 (async)      |
| Migrations      | Alembic                     |
| Database        | PostgreSQL 15               |
| Cache + Events  | Redis 7 (caching + pub/sub) |
| Package manager | uv                          |
| Testing         | pytest                      |
| Containers      | Docker + Docker Compose     |

---

## Project Structure

```
pricegrid/
├── app/
│   ├── api/v1/          # Routers only — no business logic here
│   │   ├── auth.py
│   │   ├── prices.py
│   │   ├── goods.py
│   │   ├── vendors.py
│   │   ├── markets.py
│   │   └── alerts.py
│   ├── services/        # All business logic lives here
│   │   ├── price_service.py
│   │   ├── alert_service.py
│   │   └── auth_service.py
│   ├── repositories/    # All database access lives here
│   │   ├── price_repo.py
│   │   ├── good_repo.py
│   │   └── vendor_repo.py
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── good.py
│   │   ├── vendor.py
│   │   ├── market.py
│   │   └── price.py
│   ├── schemas/         # Pydantic request/response schemas
│   ├── core/            # Config, DB session, Redis client
│   │   ├── config.py
│   │   ├── database.py
│   │   └── redis.py
│   ├── events/          # Pub/sub publisher and consumer
│   │   ├── publisher.py
│   │   └── consumer.py
│   └── main.py
├── alembic/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── uv.lock
├── .env.example
└── README.md
```

---

## Architecture Rules

These are non-negotiable. Follow them in every change.

### 1. Routes are thin

Routes in `app/api/v1/` do exactly three things: validate input, call a service, return a response. No business logic, no direct database calls, no Redis calls.

```python
# CORRECT
@router.post("/prices")
async def submit_price(payload: PriceCreate, service: PriceService = Depends(get_price_service)):
    return await service.submit(payload)

# WRONG — business logic in the route
@router.post("/prices")
async def submit_price(payload: PriceCreate, db: AsyncSession = Depends(get_db)):
    avg = await db.execute(select(...))  # NO
    if payload.price > avg * 1.2:        # NO
        ...
```

### 2. Services own business logic

All rules, calculations, and decisions live in `app/services/`. Services call repositories for data — they never import SQLAlchemy models directly or write raw queries.

### 3. Repositories own data access

All SQLAlchemy queries live in `app/repositories/`. Nothing else touches the database session directly. Repositories take a session as a parameter — they do not create their own.

```python
# CORRECT
class PriceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(self, good_id: int, market_id: int) -> PriceRecord | None:
        ...
```

### 4. Dependencies via FastAPI Depends()

DB sessions, Redis clients, current user, and service instances are all injected via `Depends()`. No global state, no module-level singletons accessed directly in routes or services.

### 5. All schema changes go through Alembic

Never modify the database directly. Never use `Base.metadata.create_all()` in production code. Every schema change is a migration.

```bash
# Create a new migration after changing a model
alembic revision --autogenerate -m "add price_alerts table"

# Apply migrations
alembic upgrade head
```

### 6. Redis cache keys follow a strict pattern

```
price:current:{good_id}:{market_id}     # Current price cache
goods:list                              # All goods list cache
```

Cache is invalidated on write, not relied on solely via TTL. TTL is a safety net only.

### 7. Pub/sub events go through the publisher module

Never publish to Redis directly from a service. Use `app/events/publisher.py`.

```python
# CORRECT
from app.events.publisher import publish_spike_event
await publish_spike_event(event_data)

# WRONG
await redis.publish("price:spikes", json.dumps(data))  # NO
```

---

## Running the Project

### Docker (all services)

```bash
docker-compose up --build
```

### Local dev with uv

```bash
uv sync
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload
```

### Adding a dependency

```bash
uv add <package>          # runtime dependency
uv add --dev <package>    # dev/test only
```

Never use `pip install` directly. Always use `uv`.

---

## Running Tests

```bash
# All tests
uv run pytest

# Unit only (no DB, no Redis)
uv run pytest tests/unit

# Integration only
uv run pytest tests/integration

# With coverage
uv run pytest --cov=app --cov-report=term-missing
```

### Test rules

- Unit tests must not touch the database or Redis. Use mocks or fakes.
- Integration tests use a separate test database spun up via `conftest.py`.
- Every new service method needs at least one unit test.
- Every new endpoint needs at least one integration test covering the happy path and one covering a failure case (wrong role, bad input, not found).

---

## Key Business Rules

These rules live in `app/services/price_service.py`. Do not move them.

**Spike detection**
A price submission is flagged as a spike if it deviates from the 30-day rolling average for that good in that market by more than `SPIKE_THRESHOLD_PCT` (default: 20%). When a spike is detected, a `price:spikes` event is published via Redis pub/sub.

**Price records are append-only**
`price_records` is never updated. The current price for a good/market pair is always the most recently inserted record. Do not add update or delete operations to `PriceRepository`.

**Role enforcement**

- `viewer` — read-only access to all price data
- `vendor` — can submit prices, read everything
- `admin` — full access including goods/market management and alert threshold configuration

Role checks are enforced in the service layer, not the route layer.

---

## Environment Variables

All config is in `app/core/config.py` via `pydantic-settings`. Never hardcode values. Never read `os.environ` directly outside of `config.py`.

Required variables (see `.env.example`):

```
DATABASE_URL
REDIS_URL
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
ENVIRONMENT
SPIKE_THRESHOLD_PCT
```

---

## What Not To Do

- Do not add third-party API integrations — the system is intentionally self-contained
- Do not write raw SQL — use SQLAlchemy ORM and repository methods
- Do not put logic in routes
- Do not access the database from tests without going through `conftest.py` fixtures
- Do not use `pip install` — use `uv add`
- Do not create new Alembic migrations without running `alembic upgrade head` locally first to verify they apply cleanly
- Do not hardcode currency — always store as a field on `price_records`

---

## Commit Convention

Follow conventional commits. Sprint branches are named `sprint/1`, `sprint/2`, etc.

```
feat: add spike detection to price service
fix: invalidate redis cache on price submission
test: add unit tests for price averaging logic
chore: add alembic migration for price_alerts table
refactor: extract alert threshold logic into alert service
docs: update README with uv local dev setup
```

Each commit should do one thing. If the commit message needs "and", split it.
