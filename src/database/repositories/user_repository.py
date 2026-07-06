import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User


class SqlAlchemyUserRepository:
    """Реализация репозитория пользователей."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Находим пользователя по его уникальному идентификатору."""
        return await self._db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Находим пользователя по его адресу электронной почты."""
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Сохраняем нового пользователя в базе данных."""
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Изменения существующего пользователя в базе данных."""
        await self._db.commit()
        await self._db.refresh(user)
        return user
