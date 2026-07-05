import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from src.database.models import User


class SqlAlchemyUserRepository:
    """Реализация репозитория пользователей."""

    def __init__(self, db: DbSession) -> None:
        self._db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Находим пользователя по его уникальному идентификатору."""
        return self._db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        """Находим пользователя по его адресу электронной почты."""
        stmt = select(User).where(User.email == email)
        return self._db.execute(stmt).scalar_one_or_none()

    def create(self, user: User) -> User:
        """Сохраняем нового пользователя в базе данных."""
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update(self, user: User) -> User:
        """Изменения существующего пользователя в базе данных."""
        self._db.commit()
        self._db.refresh(user)
        return user
