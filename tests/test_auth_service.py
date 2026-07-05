import pytest

from src.services.auth_service import (
    AuthService,
    EmailAlreadyTakenError,
    InvalidCredentialsError,
)
from src.services.user_service import UserService
from tests.fakes import FakeSessionRepository, FakeUserRepository


@pytest.fixture
def auth_service() -> AuthService:
    """Фикстура для инициализации сервиса аутентификации с фейковыми репозиториями."""
    return AuthService(
        user_repo=FakeUserRepository(),
        session_repo=FakeSessionRepository(),
        session_ttl_seconds=3600,
    )


def test_register_creates_user(auth_service: AuthService) -> None:
    """Проверяем, что при корректных данных новый пользователь успешно создается."""
    user = auth_service.register(
        "Ivanov", "Ivan", None, "ivan@example.ru", "password123"
    )

    assert user.email == "ivan@example.ru"
    assert user.is_active is True
    assert user.hashed_password != "password123"


def test_register_duplicate_email_raises(auth_service: AuthService) -> None:
    """Проверяем, что повторная регистрация на один и тот же email вызывает ошибку."""
    auth_service.register("Ivanov", "Ivan", None, "ivan@example.ru", "password123")

    with pytest.raises(EmailAlreadyTakenError):
        auth_service.register("Petrov", "Petr", None, "ivan@example.ru", "password456")


def test_login_with_correct_credentials_returns_token(
    auth_service: AuthService,
) -> None:
    """Проверяем, что при вводе верных данных возвращается объект пользователя и токен."""
    auth_service.register("Ivanov", "Ivan", None, "ivan@example.ru", "password123")

    user, token = auth_service.login("ivan@example.ru", "password123")

    assert user.email == "ivan@example.ru"
    assert isinstance(token, str) and len(token) > 0


def test_login_with_wrong_password_raises(auth_service: AuthService) -> None:
    """Проверяем, что ввод неверного пароля для существующего аккаунта вызывает ошибку."""
    auth_service.register("Ivanov", "Ivan", None, "ivan@example.ru", "password123")

    with pytest.raises(InvalidCredentialsError):
        auth_service.login("ivan@example.ru", "wrong-password")


def test_login_unknown_email_raises(auth_service: AuthService) -> None:
    """Проверяем, что попытка входа с несуществующим в системе email вызывает ошибку."""
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("nobody@example.ru", "password123")


def test_get_user_by_token_returns_user_for_valid_token(
    auth_service: AuthService,
) -> None:
    """Проверяем, что по действующему токену можно успешно идентифицировать пользователя."""
    auth_service.register("Ivanov", "Ivan", None, "ivan@example.ru", "password123")
    _, token = auth_service.login("ivan@example.ru", "password123")

    user = auth_service.get_user_by_token(token)

    assert user is not None
    assert user.email == "ivan@example.ru"


def test_get_user_by_token_returns_none_for_unknown_token(
    auth_service: AuthService,
) -> None:
    """Проверяем, что при передаче несуществующего токена метод возвращает None."""
    assert auth_service.get_user_by_token("not-a-real-token") is None


def test_logout_invalidates_token(auth_service: AuthService) -> None:
    """Проверяем, что операция выхода из системы деактивирует токен сессии."""
    auth_service.register("Ivanov", "Ivan", None, "ivan@example.ru", "password123")
    _, token = auth_service.login("ivan@example.ru", "password123")

    auth_service.logout(token)

    assert auth_service.get_user_by_token(token) is None


def test_soft_delete_revokes_sessions_and_blocks_login() -> None:
    """Проверяем комплексный сценарий мягкого удаления аккаунта."""
    user_repo = FakeUserRepository()
    session_repo = FakeSessionRepository()
    auth_service = AuthService(user_repo, session_repo, session_ttl_seconds=3600)
    user_service = UserService(user_repo, session_repo)

    auth_service.register("Ivanov", "Ivan", None, "ivan@example.ru", "password123")
    user, token = auth_service.login("ivan@example.ru", "password123")

    user_service.delete_account(user)

    assert auth_service.get_user_by_token(token) is None
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("ivan@example.ru", "password123")
