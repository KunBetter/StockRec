from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20, pattern=r"^\d+$")
    code: str = Field(..., min_length=4, max_length=6)


class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20, pattern=r"^\d+$")
    code: str = Field(..., min_length=4, max_length=6)
    nickname: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    user_uuid: str
    phone: str
    nickname: str | None = None
    avatar_url: str | None = None
    is_active: bool = True

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    user: UserResponse
