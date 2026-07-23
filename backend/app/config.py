"""
Configuración de la app vía variables de entorno (pydantic-settings).

Las credenciales de LinkedIn OAuth ya no viven hardcodeadas en el código:
se leen de variables de entorno (o de un archivo .env en local). Ver
.env.example para la plantilla.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Base de datos. SQLite para dev; en prod usar una URL de Postgres,
    # ej: "postgresql+psycopg://user:pass@host/dbname".
    database_url: str = "sqlite:///./lingraph.db"

    # Clave para firmar la cookie de sesión (necesaria para el flujo OAuth
    # de Authlib). En prod, definir SESSION_SECRET con un valor aleatorio.
    session_secret: str = "dev-insecure-change-me"

    # Credenciales de "Sign in with LinkedIn" (OpenID Connect).
    # Se obtienen creando una app en https://www.linkedin.com/developers/
    linkedin_client_id: str | None = None
    linkedin_client_secret: str | None = None

    @property
    def linkedin_oauth_configured(self) -> bool:
        return bool(self.linkedin_client_id and self.linkedin_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
