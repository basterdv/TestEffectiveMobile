import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.schemas.auth import ErrorResponse
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
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Не авторизован",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Нет прав администратора",
        },
    },
)

_404 = {status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}}
_400 = {status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}}


@router.get(
    "/roles",
    response_model=list[RoleResponse],
    summary="Список ролей",
)
async def list_roles(
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> list[RoleResponse]:
    """Возвращаем список всех существующих ролей в системе."""
    return [RoleResponse.model_validate(r) for r in rbac_service.list_roles()]


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать роль",
)
async def create_role(
    payload: CreateRoleRequest,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> RoleResponse:
    """Создаем новую роль в системе."""
    return RoleResponse.model_validate(
        await rbac_service.create_role(payload.name, payload.description)
    )


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**_404},
    summary="Удалить роль",
)
async def delete_role(
    role_id: uuid.UUID,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> None:
    """Удаляем роль из системы по её идентификатору."""
    try:
        await rbac_service.delete_role(role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/permissions",
    response_model=list[PermissionResponse],
    summary="Список permissions",
)
async def list_permissions(
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
    responses={**_400},
    summary="Создать permission",
)
async def create_permission(
    payload: CreatePermissionRequest,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> PermissionResponse:
    """Создаем новое атомарное разрешение для существующей пары ресурс-действие."""
    try:
        permission = await rbac_service.create_permission(
            payload.resource_code, payload.action_code
        )
    except UnknownResourceOrActionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return PermissionResponse.model_validate(permission)


@router.delete(
    "/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**_404},
    summary="Удалить permission",
)
async def delete_permission(
    permission_id: uuid.UUID,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> None:
    """Удаляем атомарное разрешение из системы по его идентификатору."""
    try:
        await rbac_service.delete_permission(permission_id)
    except PermissionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/roles/{role_id}/permissions/{permission_id}",
    response_model=RoleResponse,
    responses={**_404},
    summary="Назначить permission роли",
)
async def assign_permission(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> RoleResponse:
    """Привязываем выбранное разрешение конкретной роли."""
    try:
        role = await rbac_service.assign_permission(role_id, permission_id)
    except (RoleNotFoundError, PermissionNotFoundError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RoleResponse.model_validate(role)


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    response_model=RoleResponse,
    responses={**_404},
    summary="Снять permission с роли",
)
async def revoke_permission(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    rbac_service: Annotated[RbacService, Depends(get_rbac_service)],
) -> RoleResponse:
    """Отзываем выбранное разрешение у конкретной роли."""
    try:
        role = await rbac_service.revoke_permission(role_id, permission_id)
    except (RoleNotFoundError, PermissionNotFoundError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RoleResponse.model_validate(role)
