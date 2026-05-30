from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.service import get_user_by_uuid, verify_access_token

security = HTTPBearer(auto_error=False)

# Paths that do not require authentication
PUBLIC_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/health",
    "/api/v1/health/",
    "/api/v1/data/freshness",
    "/docs",
    "/openapi.json",
}


def is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith("/ws/")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """Extract and verify JWT token, return user_uuid."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_uuid = verify_access_token(token)

    if user_uuid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_uuid(user_uuid)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user.user_uuid


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """Extract user if token present, otherwise return None."""
    if credentials is None:
        return None
    user_uuid = verify_access_token(credentials.credentials)
    if user_uuid is None:
        return None
    user = get_user_by_uuid(user_uuid)
    if user is None or not user.is_active:
        return None
    return user.user_uuid
