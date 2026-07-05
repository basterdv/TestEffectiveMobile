from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.api.deps import CurrentUser, get_auth_service
from src.api.deps import bearer_scheme
from src.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.services.auth_service import (
    AuthService,
    EmailAlreadyTakenError,
    InvalidCredentialsError,
)

router = APIRouter(
    prefix="/auth",
    tags=["Аутентификация"],
)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
        payload: RegisterRequest,
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Регистрируем нового пользователя в системе."""
    try:
        user = auth_service.register(
            last_name=payload.last_name,
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            email=payload.email,
            raw_password=payload.password,
        )
    except EmailAlreadyTakenError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(
        payload: LoginRequest,
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Аутентифицируем пользователя по паре email/пароль и создаем сессию доступа."""
    try:
        _, raw_token = auth_service.login(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=raw_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Завершаем текущую сессию пользователя (выход из системы)."""
    auth_service.logout(credentials.credentials)


@router.get("/me", response_model=UserResponse)
def get_me(user: CurrentUser) -> UserResponse:
    """Возвращаем публичный профиль текущего аутентифицированного пользователя."""
    return UserResponse.model_validate(user)
