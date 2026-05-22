# PriceGrid

> A market price intelligence API that tracks good prices across vendors and markets, flags price spikes in real time, and caches high-traffic reads.

Built to address a real problem — price opacity in everyday markets. In many markets, buyers have no reliable way to know if the price they're being charged is fair relative to what others are paying, or what it was last week. PriceGrid is the backend layer that changes that.

---

## Architecture

```
                        ┌─────────────────┐
                        │   HTTP Client   │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │   FastAPI App   │
                        │  (pricegrid-api)│
                        └────┬───────┬────┘
                             │       │
              ┌──────────────▼──┐   ┌─▼───────────────┐
              │  PostgreSQL 15  │   │    Redis 7      │
              │ (pricegrid-db)  │   │(pricegrid-cache)│
              │                 │   │                 │
              │ • users         │   │ • price cache   │
              │ • goods         │   │ • pub/sub bus   │
              │ • vendors       │   │                 │
              │ • markets       │   └─────────────────┘
              │ • price_records │
              │ • price_alerts  │
              └─────────────────┘
```

---

## Tech Stack

| Tool              | Version | Why                                                                        |
| ----------------- | ------- | -------------------------------------------------------------------------- |
| FastAPI           | 0.111+  | High-performance async REST framework with automatic OpenAPI docs          |
| PostgreSQL        | 15      | Relational integrity for price history and user/vendor relationships       |
| SQLModel          | 0.0.38  | ORM + Pydantic schema in one — table models serve as both DB tables and API response schemas |
| Alembic           | 1.13+   | Schema versioning — no manual SQL, ever                                    |
| Redis             | 7       | Price caching on read-heavy endpoints + pub/sub for spike alerts           |
| uv                | Latest  | Fast Python package manager — replaces pip + venv. 10-100x faster installs |
| Docker + Compose  | Latest  | One-command setup that mirrors production environments                     |
| pytest            | 7+      | Unit and integration test coverage for business logic and API endpoints    |
| PyJWT             | 2.12+   | JWT encode/decode — used directly via `import jwt`                         |
| bcrypt            | 4.0+    | Password hashing — used directly without passlib wrapper                   |
| pydantic-settings | 2.0+    | Environment-based configuration                                            |

---

## Getting Started

### Option A — Docker (recommended)

**Prerequisites:** Docker and Docker Compose installed. That's it.

```bash
git clone https://github.com/yourusername/pricegrid.git
cd pricegrid

cp .env.example .env

docker-compose up --build
```

The API will be live at `http://localhost:8000`

Interactive docs at `http://localhost:8000/docs`

**Stop the project:**

```bash
docker-compose down

# Wipe database volume too
docker-compose down -v
```

---

### Option B — Local dev with uv

`uv` is a fast Python package and project manager (written in Rust). It replaces `pip`, `pip-tools`, and `venv` in one tool — installs are 10–100x faster.

**Prerequisites:** Python 3.13+, uv, a running PostgreSQL and Redis instance.

**Install uv** (if you don't have it):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Set up the project:**

```bash
git clone https://github.com/yourusername/pricegrid.git
cd pricegrid

# Create virtual environment and install all dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# Copy and fill in your environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload
```

**Managing dependencies:**

```bash
# Add a new package
uv add fastapi

# Add a dev-only package
uv add --dev pytest

# Remove a package
uv remove somepackage

# Sync after pulling changes (replaces pip install -r requirements.txt)
uv sync
```

> **Why uv?** Traditional `pip install -r requirements.txt` on a fresh clone can take 30–60 seconds. `uv sync` typically takes under 3 seconds for the same packages. In CI and Docker builds this adds up significantly.

---

## Environment Variables

Copy `.env.example` to `.env` before running.

```env
# Database
DATABASE_URL=postgresql://pricegrid:pricegrid@pricegrid-db:5432/pricegrid

# Redis
REDIS_URL=redis://pricegrid-cache:6379

# Auth
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# App
ENVIRONMENT=development
SPIKE_THRESHOLD_PCT=20
```

---

## API Reference

### Authentication

```
POST   /api/v1/auth/register     Register a new user
POST   /api/v1/auth/login        Login and receive JWT token
GET    /api/v1/auth/me           Get current user profile
```

### Goods, Vendors & Markets

```
GET    /api/v1/goods             List goods — paginated (Redis cached)
POST   /api/v1/goods             Create a good (admin only)
GET    /api/v1/vendors           List vendors — paginated
POST   /api/v1/vendors           Register as a vendor
GET    /api/v1/markets           List markets — paginated
POST   /api/v1/markets           Create a market (admin only)
```

### Prices

```
POST   /api/v1/prices                        Submit a price
GET    /api/v1/prices                        Query prices — paginated (filters: good, market, date range)
GET    /api/v1/prices/current                Latest price per good per market — paginated (cached)
GET    /api/v1/prices/history/{good_id}      Full price history for a good
GET    /api/v1/prices/compare?good_id={}     Compare prices across markets
GET    /api/v1/prices/trends?good_id={}&window=7d   Price trend over time window
```

### Alerts

```
GET    /api/v1/alerts                        All spike alerts (admin only)
GET    /api/v1/alerts/{good_id}              Alerts for a specific good
POST   /api/v1/alerts/thresholds             Set custom spike threshold (admin only)
```

### Pagination

All list endpoints accept `page` and `limit` query parameters and return a consistent envelope:

```
?page=1&limit=20    # default — page is 1-indexed, limit capped at 100
```

```json
{
  "items": [...],
  "total": 142,
  "page": 1,
  "limit": 20
}
```

`total` is the count of all matching records across all pages, not just the current page. Use it to calculate how many pages exist: `ceil(total / limit)`.

### Example: Submit a price

```bash
curl -X POST http://localhost:8000/api/v1/prices \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "good_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "vendor_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "market_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "price": 450.00,
    "currency": "NGN"
  }'
```

### Example: List goods (page 2)

```bash
curl "http://localhost:8000/api/v1/goods?page=2&limit=10"
```

```json
{
  "items": [
    { "id": "...", "name": "Tomato", "category": "Vegetable", "unit": "kg", ... }
  ],
  "total": 38,
  "page": 2,
  "limit": 10
}
```

### Example: Compare prices across markets

```bash
curl http://localhost:8000/api/v1/prices/compare?good_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

```json
{
  "good": "Rice (50kg bag)",
  "unit": "bag",
  "markets": [
    {
      "market": "Bodija Market",
      "city": "Ibadan",
      "current_price": 42000,
      "currency": "NGN",
      "submitted_at": "2026-05-21T10:30:00Z"
    },
    {
      "market": "Mile 12 Market",
      "city": "Lagos",
      "current_price": 44500,
      "currency": "NGN",
      "submitted_at": "2026-05-21T09:15:00Z"
    },
    {
      "market": "Wuse Market",
      "city": "Abuja",
      "current_price": 46000,
      "currency": "NGN",
      "submitted_at": "2026-05-21T11:00:00Z"
    }
  ]
}
```

---

## Roles & Permissions

| Role   | Can Do                                                               |
| ------ | -------------------------------------------------------------------- |
| viewer | Read all price data, history, comparisons, alerts                    |
| vendor | Everything a viewer can do + submit prices                           |
| admin  | Everything a vendor can do + manage goods, markets, alert thresholds |

---

## Design Decisions

### Why SQLModel instead of SQLAlchemy + Pydantic separately?

SQLModel unifies the ORM and schema layers. A `Good` model declared with `table=True` is simultaneously a SQLAlchemy table and a Pydantic model — it can be returned directly from routes as a response schema without a separate `GoodOut` class to keep in sync. Input-only schemas (payloads that don't map 1:1 to a table, like `GoodCreate` or `UserRegister`) still live in `app/schemas.py` as plain Pydantic models. Alembic reads `SQLModel.metadata` for migrations the same way it previously read `Base.metadata`.

### Why the Repository pattern?

All database access goes through repository classes (`price_repo.py`, `good_repo.py`, etc.) — never directly from routes. This keeps the service layer independent of the database session and makes the query layer easy to swap or extend without touching business logic.

### Why Redis cache on `/prices/current`?

This endpoint is the most read-heavy in the system — every comparison and dashboard view hits it. But it only changes when a new price is submitted. So rather than a short TTL, the cache is invalidated on write. The TTL (5 minutes) exists only as a safety net. This is intentional, not default behaviour.

### Why Redis pub/sub for spike alerts?

The price service does not know about alerts. It just publishes an event to the `price:spikes` channel when a spike is detected. A separate consumer picks it up and writes to `price_alerts`. This decoupling means new consumers (email, webhook, dashboard) can be added later without touching the publisher.

### Why offset-based pagination instead of cursor pagination?

All list endpoints use `{page, total, limit}` offset pagination. The `total` count lets clients build page controls and know how far through a result set they are — important for any UI or export workflow. The base repository implements this with a single `SELECT COUNT(*)` over the filtered subquery before applying `LIMIT`/`OFFSET`. Goods are an exception: because the full list fits in the Redis cache, pagination is done in memory from the cached slice rather than with a second DB round trip.

### Why append-only price records?

`price_records` is never updated — only inserted. Every price ever submitted is preserved. This gives a complete audit trail and makes trend/history queries straightforward. The "current price" is always the latest record, not a mutable field.

---

## Running Tests

### Via Docker

```bash
# Run all tests
docker-compose exec pricegrid-api pytest

# Unit tests only
docker-compose exec pricegrid-api pytest tests/unit

# Integration tests only
docker-compose exec pricegrid-api pytest tests/integration

# With coverage report
docker-compose exec pricegrid-api pytest --cov=app --cov-report=term-missing
```

### Via uv (local dev)

```bash
# Run all tests
uv run pytest

# Unit tests only
uv run pytest tests/unit

# Integration tests only
uv run pytest tests/integration

# With coverage report
uv run pytest --cov=app --cov-report=term-missing
```

### What the tests cover

**Unit tests** — pure business logic, no database or Redis:

- Spike detection: 25% above 30-day avg triggers alert, 10% does not
- Price averaging: correct rolling average across N records
- Role enforcement: vendor cannot create goods, viewer cannot submit prices

**Integration tests** — full API flow with test database:

- Auth: register → login → JWT → protected endpoint
- Price submission: vendor submits → stored → cache invalidated
- Comparison: cross-market query returns correct structure
- Alert flow: spike submission → alert recorded → appears in GET /alerts
- Permissions: viewer POST /prices → 403

---

## Sprint Log

| Sprint   | Focus                                       | Key Commits                                                                                                         |
| -------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Sprint 1 | Foundation — Docker, DB, Auth               | Project setup · Alembic init · User model · JWT auth endpoints · Auth tests                                         |
| Sprint 2 | Core Domain — Goods, Vendors, Prices        | CRUD endpoints · PriceRepository · PriceService · Redis cache on /current · Offset pagination on all list endpoints |
| Sprint 3 | Intelligence — Spike Detection & Alerts     | Spike logic · pub/sub publisher + consumer · price_alerts migration · Alert endpoints · Unit tests                  |
| Sprint 4 | Polish — History, Trends, Integration Tests | History endpoint · Trends endpoint · Cross-market compare · Full integration tests · README                         |
| Sprint 5 | SQLModel Migration                          | Replaced SQLAlchemy DeclarativeBase + Pydantic Out schemas with SQLModel · Collapsed schemas/ into schemas.py · Extracted auth deps to api/deps/ · Switched typecheck from mypy to pyright |

---

## Project Structure

```
pricegrid/
├── app/
│   ├── api/
│   │   ├── deps/        # Shared FastAPI dependencies (auth guards)
│   │   └── v1/          # FastAPI routers — routes only, no business logic
│   ├── services/        # Business logic layer
│   ├── repositories/    # Data access layer (Repository pattern)
│   ├── models/          # SQLModel table models — ORM + response schema in one
│   ├── schemas.py       # Pydantic input schemas (request payloads only)
│   ├── core/            # Config, DB session, Redis client
│   ├── events/          # Pub/sub publisher and consumer
│   └── main.py
├── alembic/             # Database migrations
├── tests/
│   ├── unit/
│   └── integration/
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

## v1 — Complete

PriceGrid v1 is feature-complete. All five sprints are shipped:

- Auth, roles, and JWT
- Goods, vendors, markets, and price submission
- Spike detection, pub/sub alerts, and threshold configuration
- Price history, cross-market comparison, and time-windowed trends
- Full SQLModel migration, unified schemas, and pyright type checking

The system is self-contained, fully tested (unit + integration), and runs end-to-end with a single `docker-compose up --build`.

---

## What v2 Could Look Like

These are the natural next layers if this were a production system:

| Feature | What it adds |
| ------- | ------------ |
| WebSocket push | Real-time price updates streamed to clients without polling |
| Alert delivery | Email or webhook notifications when a spike fires, not just a DB record |
| Bulk price submission | `POST /prices/bulk` for vendors submitting multiple prices in one request |
| Rate limiting | Per-vendor submission throttle to prevent price flooding |
| Vendor reputation | Track submission accuracy over time — flag vendors whose prices consistently deviate |
| Price forecasting | Simple moving-average or ARIMA forecast endpoint on top of the existing trend data |
| Multi-currency normalisation | Store an exchange rate snapshot at submission time so comparisons across currencies are meaningful |
| Read-only public API | Unauthenticated access to current prices and comparisons for open-data consumers |

---

## Author

> **Miracle Apata**
>
> GitHub: [@prmpsmart](https://github.com/prmpsmart)

---

## License

MIT
