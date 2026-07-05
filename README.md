# Система аутентификации и авторизации

## Стек

FastAPI + SQLAlchemy 2.0 (sync) + PostgreSQL + Docker Compose.
Без `django.contrib.auth` / `fastapi-users` / `Authlib` "из коробки" — аутентификация
и проверка прав реализованы вручную.

## Аутентификация

Используется **серверная сессия с opaque-токеном**, а не JWT.

1. При логине генерируется случайный токен (`secrets.token_urlsafe`), в БД
   сохраняется не сам токен, а его хэш (`sessions.token_hash`) — аналогично
   паролям. Сырой токен отдаётся клиенту один раз, в `Authorization: Bearer <token>`.
2. При каждом запросе токен хэшируется и ищется в `sessions`. Сессия валидна,
   если `revoked_at IS NULL` и `expires_at > now()`.
3. Logout — установка `revoked_at = now()` у текущей сессии.
4. Soft delete пользователя — `users.is_active = False` + отзыв всех его сессий.
   После этого логин для него невозможен (проверка `is_active` на этапе login),
   а активные токены перестают проходить проверку.

Если входящий запрос не содержит валидного токена сессии → **401 Unauthorized**.

## Авторизация (RBAC: resource × action)

Права не привязаны напрямую к пользователю — они идут через роли, что даёт
гибкость.

### Таблицы

| Таблица            | Назначение                                         |
|--------------------|----------------------------------------------------|
| `users`            | Пользователи                                       |
| `sessions`         | Активные/отозванные сессии (опаковые токены)       |
| `roles`            | Роли (`admin`, `manager`, `guest`)                 |
| `resources`        | Типы ресурсов системы (`campaigns`, `reports`)     |
| `actions`          | Действия (`read`, `create`, `update`, `delete`)    |
| `permissions`      | Атомарное правило: пара `(resource_id, action_id)` |
| `user_roles`       | Пользователь ↔ роль                                |
| `role_permissions` | Роль ↔ permission                                  |

### Логика проверки доступа

```
user → user_roles → roles → role_permissions → permissions → (resource, action)
```

Конкретный эндпоинт объявляет, какой `(resource_code, action_code)` ему нужен,
например `require_permission("campaigns", "delete")`. Dependency собирает все
permissions всех ролей пользователя и проверяет наличие нужной пары.

- Нет валидного токена → **401**.
- Токен валиден, но нет нужного `(resource, action)` среди permissions
  пользователя → **403 Forbidden**.
- Нужная пара есть → ресурс отдаётся.

## Тестовые данные

Заполняются скриптом `src/scripts/seed.py`:

- Роли: `admin`, `manager`, `guest`
- Ресурсы: `campaigns`, `reports`
- Действия: `read`, `create`, `update`, `delete`
- Permissions: все комбинации resource × action
- `admin` — все permissions
- `manager` — `read`/`create`/`update` на `campaigns`, `read` на `reports`
- `viewer` — только `read` на оба ресурса
- 3 тестовых пользователя, по одному на каждую роль

## API управления правами (только роль `admin`, ресурс `rbac`, действие `manage`)

- `GET /api/v1/admin/rbac/roles` / `POST /api/v1/admin/rbac/roles` / `DELETE /api/v1/admin/rbac/roles/{role_id}`
- `GET /api/v1/admin/rbac/permissions` / `POST /api/v1/admin/rbac/permissions` / `DELETE .../{permission_id}`
- `POST /api/v1/admin/rbac/roles/{role_id}/permissions/{permission_id}` — назначить permission роли
- `DELETE /api/v1/admin/rbac/roles/{role_id}/permissions/{permission_id}` — снять

## Управление профилем

- `PATCH /api/v1/users/me` — обновление last_name/first_name/middle_name
- `DELETE /api/v1/users/me` — soft delete: `is_active=False`, отзыв всех сессий, логин невозможен

## Mock-объекты бизнес-приложения

`GET /api/v1/campaigns` — `require_permission("campaigns", "read")`
`GET /api/v1/reports` — `require_permission("reports", "read")`

Реальных таблиц под эти объекты нет — данные захардкожены в коде эндпоинта,
проверка прав идёт по той же схеме, что и для остальной системы.

## Запуск в Docker


**Команда для запуска:**
```bash
docker compose up --build -d
```

После этого:
- API будет доступно по адресу: `http://localhost:8000`
- Интерактивная документация Swagger: `http://localhost:8000/docs`
- Логи контейнеров можно посмотреть через `docker compose logs -f`
