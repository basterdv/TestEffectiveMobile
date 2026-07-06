from fastapi import APIRouter, Depends, status

from src.api.deps import require_permission
from src.schemas.auth import ErrorResponse

router = APIRouter(
    prefix="/business",
    tags=["Имитация бизнес-логики"],
)

_errors = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Не авторизован",
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": "Нет доступа к ресурсу",
    },
}

# Демонстрационные (фиктивные) данные для симуляции ответов бизнес-логики.
_MOCK_CAMPAIGNS = [
    {"id": 1, "name": "Летняя распродажа", "budget": 50000},
    {"id": 2, "name": "Запуск нового продукта", "budget": 120000},
]

_MOCK_REPORTS = [
    {"id": 1, "title": "Отчёт за Q1", "status": "ready"},
    {"id": 2, "title": "Отчёт за Q2", "status": "in_progress"},
]


@router.get(
    "/campaigns",
    dependencies=[Depends(require_permission("campaigns", "read"))],
    responses={**_errors},
    summary="Список кампаний",
    description="Требует permission `(campaigns, read)`. Демонстрирует работу 401/403.",
)
async def list_campaigns() -> list[dict]:
    """Возвращаем список всех маркетинговых кампаний компании."""
    return _MOCK_CAMPAIGNS


@router.get(
    "/reports",
    dependencies=[Depends(require_permission("reports", "read"))],
    responses={**_errors},
    summary="Список отчётов",
    description="Требует permission `(reports, read)`.",
)
async def list_reports() -> list[dict]:
    """Возвращаем список аналитических отчетов компании."""
    return _MOCK_REPORTS
