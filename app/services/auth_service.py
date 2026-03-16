"""Authentication service."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate, UserResponse


class AuthService:
    """Handles user registration and authentication."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: UserCreate) -> tuple[User, str]:
        """Register a new user and return user + JWT."""
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        hashed = hash_password(data.password)
        user = await self.user_repo.create(
            email=data.email,
            hashed_password=hashed,
            created_at=datetime.now(timezone.utc),
        )
        token = create_access_token(subject=str(user.id))
        return user, token

    async def authenticate(self, email: str, password: str) -> tuple[User, str] | None:
        """Authenticate user and return user + JWT if valid."""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        token = create_access_token(subject=str(user.id))
        return user, token
