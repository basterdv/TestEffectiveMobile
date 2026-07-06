import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from src.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.database.models.user import User


class Session(TimestampMixin, Base):
    """
    Серверная сессия пользователя.

    Используется opaque-токен (случайная строка), а не JWT — это позволяет
    мгновенно отзывать доступ (logout, блокировка аккаунта) без необходимости
    держать blacklist токенов или ждать истечения срока их жизни.
    """

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    user: Mapped["User"] = relationship(back_populates="sessions")

    @property
    def is_valid(self) -> bool:
        """Проверяем, активна ли сессия в данный момент."""
        if self.revoked_at is not None:
            return False

        now = datetime.now(timezone.utc)
        expires = self.expires_at

        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        return expires > now
