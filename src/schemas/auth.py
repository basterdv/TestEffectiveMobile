import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Схема валидации данных для запроса на регистрацию нового пользователя."""

    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    password_confirm: str

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        """Проверяем совпадение полей password и password_confirm."""
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Пароли не совпадают")
        return value


class LoginRequest(BaseModel):
    """Схема валидации данных для запроса на аутентификацию."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Схема ответа."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Схема ответа профиля пользователя."""

    id: uuid.UUID
    last_name: str
    first_name: str
    middle_name: str | None
    email: EmailStr
    is_active: bool

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    detail: str = Field(examples=["Описание ошибки"])
