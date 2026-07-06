import uuid

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_user_permissions(self, user_id: uuid.UUID) -> list[Permission]:
        """Получаем полный список уникальных разрешений, назначенных пользователю через его роли."""
        stmt = (
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
            .options(selectinload(Permission.resource), selectinload(Permission.action))
            .distinct()
        )
        return list((await self._db.execute(stmt)).scalars().all())

    async def has_permission(
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
        return bool((await self._db.execute(stmt)).scalar())

    # --- Роли ---

    async def list_roles(self) -> list[Role]:
        """Возвращаем список всех существующих ролей из базы данных."""
        result = await self._db.execute(select(Role))
        return list(result.scalars().all())

    async def get_role(self, role_id) -> Role | None:
        """Находим роль по её идентификатору."""
        return await self._db.get(
            Role, role_id, options=[selectinload(Role.permissions)]
        )

    async def create_role(self, name: str, description: str | None) -> Role:
        """Создаем и сохраняем новую роль в базе данных."""
        role = Role(name=name, description=description)
        role.permissions = []
        self._db.add(role)
        await self._db.commit()
        await self._db.refresh(role)
        return role

    async def delete_role(self, role: Role) -> None:
        """Удаляем роль из базы данных."""
        await self._db.delete(role)
        await self._db.commit()

    # --- Ресурсы и действия ---

    async def list_resources(self) -> list[Resource]:
        """Возвращаем список всех зарегистрированных ресурсов."""
        return list((await self._db.execute(select(Resource))).scalars().all())

    async def get_resource_by_code(self, code: str) -> Resource | None:
        """Находим системный ресурс по его строковому коду."""
        result = await self._db.execute(select(Resource).where(Resource.code == code))
        return result.scalar_one_or_none()

    async def list_actions(self) -> list[Action]:
        """Возвращаем список всех зарегистрированных атомарных действий."""
        return list((await self._db.execute(select(Action))).scalars().all())

    async def get_action_by_code(self, code: str) -> Action | None:
        """Находим атомарное действие по его строковому коду."""
        result = await self._db.execute(select(Action).where(Action.code == code))
        return result.scalar_one_or_none()

    # --- Доступы ---

    async def list_permissions(self) -> list[Permission]:
        """Возвращаем список всех существующих атомарных разрешений."""
        stmt = select(Permission).options(
            selectinload(Permission.resource), selectinload(Permission.action)
        )
        return list((await self._db.execute(stmt)).scalars().all())

    async def get_permission(self, permission_id) -> Permission | None:
        """Находим атомарное разрешение по его идентификатору."""
        return await self._db.get(
            Permission,
            permission_id,
            options=[
                selectinload(Permission.resource),
                selectinload(Permission.action),
            ],
        )

    async def create_permission(self, resource_id, action_id) -> Permission:
        """Создаем и сохраняем новую связь разрешения между ресурсом и действием."""
        permission = Permission(resource_id=resource_id, action_id=action_id)
        self._db.add(permission)
        await self._db.commit()
        await self._db.refresh(permission)
        return await self.get_permission(permission.id)

    async def delete_permission(self, permission: Permission) -> None:
        """Удаляем разрешение из базы данных."""
        await self._db.delete(permission)
        await self._db.commit()

    async def assign_permission_to_role(
        self, role: Role, permission: Permission
    ) -> None:
        """Привязываем разрешение к роли, если оно еще не было привязано."""
        await self._db.refresh(role, ["permissions"])
        if permission not in role.permissions:
            role.permissions.append(permission)
            await self._db.commit()

    async def remove_permission_from_role(
        self, role: Role, permission: Permission
    ) -> None:
        """Отзываем разрешение у конкретной роли, если оно было назначено."""
        await self._db.refresh(role, ["permissions"])
        if permission in role.permissions:
            role.permissions.remove(permission)
            await self._db.commit()
