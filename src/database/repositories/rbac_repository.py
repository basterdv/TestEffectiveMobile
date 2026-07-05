import uuid

from sqlalchemy import select, exists, and_
from sqlalchemy.orm import Session as DbSession

from src.database.models import (
    Permission,
    Resource,
    Action,
    Role,
    user_roles,
    role_permissions,
)


class SqlAlchemyRbacRepository:
    """Реализация репозитория RBAC с использованием SQLAlchemy ORM."""

    def __init__(self, db: DbSession) -> None:
        self._db = db

    def get_user_permissions(self, user_id: uuid.UUID) -> list[Permission]:
        """Получаем полный список уникальных разрешений, назначенных пользователю через его роли."""
        stmt = (
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
            .distinct()
        )
        return list(self._db.execute(stmt).scalars().all())

    def has_permission(
        self, user_id: uuid.UUID, resource_code: str, action_code: str
    ) -> bool:
        """Проверяем наличие у пользователя права на выполнение действия над ресурсом."""
        stmt = select(
            exists().where(
                and_(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role_permissions.c.role_id,
                    role_permissions.c.permission_id == Permission.id,
                    Permission.resource_id == Resource.id,
                    Permission.action_id == Action.id,
                    Resource.code == resource_code,
                    Action.code == action_code,
                )
            )
        )
        return bool(self._db.execute(stmt).scalar())

    # --- Роли ---

    def list_roles(self) -> list[Role]:
        """Возвращаем список всех существующих ролей из базы данных."""
        return list(self._db.execute(select(Role)).scalars().all())

    def get_role(self, role_id) -> Role | None:
        """Находим роль по её идентификатору."""
        return self._db.get(Role, role_id)

    def create_role(self, name: str, description: str | None) -> Role:
        """Создаем и сохраняем новую роль в базе данных."""
        role = Role(name=name, description=description)
        self._db.add(role)
        self._db.commit()
        self._db.refresh(role)
        return role

    def delete_role(self, role: Role) -> None:
        """Удаляем роль из базы данных."""
        self._db.delete(role)
        self._db.commit()

    # --- Ресурсы и действия ---

    def list_resources(self) -> list[Resource]:
        """Возвращаем список всех зарегистрированных ресурсов."""
        return list(self._db.execute(select(Resource)).scalars().all())

    def get_resource_by_code(self, code: str) -> Resource | None:
        """Находим системный ресурс по его строковому коду."""
        stmt = select(Resource).where(Resource.code == code)
        return self._db.execute(stmt).scalar_one_or_none()

    def list_actions(self) -> list[Action]:
        """Возвращаем список всех зарегистрированных атомарных действий."""
        return list(self._db.execute(select(Action)).scalars().all())

    def get_action_by_code(self, code: str) -> Action | None:
        """Находим атомарное действие по его строковому коду."""
        stmt = select(Action).where(Action.code == code)
        return self._db.execute(stmt).scalar_one_or_none()

    # --- Доступы ---

    def list_permissions(self) -> list[Permission]:
        """Возвращаем список всех существующих атомарных разрешений."""
        return list(self._db.execute(select(Permission)).scalars().all())

    def get_permission(self, permission_id) -> Permission | None:
        """Находим атомарное разрешение по его идентификатору."""
        return self._db.get(Permission, permission_id)

    def create_permission(self, resource_id, action_id) -> Permission:
        """Создаем и сохраняем новую связь разрешения между ресурсом и действием."""
        permission = Permission(resource_id=resource_id, action_id=action_id)
        self._db.add(permission)
        self._db.commit()
        self._db.refresh(permission)
        return permission

    def delete_permission(self, permission: Permission) -> None:
        """Удаляем разрешение из базы данных."""
        self._db.delete(permission)
        self._db.commit()

    def assign_permission_to_role(self, role: Role, permission: Permission) -> None:
        """Привязываем разрешение к роли, если оно еще не было привязано."""
        if permission not in role.permissions:
            role.permissions.append(permission)
            self._db.commit()

    def remove_permission_from_role(self, role: Role, permission: Permission) -> None:
        """Отзываем разрешение у конкретной роли, если оно было назначено."""
        if permission in role.permissions:
            role.permissions.remove(permission)
            self._db.commit()
