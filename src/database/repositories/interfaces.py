import uuid
from typing import Protocol


from src.database.models import Action, Permission, Resource, Role, Session, User


class UserRepository(Protocol):
    """Интерфейс репозитория для управления данными пользователей."""

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Находим пользователя по его идентификатору."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Находим пользователя по его адресу электронной почты."""
        ...

    async def create(self, user: User) -> User:
        """Сохраняем нового пользователя в базе данных."""
        ...

    async def update(self, user: User) -> User:
        """Обновляем информацию о существующем пользователе."""
        ...


class SessionRepository(Protocol):
    """Интерфейс репозитория для управления сессиями пользователей."""

    async def create(self, session: Session) -> Session:
        """Сохраняем новую сессию в базе данных."""
        ...

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Находим сессию по хэшу её токена."""
        ...

    async def revoke(self, session: Session) -> None:
        """Отзываем конкретную сессию (деактивирует её)."""
        ...

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Принудительно закрывает все активные сессии конкретного пользователя."""
        ...


class RbacRepository(Protocol):
    """Интерфейс репозитория для управления ролями и правами доступа (RBAC)."""

    async def get_user_permissions(self, user_id: uuid.UUID) -> list[Permission]:
        """Получаем полный список всех разрешений, доступных пользователю."""
        ...

    async def has_permission(
        self, user_id: uuid.UUID, resource_code: str, action_code: str
    ) -> bool:
        """Проверяем, имеет ли пользователь доступ к ресурсу на выполнение действия."""
        ...

    async def list_roles(self) -> list[Role]:
        """Возвращаем список всех существующих ролей."""
        ...

    async def get_role(self, role_id: uuid.UUID) -> Role | None:
        """Находим роль по её идентификатору."""
        ...

    async def create_role(self, name: str, description: str | None) -> Role:
        """Создаем и регистрируем новую роль."""
        ...

    async def delete_role(self, role: Role) -> None:
        """Удаляем роль из системы."""
        ...

    async def list_resources(self) -> list[Resource]:
        """Возвращаем список всех зарегистрированных ресурсов системы."""
        ...

    async def get_resource_by_code(self, code: str) -> Resource | None:
        """Находим системный ресурс по его строковому коду."""
        ...

    async def list_actions(self) -> list[Action]:
        """Возвращаем список всех зарегистрированных атомарных действий."""
        ...

    async def get_action_by_code(self, code: str) -> Action | None:
        """Находим атомарное действие по его строковому коду."""
        ...

    async def list_permissions(self) -> list[Permission]:
        """Возвращаем список всех существующих атомарных связок разрешений."""
        ...

    async def get_permission(self, permission_id: uuid.UUID) -> Permission | None:
        """Находим связку разрешения по её идентификатору."""
        ...

    async def create_permission(
        self, resource_id: uuid.UUID, action_id: uuid.UUID
    ) -> Permission:
        """Создаем новое атомарное разрешение для пары ресурс-действие."""
        ...

    async def delete_permission(self, permission: Permission) -> None:
        """Удаляем существующее разрешение из системы."""
        ...

    async def assign_permission_to_role(
        self, role: Role, permission: Permission
    ) -> None:
        """Связываем выбранное разрешение конкретной роли."""
        ...

    async def remove_permission_from_role(
        self, role: Role, permission: Permission
    ) -> None:
        """Отзываем выбранное разрешение у конкретной роли."""
        ...
