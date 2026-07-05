"""
Наполняет БД минимальным набором тестовых данных для демонстрации.
"""

from src.core.security import hash_password
from src.database.db import SessionLocal, engine
from src.database.models import Action, Base, Permission, Resource, Role, User
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


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        resources = {
            code: Resource(code=code, description=desc)
            for code, desc in RESOURCES.items()
        }

        actions = {
            code: Action(code=code, description=desc) for code, desc in ACTIONS.items()
        }

        db.add_all([*resources.values(), *actions.values()])
        db.flush()

        permissions: dict[tuple[str, str], Permission] = {}

        for r in RESOURCES:
            for a in ACTIONS:
                perm = Permission(resource_id=resources[r].id, action_id=actions[a].id)
                db.add(perm)
                permissions[(r, a)] = perm
        db.flush()

        roles: dict[str, Role] = {}
        for role_name, role_data in ROLE_PERMISSIONS.items():
            role = Role(name=role_name, description=role_data["description"])
            role.permissions = [permissions[pair] for pair in role_data["permissions"]]
            db.add(role)
            roles[role_name] = role
        db.flush()

        for last_name, first_name, email, password, role_name in TEST_USERS:
            user = User(
                last_name=last_name,
                first_name=first_name,
                middle_name=None,
                email=email,
                hashed_password=hash_password(password),
                is_active=True,
            )
            user.roles = [roles[role_name]]
            db.add(user)

        db.commit()
        logger.info("Seed завершён успешно.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
