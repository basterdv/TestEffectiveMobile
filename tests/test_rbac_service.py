import uuid

import pytest

from src.services.rbac_service import (
    PermissionNotFoundError,
    RbacService,
    RoleNotFoundError,
    UnknownResourceOrActionError,
)
from tests.fakes_rbac import FakeRbacRepository


@pytest.fixture
def rbac_repo() -> FakeRbacRepository:
    """Фикстура для инициализации фейкового репозитория RBAC."""
    repo = FakeRbacRepository()
    repo.seed_resource("campaigns")
    repo.seed_action("read")
    return repo


@pytest.fixture
def rbac_service(rbac_repo: FakeRbacRepository) -> RbacService:
    """Фикстура для инициализации сервиса RBAC."""
    return RbacService(rbac_repo)


def test_create_role(rbac_service: RbacService) -> None:
    """Проверяем, что новая роль успешно создается."""
    role = rbac_service.create_role("manager", "Менеджер кампаний")

    assert role.name == "manager"
    assert role in rbac_service.list_roles()


def test_delete_unknown_role_raises(rbac_service: RbacService) -> None:
    """Проверяем, что попытка удаления несуществующей роли вызывает ошибку RoleNotFoundError."""
    with pytest.raises(RoleNotFoundError):
        rbac_service.delete_role(uuid.uuid4())


def test_create_permission(rbac_service: RbacService) -> None:
    """Проверяем, что новое разрешение успешно создается для существующих ресурсов и действий."""
    permission = rbac_service.create_permission("campaigns", "read")

    assert permission in rbac_service.list_permissions()


def test_create_permission_unknown_resource_raises(rbac_service: RbacService) -> None:
    """Проверяем, что создание разрешения для несуществующего ресурса вызывает ошибку."""
    with pytest.raises(UnknownResourceOrActionError):
        rbac_service.create_permission("unknown-resource", "read")


def test_assign_and_revoke_permission(rbac_service: RbacService) -> None:
    """Проверяем полный цикл назначения и последующего отзыва разрешения у роли."""
    role = rbac_service.create_role("manager", None)
    permission = rbac_service.create_permission("campaigns", "read")

    updated_role = rbac_service.assign_permission(role.id, permission.id)
    assert permission in updated_role.permissions

    updated_role = rbac_service.revoke_permission(role.id, permission.id)
    assert permission not in updated_role.permissions


def test_assign_permission_unknown_role_raises(rbac_service: RbacService) -> None:
    """Проверяем, что попытка назначить разрешение несуществующей роли вызывает ошибку RoleNotFoundError."""
    permission = rbac_service.create_permission("campaigns", "read")

    with pytest.raises(RoleNotFoundError):
        rbac_service.assign_permission(uuid.uuid4(), permission.id)


def test_assign_unknown_permission_raises(rbac_service: RbacService) -> None:
    """Проверяем, что попытка назначить роли несуществующее разрешение вызывает ошибку PermissionNotFoundError."""
    role = rbac_service.create_role("manager", None)

    with pytest.raises(PermissionNotFoundError):
        rbac_service.assign_permission(role.id, uuid.uuid4())
