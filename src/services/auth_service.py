from datetime import datetime, timedelta, timezone

from src.core.security import (
    generate_session_token,
    hash_password,
    hash_token,
    verify_password,
)
from src.database.models import Session as SessionModel
from src.database.models import User
from src.database.repositories.interfaces import SessionRepository, UserRepository


class AuthError(Exception):
    """Базовая ошибка аутентификации."""

    pass


class InvalidCredentialsError(AuthError):
    """Исключение, вызываемое при указании неверных учетных данных пользователя."""

    pass


class EmailAlreadyTakenError(AuthError):
    """Исключение, вызываемое при попытке зарегистрировать уже существующий в системе email."""

    pass


class AuthService:
    """Сервис для управления процессами аутентификации и сессиями пользователей."""

    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        session_ttl_seconds: int,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._session_ttl_seconds = session_ttl_seconds

    async def register(
        self,
        last_name: str,
        first_name: str,
        middle_name: str | None,
        email: str,
        raw_password: str,
    ) -> User:
        """Регистрирует нового пользователя в системе."""
        if await self._user_repo.get_by_email(email) is not None:
            raise EmailAlreadyTakenError(f"Email {email} уже зарегистрирован")

        user = User(
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            email=email,
            hashed_password=hash_password(raw_password),
            is_active=True,
        )
        return await self._user_repo.create(user)

    async def login(self, email: str, raw_password: str) -> tuple[User, str]:
        """Аутентифицирует пользователя и создаем новую сессию."""
        user = await self._user_repo.get_by_email(email)
        if (
            user is None
            or not user.is_active
            or not verify_password(raw_password, user.hashed_password)
        ):
            raise InvalidCredentialsError("Неверный email или пароль")

        raw_token = generate_session_token()
        now = datetime.now(timezone.utc)
        session = SessionModel(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            created_at=now,
            expires_at=now + timedelta(seconds=self._session_ttl_seconds),
        )
        await self._session_repo.create(session)
        return user, raw_token

    async def logout(self, raw_token: str) -> None:
        """Завершаем сессию пользователя (выход из системы)."""
        session = await self._session_repo.get_by_token_hash(hash_token(raw_token))
        if session is not None and session.is_valid:
            await self._session_repo.revoke(session)

    async def get_user_by_token(self, raw_token: str) -> User | None:
        """Идентифицируем и возвращаем пользователя по его сырому токену сессии."""
        session = await self._session_repo.get_by_token_hash(hash_token(raw_token))
        if session is None or not session.is_valid:
            return None
        user = await self._user_repo.get_by_id(session.user_id)
        if user is None or not user.is_active:
            return None
        return user
