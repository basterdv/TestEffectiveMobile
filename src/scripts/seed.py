"""
Наполняет БД минимальным набором тестовых данных для демонстрации.
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import settings
from src.core.security import hash_password
from src.database.models import Action, Permission, Resource, Role, User

from ..logger import logger

RESOURCES = {
    "campaigns": "Рекламные кампании",
    "reports": "Аналитические отчеты",
    "rbac": "Управление доступом (RBAC)",
}

ACTIONS = {
    "read": "Просмотр",
    "create": "Создание",
    "update": "Редактирование",
    "delete": "Удаление",
    "manage": "Полное управление",
}

ROLE_PERMISSIONS = {
    "admin": {
        "description": "Администратор системы с полным доступом ко всем ресурсам",
        "permissions": [(r, a) for r in RESOURCES for a in ACTIONS],
    },
    "manager": {
        "description": "Менеджер с правами управления кампаниями и просмотра отчетов",
        "permissions": [
            ("campaigns", "read"),
            ("campaigns", "create"),
            ("campaigns", "update"),
            ("reports", "read"),
        ],
    },
    "guest": {
        "description": "Гость с правами только на просмотр кампаний и отчетов",
        "permissions": [
            ("campaigns", "read"),
            ("reports", "read"),
        ],
    },
}

TEST_USERS = [
    ("Admin", "Admin", "admin@example.ru", "admin_password", "admin"),
    ("Manager", "Manager", "manager@example.ru", "manager_password", "manager"),
    ("Guest", "Guest", "guest@example.ru", "guest_password", "guest"),
]


async def seed() -> None:
    engine = create_async_engine(settings.database_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as db:
        try:
            resources = {}
            for code, desc in RESOURCES.items():
                res = await db.execute(select(Resource).where(Resource.code == code))
                obj = res.scalar_one_or_none()
                if not obj:
                    obj = Resource(code=code, description=desc)
                    db.add(obj)
                resources[code] = obj
            await db.flush()

            actions = {}
            for code, desc in ACTIONS.items():
                res = await db.execute(select(Action).where(Action.code == code))
                obj = res.scalar_one_or_none()
                if not obj:
                    obj = Action(code=code, description=desc)
                    db.add(obj)
                actions[code] = obj
            await db.flush()

            permissions: dict[tuple[str, str], Permission] = {}
            for r in RESOURCES:
                for a in ACTIONS:
                    res = await db.execute(
                        select(Permission).where(
                            Permission.resource_id == resources[r].id,
                            Permission.action_id == actions[a].id,
                        )
                    )
                    perm = res.scalar_one_or_none()
                    if not perm:
                        perm = Permission(
                            resource_id=resources[r].id, action_id=actions[a].id
                        )
                        db.add(perm)
                    permissions[(r, a)] = perm
            await db.flush()

            roles: dict[str, Role] = {}
            for role_name, role_data in ROLE_PERMISSIONS.items():
                res = await db.execute(select(Role).where(Role.name == role_name))
                role = res.scalar_one_or_none()
                if not role:
                    role = Role(name=role_name, description=role_data["description"])
                    db.add(role)
                    await db.flush()

                # Безопасно подгружаем связь в асинхронном режиме перед обновлением
                await db.refresh(role, attribute_names=["permissions"])
                role.permissions = [
                    permissions[pair] for pair in role_data["permissions"]
                ]
                roles[role_name] = role
            await db.flush()

            for last_name, first_name, email, password, role_name in TEST_USERS:
                res = await db.execute(select(User).where(User.email == email))
                user = res.scalar_one_or_none()
                if not user:
                    user = User(
                        last_name=last_name,
                        first_name=first_name,
                        middle_name=None,
                        email=email,
                        hashed_password=hash_password(password),
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()

                await db.refresh(user, attribute_names=["roles"])
                user.roles = [roles[role_name]]

            await db.commit()
            logger.info("Seed завершён успешно.")

        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка при заполнении БД: {e}")
            raise e

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
