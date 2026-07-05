import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_rbac_service, require_permission
from src.schemas.rbac import (
    CreatePermissionRequest,
    CreateRoleRequest,
    PermissionResponse,
    RoleResponse,
)
from src.services.rbac_service import (
    PermissionNotFoundError,
    RbacService,
    RoleNotFoundError,
    UnknownResourceOrActionError,
)

router = APIRouter(
    prefix="/admin/rbac",
    tags=["Администрирование системы управления доступом на основе ролей"],
    dependencies=[Depends(require_permission("rbac", "manage"))],
)


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> list[RoleResponse]:
    """Возвращаем список всех существующих ролей в системе."""
    return [RoleResponse.model_validate(r) for r in rbac_service.list_roles()]


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: CreateRoleRequest,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> RoleResponse:
    """Создаем новую роль в системе."""
    role = rbac_service.create_role(payload.name, payload.description)
    return RoleResponse.model_validate(role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: uuid.UUID,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> None:
    """Удаляем роль из системы по её идентификатору."""
    try:
        rbac_service.delete_role(role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions(
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> list[PermissionResponse]:
    """Возвращаем список всех атомарных разрешений, зарегистрированных в системе."""
    return [
        PermissionResponse.model_validate(p) for p in rbac_service.list_permissions()
    ]


@router.post(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_permission(
    payload: CreatePermissionRequest,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> PermissionResponse:
    """Создаем новое атомарное разрешение для существующей пары ресурс-действие."""
    try:
        permission = rbac_service.create_permission(
            payload.resource_code, payload.action_code
        )
    except UnknownResourceOrActionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return PermissionResponse.model_validate(permission)


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    permission_id: uuid.UUID,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> None:
    """Удаляем атомарное разрешение из системы по его идентификатору."""
    try:
        rbac_service.delete_permission(permission_id)
    except PermissionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/roles/{role_id}/permissions/{permission_id}", response_model=RoleResponse
)
def assign_permission(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> RoleResponse:
    """Привязываем выбранное разрешение конкретной роли."""
    try:
        role = rbac_service.assign_permission(role_id, permission_id)
    except (RoleNotFoundError, PermissionNotFoundError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RoleResponse.model_validate(role)


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}", response_model=RoleResponse
)
def revoke_permission(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> RoleResponse:
    """Отзываем выбранное разрешение у конкретной роли."""
    try:
        role = rbac_service.revoke_permission(role_id, permission_id)
    except (RoleNotFoundError, PermissionNotFoundError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RoleResponse.model_validate(role)
