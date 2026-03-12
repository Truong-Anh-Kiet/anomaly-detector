"""User and authentication related Pydantic schemas"""

from enum import StrEnum

from pydantic import BaseModel, Field


class RoleEnum(StrEnum):
    """User role enumeration"""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    ANALYST = "ANALYST"


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    """User response schema (excludes password_hash)"""
    user_id: str
    role: RoleEnum
    assigned_categories: list[str] | None = None
    created_at: str
    last_login: str | None = None

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """JWT token payload schema"""
    sub: str  # user_id
    role: RoleEnum
    assigned_categories: list[str] | None = None
    exp: int  # expiration timestamp
    token_type: str = "access"


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    expires_in: int
    user: UserResponse


class TokenRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Access token response schema"""
    access_token: str
    expires_in: int
