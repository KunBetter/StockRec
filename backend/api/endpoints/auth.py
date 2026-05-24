from fastapi import APIRouter, Depends, HTTPException, Request

from backend.auth.dependencies import get_current_user
from backend.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from backend.auth.service import login, logout, refresh_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def auth_login(body: LoginRequest):
    try:
        return login(body.phone, body.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/register", response_model=LoginResponse)
async def auth_register(body: RegisterRequest):
    return login(body.phone, body.code)


@router.post("/refresh", response_model=TokenResponse)
async def auth_refresh(body: RefreshRequest):
    try:
        return await refresh_access_token(body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def auth_logout(user_uuid: str = Depends(get_current_user)):
    await logout(user_uuid)
    return {"message": "Logged out successfully"}
