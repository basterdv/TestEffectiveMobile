import uuid

from pydantic import BaseModel, Field


class RoleResponse(BaseModel):
    """Схема ответа, содержащая информацию о роли пользователя."""

    id: uuid.UUID
    name: str
    description: str | None

    model_config = {"from_attributes": True}


class CreateRoleRequest(BaseModel):
    """Схема валидации данных для запроса на создание новой роли."""

    name: str = Field(min_length=1, max_length=50)
    description: str | None = None


class ResourceResponse(BaseModel):
    """Схема ответа, представляющая защищаемый системный ресурс."""

    id: uuid.UUID
    code: str
    description: str | None

    model_config = {"from_attributes": True}


class ActionResponse(BaseModel):
    """Схема ответа, представляющая атомарное действие над ресурсом."""

    id: uuid.UUID
    code: str
    description: str | None

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    """Схема ответа, связывающая конкретный ресурс и разрешенное действие."""

    id: uuid.UUID
    resource: ResourceResponse
    action: ActionResponse

    model_config = {"from_attributes": True}


class CreatePermissionRequest(BaseModel):
    """Схема валидации данных для запроса на создание нового разрешения."""

    resource_code: str
    action_code: str


class UpdateProfileRequest(BaseModel):
    """Схема валидации данных для изменения персональной информации пользователя."""

    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    middle_name: str | None = None
