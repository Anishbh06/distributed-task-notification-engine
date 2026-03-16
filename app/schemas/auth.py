"""Auth schemas."""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user in API responses."""

    id: str
    email: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for auth token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
