"""Configuración del orquestador: URLs de los microservicios que coordina."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "orquestador-service"
    app_version: str = "0.1.0"
    debug: bool = False

    # URLs de los microservicios coordinados (se sobreescriben con env vars en Docker)
    documentos_url: str = "http://localhost:8001"
    extraccion_url: str = "http://localhost:8002"
    resumen_url: str = "http://localhost:8003"
    notificaciones_url: str = "http://localhost:8004"

    resumen_max_words: int = 150

    # Redis (cache de resultados de la Saga)
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600
    cache_enabled: bool = True
    http_timeout_seconds: float = 120.0
    api_v1_prefix: str = "/api/v1"


settings = Settings()
