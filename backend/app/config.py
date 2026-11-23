from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno o de backend/.env (nunca en el repo)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Automotive Membership Platform"
    environment: str = "development"
    database_url: str  # obligatorio, sin valor por defecto: no hay credenciales en el código
    cors_origins: str = "http://localhost:8080,http://localhost:5000"
    timezone: str = "America/Chihuahua"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
