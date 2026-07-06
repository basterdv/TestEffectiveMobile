import uuid

from src.database.models import Permission, Role
from src.database.repositories.interfaces import RbacRepository


class RbacError(Exception):
    """Базовое исключение для всех ошибок, связанных с компонентами RBAC."""

    pass


class RoleNotFoundError(RbacError):
    """Исключение, вызываемое при попытке найти или изменить несуществующую роль."""

    pass


class PermissionNotFoundError(RbacError):
    """Исключение, вызываемое при попытке найти или изменить несуществующее разрешение."""

    pass


class UnknownResourceOrActionError(RbacError):
    """Исключение, вызываемое если указанный код ресурса или действия отсутствует в системе."""

    pass


class RbacService:
    """Сервис для управления ролевой моделью доступа (RBAC)."""

    def __init__(self, rbac_repo: RbacRepository) -> None:
        self._rbac_repo = rbac_repo

    async def list_roles(self) -> list[Role]:
        """Возвращаем список всех доступных в системе ролей."""
        return await self._rbac_repo.list_roles()

    async def create_role(self, name: str, description: str | None) -> Role:
        """Создает новую роль."""
        return await self._rbac_repo.create_role(name, description)

    async def delete_role(self, role_id: uuid.UUID) -> None:
        """Удаляет роль из системы по её идентификатору."""
        role = await self._rbac_repo.get_role(role_id)
        if role is None:
            raise RoleNotFoundError(f"Роль {role_id} не найдена")
        await self._rbac_repo.delete_role(role)

    async def list_permissions(self) -> list[Permission]:
        """Возвращает список всех существующих разрешений."""
        return await self._rbac_repo.list_permissions()

    async def create_permission(
        self, resource_code: str, action_code: str
    ) -> Permission:
        """Создаем новое разрешение, связывая существующий ресурс и действие."""
        resource = await self._rbac_repo.get_resource_by_code(resource_code)
        action = await self._rbac_repo.get_action_by_code(action_code)
        if resource is None or action is None:
            raise UnknownResourceOrActionError(
                f"Неизвестный resource_code={resource_code} или action_code={action_code}"
            )
        return await self._rbac_repo.create_permission(resource.id, action.id)

    async def delete_permission(self, permission_id: uuid.UUID) -> None:
        """Удаляем разрешение из системы по его идентификатору."""
        permission = await self._rbac_repo.get_permission(permission_id)
        if permission is None:
            raise PermissionNotFoundError(f"Permission {permission_id} не найден")
        await self._rbac_repo.delete_permission(permission)

    async def assign_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> Role:
        """Назначаем разрешение конкретной роли."""
        role = await self._rbac_repo.get_role(role_id)
        permission = await self._rbac_repo.get_permission(permission_id)
        if role is None:
            raise RoleNotFoundError(f"Роль {role_id} не найдена")
        if permission is None:
            raise PermissionNotFoundError(f"Permission {permission_id} не найден")
        await self._rbac_repo.assign_permission_to_role(role, permission)
        return role

    async def revoke_permission(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> Role:
        """Отзывает разрешение у конкретной роли."""
        role = await self._rbac_repo.get_role(role_id)
        permission = await self._rbac_repo.get_permission(permission_id)
        if role is None:
            raise RoleNotFoundError(f"Роль {role_id} не найдена")
        if permission is None:
            raise PermissionNotFoundError(f"Permission {permission_id} не найден")
        await self._rbac_repo.remove_permission_from_role(role, permission)
        return role
