from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.deps import CurrentUser, get_user_service
from src.schemas.auth import UserResponse
from src.schemas.rbac import UpdateProfileRequest
from src.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Пользователи"],
)


@router.patch("/me", response_model=UserResponse)
def update_profile(
    payload: UpdateProfileRequest,
    user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Частично обновляем персональные данные профиля текущего пользователя."""
    updated = user_service.update_profile(
        user=user,
        last_name=payload.last_name,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
    )
    return UserResponse.model_validate(updated)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """Выполняем мягкое удаление (soft delete) аккаунта текущего пользователя."""
    user_service.delete_account(user)
