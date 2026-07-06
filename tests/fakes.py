import uuid
from datetime import datetime, timezone

from src.database.models import Session, User


class FakeUserRepository:
    """Фейковый (in-memory) репозиторий для управления пользователями."""

    def __init__(self) -> None:
        self._users: dict[uuid.UUID, User] = {}

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Находим пользователя по его идентификатору."""
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Находим пользователя по его адресу электронной почты."""
        return next((u for u in self._users.values() if u.email == email), None)

    async def create(self, user: User) -> User:
        """Сохраняем нового пользователя в репозитории."""
        if user.id is None:
            user.id = uuid.uuid4()
        self._users[user.id] = user
        return user

    async def update(self, user: User) -> User:
        """Обновляем данные существующего пользователя."""
        self._users[user.id] = user
        return user


class FakeSessionRepository:
    """Фейковый (in-memory) репозиторий для управления сессиями пользователей."""

    def __init__(self) -> None:
        self._sessions: dict[uuid.UUID, Session] = {}

    async def create(self, session: Session) -> Session:
        """Создаем и сохраняет новую сессию в репозитории."""
        if session.id is None:
            session.id = uuid.uuid4()
        self._sessions[session.id] = session
        return session

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Находим сессию по хэшу её токена."""
        return next(
            (s for s in self._sessions.values() if s.token_hash == token_hash), None
        )

    async def revoke(self, session: Session) -> None:
        """Отзываем конкретную сессию."""
        session.revoked_at = datetime.now(timezone.utc)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Отзываем все активные сессии конкретного пользователя."""
        for s in self._sessions.values():
            if s.user_id == user_id and s.revoked_at is None:
                s.revoked_at = datetime.now(timezone.utc)
