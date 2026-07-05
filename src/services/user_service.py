from src.database.models import User
from src.database.repositories.interfaces import SessionRepository, UserRepository


class UserService:
    """Сервис для управления профилями пользователей и их учетными записями."""

    def __init__(
        self, user_repo: UserRepository, session_repo: SessionRepository
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo

    def update_profile(
        self,
        user: User,
        last_name: str | None,
        first_name: str | None,
        middle_name: str | None,
    ) -> User:
        """Обновляем персональные данные профиля пользователя."""
        if last_name is not None:
            user.last_name = last_name
        if first_name is not None:
            user.first_name = first_name
        if middle_name is not None:
            user.middle_name = middle_name
        return self._user_repo.update(user)

    def delete_account(self, user: User) -> None:
        """Выполняем мягкое удаление учетной записи пользователя."""
        user.is_active = False
        self._user_repo.update(user)
        self._session_repo.revoke_all_for_user(user.id)
