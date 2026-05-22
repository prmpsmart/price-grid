import uuid
from unittest.mock import AsyncMock, patch

import pytest
from uuid_extensions import uuid7

from app.models.user import User, UserRole
from app.schemas.auth import UserRegister
from app.services.auth_service import AuthService

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo) -> AuthService:
    return AuthService(mock_repo, AsyncMock())


# ── Password ──────────────────────────────────────────────────────────────────


def test_hash_and_verify_password(service: AuthService):
    hashed = service.hash_password("secret123")
    assert service.verify_password("secret123", hashed)
    assert not service.verify_password("wrong", hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────


def test_create_and_decode_token(service: AuthService):
    user_id = uuid7()
    token = service.create_access_token(user_id=str(user_id))
    token_data = service.decode_token(token)
    assert token_data.user_id == user_id


def test_decode_invalid_token_raises(service: AuthService):
    with pytest.raises(ValueError, match="Invalid or expired token"):
        service.decode_token("not.a.valid.token")


# ── Register ──────────────────────────────────────────────────────────────────


async def test_register_success(service: AuthService):
    with (
        patch.object(
            service.repo, "get_by_email", new_callable=AsyncMock
        ) as mock_get_by_email,
        patch.object(service.repo, "create", new_callable=AsyncMock) as mock_create,
    ):
        mock_get_by_email.return_value = None
        mock_create.return_value = User(
            id=uuid.uuid4(),
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.viewer,
        )

        result = await service.register(
            UserRegister(email="user@example.com", password="pass123")
        )

        assert result.email == "user@example.com"
        mock_create.assert_called_once()


async def test_register_duplicate_email_raises(service: AuthService):
    with patch.object(
        service.repo, "get_by_email", new_callable=AsyncMock
    ) as mock_get_by_email:
        mock_get_by_email.return_value = User(
            id=uuid.uuid4(),
            email="dup@example.com",
            hashed_password="x",
            role=UserRole.viewer,
        )

        with pytest.raises(ValueError, match="already registered"):
            await service.register(
                UserRegister(email="dup@example.com", password="pass")
            )


# ── Login ─────────────────────────────────────────────────────────────────────


async def test_login_success(service: AuthService):
    hashed = service.hash_password("correct")
    with patch.object(
        service.repo, "get_by_email", new_callable=AsyncMock
    ) as mock_get_by_email:
        mock_get_by_email.return_value = User(
            id=uuid.uuid4(),
            email="u@example.com",
            hashed_password=hashed,
            role=UserRole.viewer,
        )

        token = await service.login("u@example.com", "correct")
        assert isinstance(token, str)


async def test_login_wrong_password_raises(service: AuthService):
    hashed = service.hash_password("correct")
    with patch.object(
        service.repo, "get_by_email", new_callable=AsyncMock
    ) as mock_get_by_email:
        mock_get_by_email.return_value = User(
            id=uuid.uuid4(),
            email="u@example.com",
            hashed_password=hashed,
            role=UserRole.viewer,
        )

        with pytest.raises(ValueError, match="Invalid credentials"):
            await service.login("u@example.com", "wrong")


async def test_login_unknown_email_raises(service: AuthService):
    with patch.object(
        service.repo, "get_by_email", new_callable=AsyncMock
    ) as mock_get_by_email:
        mock_get_by_email.return_value = None

        with pytest.raises(ValueError, match="Invalid credentials"):
            await service.login("nobody@example.com", "any")
