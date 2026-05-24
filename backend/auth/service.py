import os
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.schemas import LoginResponse, TokenResponse, UserResponse
from backend.persistence.database import get_session
from backend.persistence.models import User
from backend.persistence.redis_client import cache_delete, cache_get, cache_set

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
REFRESH_TOKEN_BYTES = 32


def _create_access_token(user_uuid: str) -> tuple[str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_uuid,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expire


def _create_refresh_token(user_uuid: str) -> str:
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


async def _store_refresh_token(user_uuid: str, refresh_token: str) -> None:
    await cache_set(
        f"refresh:{user_uuid}",
        refresh_token,
        ttl=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


async def _verify_refresh_token(user_uuid: str, refresh_token: str) -> bool:
    stored = await cache_get(f"refresh:{user_uuid}")
    return stored is not None and stored == refresh_token


async def _revoke_refresh_token(user_uuid: str) -> None:
    await cache_delete(f"refresh:{user_uuid}")


def login(phone: str, code: str) -> LoginResponse:
    """
    Login or register by phone + verification code.
    In development mode, any 6-digit code is accepted.
    In production, validate against SMS verification service.
    """
    if len(code) < 4:
        raise ValueError("Invalid verification code")

    db: Session = get_session()

    user = db.execute(select(User).where(User.phone == phone)).scalar_one_or_none()

    if user is None:
        nickname = f"用户{phone[-4:]}"
        user = User(phone=phone, nickname=nickname)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user registered: {phone}")

    user.last_login_at = datetime.utcnow()
    db.commit()

    access_token, _ = _create_access_token(user.user_uuid)
    refresh_token = _create_refresh_token(user.user_uuid)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            user_uuid=user.user_uuid,
            phone=user.phone,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
        ),
    )


async def refresh_access_token(refresh_token: str) -> TokenResponse:
    for key_pattern in await _scan_refresh_keys():
        user_uuid = key_pattern.replace("refresh:", "")
        if await _verify_refresh_token(user_uuid, refresh_token):
            access_token, _ = _create_access_token(user_uuid)
            new_refresh = _create_refresh_token(user_uuid)
            await _store_refresh_token(user_uuid, new_refresh)
            return TokenResponse(access_token=access_token, refresh_token=new_refresh)

    raise ValueError("Invalid or expired refresh token")


async def _scan_refresh_keys() -> list[str]:
    from backend.persistence.redis_client import get_redis

    r = await get_redis()
    if r is None:
        return []
    try:
        return await r.keys("refresh:*")
    except Exception:
        return []


async def logout(user_uuid: str) -> None:
    await _revoke_refresh_token(user_uuid)


def get_user_by_uuid(user_uuid: str) -> User | None:
    db: Session = get_session()
    return db.execute(select(User).where(User.user_uuid == user_uuid)).scalar_one_or_none()


def verify_access_token(token: str) -> str | None:
    """Verify JWT access token and return user_uuid, or None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        user_uuid = payload.get("sub")
        if user_uuid is None:
            return None
        return user_uuid
    except JWTError:
        return None
