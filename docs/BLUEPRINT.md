# PriceGrid

## Market Price Intelligence API

### Backend Portfolio Project — Full Technical Blueprint

**Stack:** FastAPI · PostgreSQL · SQLModel · Redis · Docker · pytest

---

## 1. Project Overview

PriceGrid is a self-contained backend API that tracks, stores, and exposes market price data for goods across vendors and locations. It enables price comparison, trend analysis, and real-time alerts when prices spike — solving the real problem of price opacity in everyday markets.

This project is designed to demonstrate production-level backend engineering across a modern Python stack, with clean architecture, meaningful tests, and a Docker-based deployment setup that mirrors real team environments.

### Problem Statement

In many markets — particularly in emerging economies — goods prices fluctuate with little transparency. Buyers have no reliable way to compare prices across vendors or track whether a current price is fair relative to historical data. PriceGrid simulates the backend layer of a system that would fix this.

### What It Is Not

- Not a web scraper — all price data is submitted via API
- Not dependent on any third-party service or API key
- Not a frontend application — purely a backend REST API
- Not a toy CRUD app — contains real business logic, constraints, and patterns

---

## 2. Skills Coverage Map

Every skill in the job description is exercised genuinely — not artificially bolted on.

| Skill                   | Where It Appears in PriceGrid                                                                                                 | Depth   |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------- |
| FastAPI                 | REST API layer: auth, price submission, comparison, alerts, search endpoints                                                  | Core    |
| PostgreSQL + SQLModel   | Relational schema: goods, vendors, markets, price records, users. Foreign keys, joins, constraints, Alembic migrations. Models serve as both ORM tables and API response schemas | Core    |
| Redis — Caching         | Current price cache per good/market. Cache invalidated on new submission. Heavy read optimisation                             | Core    |
| Redis — Pub/Sub         | Price spike events published to channel. Alert subscribers consume and log notifications                                      | Core    |
| Docker                  | API, PostgreSQL, Redis all containerised. Single `docker-compose up` spins everything                                         | Core    |
| pytest                  | Unit tests for business logic: spike detection, price averaging, alert rules. Integration tests for API endpoints             | Core    |
| Design Patterns         | Repository pattern for DB access. Service layer separating logic from routes. Observer via pub/sub. Factory for test fixtures | Core    |
| Git / Agile             | Sprint-based commit history. Feature branches per sprint. Meaningful commit messages that tell a story                        | Process |

---

## 3. System Architecture

### Service Layout

PriceGrid runs as a single containerised backend service with two external dependencies — both self-hosted via Docker Compose.

| Service         | Technology       | Role                                          |
| --------------- | ---------------- | --------------------------------------------- |
| pricegrid-api   | FastAPI (Python) | Main REST API — all business logic lives here |
| pricegrid-db    | PostgreSQL 15    | Primary data store — all persistent data      |
| pricegrid-cache | Redis 7          | Price caching + pub/sub event bus             |

### Request Flow

A price submission follows this path:

1. Client sends `POST /prices` with good, vendor, market, and price
2. FastAPI route receives and validates the request
3. Auth middleware checks JWT and role (only vendors/admins can submit)
4. `PriceService` checks for spikes against historical average
5. `PriceRepository` writes to PostgreSQL via SQLModel
6. Redis cache for that good/market is invalidated
7. If spike detected, event published to Redis pub/sub channel
8. Alert consumer logs or records the notification

### Folder Structure

```
pricegrid/
├── app/
│   ├── api/
│   │   ├── deps/            # Shared FastAPI dependencies
│   │   │   └── auth.py      # get_current_user, get_auth_service
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── prices.py
│   │       ├── goods.py
│   │       ├── vendors.py
│   │       ├── markets.py
│   │       └── alerts.py
│   ├── services/
│   │   ├── price_service.py
│   │   ├── alert_service.py
│   │   └── auth_service.py
│   ├── repositories/
│   │   ├── price_repo.py
│   │   ├── good_repo.py
│   │   └── vendor_repo.py
│   ├── models/              # SQLModel table models — ORM + response schema in one
│   │   ├── user.py
│   │   ├── good.py
│   │   ├── vendor.py
│   │   ├── market.py
│   │   └── price.py
│   ├── schemas.py           # Pydantic input schemas (request payloads only)
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── redis.py
│   ├── events/
│   │   ├── publisher.py
│   │   └── consumer.py
│   └── main.py
├── alembic/
├── tests/
│   ├── unit/
│   └── integration/
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

## 4. Database Design

### Core Entities

| Table         | Key Fields                                                                                              | Purpose                                   |
| ------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| users         | id (UUID PK), email, hashed_password, role (admin/vendor/viewer), created_at                            | Authentication and role-based access      |
| goods         | id (UUID PK), name, category, unit (kg/litre/piece), description                                       | Catalogue of trackable goods              |
| vendors       | id (UUID PK), name, location, user_id (UUID FK)                                                        | Vendors who submit prices                 |
| markets       | id (UUID PK), name, city, region                                                                       | Physical market locations                 |
| price_records | id (UUID PK), good_id (UUID FK), vendor_id (UUID FK), market_id (UUID FK), price, currency, submitted_at | Core price data — every submission stored |
| price_alerts  | id (UUID PK), good_id (UUID FK), market_id (UUID FK), threshold_pct, triggered_at, price_delta         | Log of spike events                       |

### Key Design Decisions

- All primary keys are UUIDs — avoids enumerable IDs and works naturally in distributed systems
- `price_records` is append-only — no updates, full audit trail
- Role separation enforced at DB level via `user.role` enum
- Foreign key constraints ensure referential integrity
- Alembic manages all schema changes — no manual SQL
- Indexes on `good_id + market_id + submitted_at` for fast time-series queries

---

## 5. API Endpoints

### Authentication

| Method | Endpoint              | Description              | Auth     |
| ------ | --------------------- | ------------------------ | -------- |
| POST   | /api/v1/auth/register | Register a new user      | None     |
| POST   | /api/v1/auth/login    | Login, receive JWT token | None     |
| GET    | /api/v1/auth/me       | Get current user profile | Required |

### Goods & Vendors

| Method | Endpoint        | Description                                              | Auth   | Pagination         |
| ------ | --------------- | -------------------------------------------------------- | ------ | ------------------ |
| GET    | /api/v1/goods   | List trackable goods (Redis cached, in-memory paginated) | None   | `?page=1&limit=20` |
| POST   | /api/v1/goods   | Create a new good                                        | Admin  | —                  |
| GET    | /api/v1/vendors | List all vendors                                         | None   | `?page=1&limit=20` |
| POST   | /api/v1/vendors | Register as a vendor                                     | Vendor | —                  |
| GET    | /api/v1/markets | List all markets                                         | None   | `?page=1&limit=20` |
| POST   | /api/v1/markets | Create a market                                          | Admin  | —                  |

All list endpoints return a paginated envelope: `{ items, total, page, limit }`. `limit` is capped at 100.

### Prices — Core Feature

| Method | Endpoint                         | Description                                          | Auth   | Pagination         |
| ------ | -------------------------------- | ---------------------------------------------------- | ------ | ------------------ |
| POST   | /api/v1/prices                   | Submit a price for a good at a market                | Vendor | —                  |
| GET    | /api/v1/prices                   | Query prices with filters (good, market, date range) | None   | `?page=1&limit=20` |
| GET    | /api/v1/prices/current           | Latest price per good per market (Redis cached)      | None   | `?page=1&limit=20` |
| GET    | /api/v1/prices/history/{good_id} | Price history for a specific good                    | None   | —                  |
| GET    | /api/v1/prices/compare           | Compare current prices across markets for a good     | None   | —                  |
| GET    | /api/v1/prices/trends            | Average price over time window (7d, 30d)             | None   | —                  |

### Alerts

| Method | Endpoint                  | Description                                  | Auth  |
| ------ | ------------------------- | -------------------------------------------- | ----- |
| GET    | /api/v1/alerts            | List all triggered spike alerts              | Admin |
| GET    | /api/v1/alerts/{good_id}  | Alerts for a specific good                   | None  |
| POST   | /api/v1/alerts/thresholds | Set custom spike threshold for a good/market | Admin |

---

## 6. Redis Strategy

### Caching

The most frequently hit endpoint is `GET /prices/current` — the latest price for every good per market. This is read-heavy and changes only when a new submission comes in.

- Cache key pattern: `price:current:{good_id}:{market_id}`
- TTL: 5 minutes (safety net; primarily invalidated on write)
- On new price submission: cache for that good+market key is deleted
- On cache miss: query PostgreSQL, set cache, return result

> This demonstrates knowing _what_ to cache and _why_ — not just using Redis because it was listed.

### Pub/Sub — Price Spike Alerts

When a new price is submitted, `PriceService` checks it against the rolling 30-day average for that good in that market. If the deviation exceeds the threshold (default 20%), a spike event is published.

- Publisher: `price_service.py` publishes to channel `price:spikes`
- Payload: `good_id, market_id, previous_avg, new_price, delta_pct, submitted_at`
- Consumer: runs as a background task on app startup, listens on `price:spikes`
- On event received: writes to `price_alerts` table, logs the event

> This is the Observer pattern implemented via Redis pub/sub — exactly how production event-driven systems work.

---

## 7. Design Patterns Used

| Pattern              | Where Used                                                                                                       | Why It Matters                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Repository Pattern   | `price_repo.py`, `good_repo.py`, `vendor_repo.py` — all DB access goes through repos, never directly from routes | Separates data access from business logic. Makes testing easy — swap real DB for mock |
| Service Layer        | `price_service.py`, `alert_service.py` — all business rules live here, routes just call services                 | Routes stay thin. Logic is testable in isolation without HTTP context                 |
| Observer Pattern     | Redis pub/sub — price submission triggers spike alert downstream without coupling the two                        | Decoupled, event-driven design. Adding new consumers doesn't change the publisher     |
| Dependency Injection | FastAPI's `Depends()` used for DB sessions, Redis client, current user — injected into routes                    | Testable, swappable dependencies. No global state                                     |
| Factory Pattern      | `conftest.py` — test fixtures create consistent test data (goods, vendors, prices) for each test                 | Clean, repeatable test setup. Each test starts from a known state                     |
| Pagination           | `BaseRepository.paginate_offset()` — shared offset pagination used by all list repos; goods service paginates in-memory from the Redis cache | Consistent `{items, total, page, limit}` envelope across every list endpoint. One COUNT + one SELECT per page request |

---

## 8. Testing Strategy

### Unit Tests — Business Logic

Tests that verify the rules of the system without touching the database or Redis:

- Spike detection: price 25% above 30-day avg triggers alert, 10% does not
- Price averaging: correct rolling average across N records
- Role enforcement: vendor cannot create goods, viewer cannot submit prices
- Cache key generation: correct format for different good/market combinations

### Integration Tests — API Endpoints

Tests that hit the actual FastAPI endpoints using `TestClient` with a test database:

- Auth flow: register → login → receive JWT → use protected endpoint
- Price submission: valid vendor submits → stored in DB → cache invalidated
- Price comparison: query across multiple markets returns correct structure
- Alert flow: spike submission → alert appears in `GET /alerts`
- Permissions: viewer trying to `POST /prices` returns 403

### Test File Structure

```
tests/
├── unit/
│   ├── test_price_service.py      # Spike detection, averaging logic
│   ├── test_alert_service.py      # Alert threshold rules
│   └── test_auth_service.py       # Password hashing, token validation
└── integration/
    ├── test_auth_endpoints.py     # Register, login, /me
    ├── test_price_endpoints.py    # Full price submission + query flow
    ├── test_comparison.py         # Cross-market comparison endpoint
    └── conftest.py                # Fixtures: test DB, test client, seed data
```

---

## 9. Sprint Breakdown

Four focused sprints. Each one is a shippable slice of the system.

| Sprint                | Focus                 | Deliverables                                                                                                                                                       | Skills Demonstrated                                            |
| --------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| Sprint 1 (Days 1–3)   | Foundation            | Project setup, Docker Compose, PostgreSQL connection, Alembic migrations, User model, JWT auth endpoints, basic tests                                              | Docker, PostgreSQL, SQLModel, FastAPI, pytest                  |
| Sprint 2 (Days 4–6)   | Core Domain           | Goods, Vendors, Markets CRUD. Price submission endpoint. PriceRepository. PriceService (no spike logic yet). Redis cache on GET /prices/current. Offset pagination (`page`, `total`, `limit`) on all list endpoints | Repository pattern, Service layer, Redis caching, pagination   |
| Sprint 3 (Days 7–9)   | Intelligence Layer    | Spike detection logic in PriceService. Redis pub/sub publisher + consumer. price_alerts table + migration. Alert endpoints. Full unit test coverage of spike logic | Observer pattern, pub/sub, business logic testing              |
| Sprint 4 (Days 10–12) | Polish & Completeness | Price history endpoint. Trend/average endpoint. Cross-market comparison. Integration tests. README with architecture diagram. .env.example. Clean commit history   | Integration testing, documentation, engineering best practices |
| Sprint 5              | SQLModel Migration    | Replaced SQLAlchemy DeclarativeBase + separate Pydantic Out schemas with SQLModel. Collapsed `schemas/` into `schemas.py`. Extracted auth deps to `api/deps/`. Switched type checker from mypy to pyright | SQLModel, architectural refactoring                           |

---

## 10. How to Talk About This Project

### The One-Line Answer

> "I built a market price intelligence API that tracks good prices across vendors and markets, flags price spikes in real time, and caches high-traffic reads — fully containerised with Docker and covered by a meaningful test suite."

### When They Ask Why You Built It

> "Price instability in everyday markets is a real problem — people have no visibility into whether a price they're being charged is fair relative to what others are paying or what it was last week. I wanted to simulate what the backend layer of a transparency system would look like, and it turned out to be a great canvas for demonstrating the full stack."

### When They Ask About Specific Decisions

- **Redis caching:** "I cache the current price endpoint because it's read constantly but only changes on a new submission — so I invalidate on write rather than relying solely on TTL. That's intentional, not default behaviour."
- **Pub/Sub:** "Spike alerts are decoupled from price submission using Redis pub/sub. The price service doesn't know about alerts — it just publishes an event. This means I can add new consumers later without touching the publisher."
- **Repository pattern:** "All database access goes through repository classes. This means my service layer can be tested without a real database — I just pass in a mock repository."
- **Alembic:** "Every schema change is a migration. There's no manual SQL anywhere. This is how real teams manage database changes."
- **Pagination:** "Every list endpoint returns a consistent `{items, total, page, limit}` envelope. The base repository handles the COUNT + offset query so repos don't repeat that logic. Goods are a special case — because the full list is already in Redis, I paginate in memory rather than doing an extra DB round trip."

---

## 11. README Structure (for GitHub)

Your README is the first thing a hiring manager sees. Structure it as a product document, not a school project.

- **PriceGrid** — one-line description of what it does and why
- **Architecture diagram** — simple ASCII or image showing API → PostgreSQL + Redis
- **Tech Stack** — clean table: tool + why you chose it
- **Getting Started** — `docker-compose up` and it works. No setup friction.
- **API Reference** — key endpoints with example request/response
- **Design Decisions** — 3–4 short paragraphs explaining non-obvious choices
- **Running Tests** — pytest command, what the tests cover
- **Sprint Log** — optional but impressive, links commits to sprint goals

---

> **Build it sprint by sprint.**
> The goal is not a perfect system. It is a system that tells a clear story about how you think.
