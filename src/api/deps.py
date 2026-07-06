from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.database.db import get_db
from src.database.models import User
from src.database.repositories.rbac_repository import SqlAlchemyRbacRepository
from src.database.repositories.session_repository import SqlAlchemySessionRepository
from src.database.repositories.user_repository import SqlAlchemyUserRepository
from src.services.auth_service import AuthService
from src.services.rbac_service import RbacService
from src.services.user_service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    """Создаем и возвращаем экземпляр сервиса аутентификации."""
    return AuthService(
        user_repo=SqlAlchemyUserRepository(db),
        session_repo=SqlAlchemySessionRepository(db),
        session_ttl_seconds=settings.session_ttl_seconds,
    )


async def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Создаем и возвращаем экземпляр сервиса управления пользователями."""
    return UserService(
        user_repo=SqlAlchemyUserRepository(db),
        session_repo=SqlAlchemySessionRepository(db),
    )


async def get_rbac_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SqlAlchemyRbacRepository:
    """Создаем и возвращаем экземпляр репозитория ролевой модели доступа."""
    return SqlAlchemyRbacRepository(db)


async def get_rbac_service(
    rbac_repo: Annotated[SqlAlchemyRbacRepository, Depends(get_rbac_repository)],
) -> RbacService:
    """Создаем и возвращаем экземпляр сервиса управления доступом."""
    return RbacService(rbac_repo)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Извлекаем, валидируем токен из заголовка и возвращаем текущего пользователя."""
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Не предоставлен токен"
        )

    user = await auth_service.get_user_by_token(credentials.credentials)

    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Невалидная или истёкшая сессия"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(resource_code: str, action_code: str):
    """
    Dependency-фабрика: проверяет, что у текущего пользователя есть permission
    (resource_code, action_code) через его роли. 401 уже отработан в get_current_user,
    здесь возможна только 403.
    """

    async def _checker(
        user: CurrentUser,
        rbac_repo: Annotated[SqlAlchemyRbacRepository, Depends(get_rbac_repository)],
    ) -> User:
        if not await rbac_repo.has_permission(user.id, resource_code, action_code):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав: требуется ({resource_code}, {action_code})",
            )
        return user

    return _checker
