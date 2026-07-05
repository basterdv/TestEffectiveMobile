from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Класс конфигурации приложения, управляющий переменными окружения."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    session_ttl_seconds: int = 60 * 60 * 24  # 24 часа


settings = Settings()
