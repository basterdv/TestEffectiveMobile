from fastapi import APIRouter, Depends

from src.api.deps import require_permission

router = APIRouter(
    prefix="/business",
    tags=["Имитация бизнес-логики"],
)

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
    "/campaigns", dependencies=[Depends(require_permission("campaigns", "read"))]
)
def list_campaigns() -> list[dict]:
    """Возвращаем список всех маркетинговых кампаний компании."""
    return _MOCK_CAMPAIGNS


@router.get("/reports", dependencies=[Depends(require_permission("reports", "read"))])
def list_reports() -> list[dict]:
    """Возвращаем список аналитических отчетов компании."""
    return _MOCK_REPORTS
