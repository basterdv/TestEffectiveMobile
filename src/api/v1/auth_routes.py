from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.api.deps import CurrentUser, get_auth_service
from src.api.deps import bearer_scheme
from src.schemas.auth import (
    ErrorResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.services.auth_service import (
    AuthService,
    EmailAlreadyTakenError,
    InvalidCredentialsError,
)

router = APIRouter(
    prefix="/auth",
    tags=["Аутентификация"],
)

_401 = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Невалидный или отсутствующий токен",
    }
}
_409 = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "Email уже зарегистрирован",
    }
}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**_409},
    summary="Регистрация нового пользователя",
)
async def register(
    payload: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Регистрируем нового пользователя в системе."""
    try:
        user = await auth_service.register(
            last_name=payload.last_name,
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            email=payload.email,
            raw_password=payload.password,
        )
    except EmailAlreadyTakenError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={**_401},
    summary="Вход в систему",
    description="Возвращает opaque-токен сессии. Передавать в заголовке `Authorization: Bearer <token>`.",
)
async def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Аутентифицируем пользователя по паре email/пароль и создаем сессию доступа."""
    try:
        _, raw_token = await auth_service.login(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=raw_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
    description="Отзывает текущую сессию. Повторное использование токена вернёт 401.",
)
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Завершаем текущую сессию пользователя (выход из системы)."""
    await auth_service.logout(credentials.credentials)


@router.get(
    "/me",
    response_model=UserResponse,
    responses={**_401},
    summary="Текущий пользователь",
)
async def get_me(user: CurrentUser) -> UserResponse:
    """Возвращаем публичный профиль текущего аутентифицированного пользователя."""
    return UserResponse.model_validate(user)
