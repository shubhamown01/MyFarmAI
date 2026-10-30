"""Auth API schemas (P3-07) — flat envelopes per ADR-009."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    # Android clients request a refresh token; web gets a cookie session.
    android: bool = Field(default=False)


class SessionUserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str


class LoginResponse(BaseModel):
    user: SessionUserResponse
    # Web: session ID lives in an HttpOnly cookie; not returned in the body.
    # Android: bearer token returned here; cookie set only when not android.
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"


class AuthErrorResponse(BaseModel):
    detail: str
    error_code: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=32, max_length=128)


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str | None
    role: str
    preferred_language: str
    is_active: bool
