import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession

from src.database.models import Session


class SqlAlchemySessionRepository:
    """Реализация репозитория сессий."""

    def __init__(self, db: DbSession) -> None:
        self._db = db

    def create(self, session: Session) -> Session:
        """Сохраняем новую сессию в базе данных."""
        self._db.add(session)
        self._db.commit()
        self._db.refresh(session)
        return session

    def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Находим сессию по хэшу её токена доступа."""
        stmt = select(Session).where(Session.token_hash == token_hash)
        return self._db.execute(stmt).scalar_one_or_none()

    def revoke(self, session: Session) -> None:
        """Отзываем конкретную сессию."""
        session.revoked_at = datetime.now(timezone.utc)
        self._db.commit()

    def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Принудительно закрываем все активные сессии конкретного пользователя."""
        stmt = (
            update(Session)
            .where(Session.user_id == user_id, Session.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        self._db.execute(stmt)
        self._db.commit()
