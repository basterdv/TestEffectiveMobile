import uuid

from src.database.models import Action, Permission, Resource, Role


class FakeRbacRepository:
    """Фейковый (in-memory) репозиторий для управления (RBAC)."""

    def __init__(self) -> None:
        self.roles: dict[uuid.UUID, Role] = {}
        self.resources: dict[str, Resource] = {}
        self.actions: dict[str, Action] = {}
        self.permissions: dict[uuid.UUID, Permission] = {}

    def seed_resource(self, code: str) -> Resource:
        """Создаем и сохраняем тестовый ресурс."""

        resource = Resource(id=uuid.uuid4(), code=code)
        self.resources[code] = resource
        return resource

    def seed_action(self, code: str) -> Action:
        """Создаем и сохраняем тестовое действие."""
        action = Action(id=uuid.uuid4(), code=code)
        self.actions[code] = action
        return action

    # --- Роли ---

    def list_roles(self) -> list[Role]:
        """Возвращаем список всех существующих ролей."""
        return list(self.roles.values())

    def get_role(self, role_id: uuid.UUID) -> Role | None:
        """Находим роль по её идентификатору."""
        return self.roles.get(role_id)

    def create_role(self, name: str, description: str | None) -> Role:
        """Создаем новую роль и инициализируем её список прав."""
        role = Role(id=uuid.uuid4(), name=name, description=description)
        role.permissions = []
        self.roles[role.id] = role
        return role

    def delete_role(self, role: Role) -> None:
        """Удаляем роль из репозитория."""
        self.roles.pop(role.id, None)

    # --- Ресурсы / Операции ---

    def list_resources(self) -> list[Resource]:
        """Возвращаем список всех созданных ресурсов."""
        return list(self.resources.values())

    def get_resource_by_code(self, code: str) -> Resource | None:
        """Находим ресурс по его текстовому коду."""
        return self.resources.get(code)

    def list_actions(self) -> list[Action]:
        """Возвращаем список всех созданных действий."""
        return list(self.actions.values())

    def get_action_by_code(self, code: str) -> Action | None:
        """Находим действие по его текстовому коду."""
        return self.actions.get(code)

    # --- Права доступа ---

    def list_permissions(self) -> list[Permission]:
        """Возвращаем список всех существующих разрешений."""
        return list(self.permissions.values())

    def get_permission(self, permission_id: uuid.UUID) -> Permission | None:
        """Находим разрешение по его идентификатору."""
        return self.permissions.get(permission_id)

    def create_permission(
        self, resource_id: uuid.UUID, action_id: uuid.UUID
    ) -> Permission:
        """Создаем новое разрешение, связывающее ресурс и действие."""
        permission = Permission(
            id=uuid.uuid4(), resource_id=resource_id, action_id=action_id
        )
        self.permissions[permission.id] = permission
        return permission

    def delete_permission(self, permission: Permission) -> None:
        """Удаляем разрешение из репозитория."""
        self.permissions.pop(permission.id, None)

    def assign_permission_to_role(self, role: Role, permission: Permission) -> None:
        """Назначаем разрешение конкретной роли, если его там еще нет."""
        if permission not in role.permissions:
            role.permissions.append(permission)

    def remove_permission_from_role(self, role: Role, permission: Permission) -> None:
        """Отзываем разрешение у конкретной роли."""
        if permission in role.permissions:
            role.permissions.remove(permission)

    # --- Доступ пользователя ---

    def get_user_permissions(self, user_id: uuid.UUID) -> list[Permission]:
        """Получаем полный список разрешений для конкретного пользователя."""
        raise NotImplementedError

    def has_permission(
        self, user_id: uuid.UUID, resource_code: str, action_code: str
    ) -> bool:
        """Проверяем, имеет ли пользователь доступ к указанному ресурсу и действию."""
        raise NotImplementedError
