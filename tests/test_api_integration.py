import uuid

import pytest
from fastapi.testclient import TestClient

from src.api import deps
from src.database.models import Permission
from src.main import app
from tests.fakes import FakeSessionRepository, FakeUserRepository


class FakeRbacRepoForApi:
    """Минимальная in-memory реализация."""

    def __init__(self) -> None:
        self.granted: set[tuple[uuid.UUID, str, str]] = set()

    def grant(self, user_id: uuid.UUID, resource_code: str, action_code: str) -> None:
        """Напрямую выдаем пользователю право на действие с ресурсом."""
        self.granted.add((user_id, resource_code, action_code))

    def has_permission(
        self, user_id: uuid.UUID, resource_code: str, action_code: str
    ) -> bool:
        """Проверяем, было ли выдано конкретное право пользователю."""
        return (user_id, resource_code, action_code) in self.granted

    def get_user_permissions(self, user_id: uuid.UUID) -> list[Permission]:
        """Заглушка для получения списка объектов Permission."""
        return []


@pytest.fixture
def fake_state():
    """Фикстура для инициализации общего состояния тестовых in-memory репозиториев."""
    user_repo = FakeUserRepository()
    session_repo = FakeSessionRepository()
    rbac_repo = FakeRbacRepoForApi()
    return user_repo, session_repo, rbac_repo


@pytest.fixture
def client(fake_state):
    """Фикстура для создания тестового клиента FastAPI с подмененными зависимостями."""
    user_repo, session_repo, rbac_repo = fake_state

    def _override_auth_service():
        from src.services.auth_service import AuthService

        return AuthService(user_repo, session_repo, session_ttl_seconds=3600)

    def _override_user_service():
        from src.services.user_service import UserService

        return UserService(user_repo, session_repo)

    def _override_rbac_repo():
        return rbac_repo

    app.dependency_overrides[deps.get_auth_service] = _override_auth_service
    app.dependency_overrides[deps.get_user_service] = _override_user_service
    app.dependency_overrides[deps.get_rbac_repository] = _override_rbac_repo

    client_instance = TestClient(app)
    yield client_instance

    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, email: str = "ivan@example.ru") -> str:
    """Вспомогательный метод для быстрой регистрации и авторизации пользователя в тестах."""
    client.post(
        "/api/v1/auth/register",
        json={
            "last_name": "Ivanov",
            "first_name": "Ivan",
            "email": email,
            "password": "password123",
            "password_confirm": "password123",
        },
    )
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return resp.json()["access_token"]


def test_register_and_get_me(client: TestClient) -> None:
    """Проверяем, что после регистрации и входа можно успешно получить профиль пользователя."""
    token = _register_and_login(client)

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert resp.json()["email"] == "ivan@example.ru"


def test_protected_endpoint_without_token_returns_401(client: TestClient) -> None:
    """Проверяем, что запрос к защищенному эндпоинту без токена возвращает 401 Unauthorized."""
    resp = client.get("/api/v1/business/campaigns")
    assert resp.status_code == 401


def test_protected_endpoint_with_invalid_token_returns_401(client: TestClient) -> None:
    """Проверяем, что запрос с некорректным токеном возвращает 401 Unauthorized."""
    resp = client.get(
        "/api/v1/business/campaigns",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401


def test_authenticated_without_permission_returns_403(client: TestClient) -> None:
    """Проверяем, что аутентифицированный пользователь без нужных прав получает 403 Forbidden."""
    token = _register_and_login(client)

    resp = client.get(
        "/api/v1/business/campaigns",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


def test_authenticated_with_permission_returns_200(
    client: TestClient, fake_state
) -> None:
    """Проверяем, что при наличии выданного права эндпоинт успешно возвращает данные (200)."""
    user_repo, _, rbac_repo = fake_state
    token = _register_and_login(client)

    me_resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    user_id = uuid.UUID(me_resp.json()["id"])
    rbac_repo.grant(user_id, "campaigns", "read")

    resp = client.get(
        "/api/v1/business/campaigns", headers={"Authorization": f"Bearer {token}"}
    )

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) > 0


def test_logout_revokes_token(client: TestClient) -> None:
    """Проверяем, что после логаута токен становится невалидным (401)."""
    token = _register_and_login(client)

    logout_resp = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_resp.status_code == 204

    me_resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 401


def test_soft_delete_blocks_further_access(client: TestClient) -> None:
    """Проверяем, что мягкое удаление аккаунта блокирует последующий доступ к системе."""
    token = _register_and_login(client)

    delete_resp = client.delete(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_resp.status_code == 204

    me_resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 401


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    """Проверяем, что попытка регистрации на уже существующий email возвращает 409 Conflict."""
    _register_and_login(client, email="dup@example.ru")

    resp = client.post(
        "/api/v1/auth/register",
        json={
            "last_name": "Petrov",
            "first_name": "Petr",
            "email": "dup@example.ru",
            "password": "password456",
            "password_confirm": "password456",
        },
    )

    assert resp.status_code == 409


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    """Проверяем, что ввод неверного пароля при авторизации возвращает 401 Unauthorized."""
    _register_and_login(client, email="wrongpass@example.ru")

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.ru", "password": "incorrect"},
    )

    assert resp.status_code == 401
