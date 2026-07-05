from fastapi import APIRouter

from src.api.v1.auth_routes import router as auth_router
from src.api.v1.business_mock_routes import router as business_router
from src.api.v1.rbac_admin_routes import router as rbac_admin_router
from src.api.v1.user_routes import router as user_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(rbac_admin_router)
api_router.include_router(business_router)
