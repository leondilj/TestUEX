"""Configuração da aplicação — lê variáveis de ambiente (pydantic-settings)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings globais. Variáveis de ambiente vencem valores default (case-insensitive)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    db_pool_size: int = 10  # conexões persistentes mantidas abertas no pool, mesmo ociosas
    db_max_overflow: int = 20  # conexões extras acima do pool_size permitidas em pico de carga
    db_pool_timeout: int = 30  # segundos que uma requisição espera por conexão livre antes de falhar
    jwt_secret: str
    jwt_expires_days: int = 7  # sem refresh token — ver ADR-001
    cookie_secure: bool = False  # True em produção (ADR-001)
    cookie_samesite: str = "lax"  # "none" se web e api em domínios diferentes (ADR-001)
    cors_origins: list[str] = ["http://localhost:3000"]

    # Anexos — limites recomendados em spec/data-model.md (open question resolvida lá)
    upload_dir: str = "uploads"
    max_upload_bytes: int = 10 * 1024 * 1024
    allowed_upload_types: list[str] = [
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]

    # Extensão — assistente (ADR-003); vazio desabilita o endpoint de chat
    anthropic_api_key: str = ""
    # Modelo leve/rápido: tools são simples, não exigem raciocínio complexo (ADR-003 — Risks)
    assistant_model: str = "claude-haiku-4-5-20251001"

    # Extensão — observabilidade do assistente via Langfuse self-host (ADR-005);
    # public_key vazio desabilita o tracing automaticamente (client em modo no-op)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://host.docker.internal:3001"
    # Usado só como tag de rastreio no Langfuse ("development"/"staging"/"production")
    app_environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    """Instância única de Settings (cacheada por processo)."""
    return Settings()
