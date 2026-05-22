import pytest
from httpx import AsyncClient


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "fixture@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    return {"email": "fixture@example.com", "password": "password123", **resp.json()}


# ── Register ──────────────────────────────────────────────────────────────────

async def test_register_returns_user(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "password123", "role": "viewer"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["role"] == "viewer"
    # id must be a valid UUID string
    import uuid
    uuid.UUID(data["id"])
    assert "hashed_password" not in data


async def test_register_duplicate_email_returns_400(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


# ── Login ─────────────────────────────────────────────────────────────────────

async def test_login_returns_token(client: AsyncClient, registered_user: dict):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(client: AsyncClient, registered_user: dict):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "any"},
    )
    assert resp.status_code == 401


# ── /me ───────────────────────────────────────────────────────────────────────

async def test_me_returns_current_user(client: AsyncClient, registered_user: dict):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    token = login.json()["access_token"]

    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == registered_user["email"]


async def test_me_without_token_returns_403(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403


async def test_me_with_invalid_token_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401
