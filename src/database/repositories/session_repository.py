import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Session


class SqlAlchemySessionRepository:
    """Реализация репозитория сессий."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, session: Session) -> Session:
        """Сохраняем новую сессию в базе данных."""
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return session

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Находим сессию по хэшу её токена доступа."""
        result = await self._db.execute(
            select(Session).where(Session.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, session: Session) -> None:
        """Отзываем конкретную сессию."""
        session.revoked_at = datetime.now(timezone.utc)
        await self._db.commit()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Принудительно закрываем все активные сессии конкретного пользователя."""
        await self._db.execute(
            update(Session)
            .where(Session.user_id == user_id, Session.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self._db.commit()
