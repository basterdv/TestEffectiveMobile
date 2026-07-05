from fastapi import FastAPI

from src.api.router import api_router
from src.core.lifespan import lifespan

app = FastAPI(
    title="Сервис аутентификации и управления доступом на основе ролей",
    lifespan=lifespan,
)
app.include_router(api_router)
