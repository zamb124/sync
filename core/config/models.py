"""Базовые модели конфигурации для проекта sync.

Все значения, критичные для работы сервиса (URL баз данных, брокера и т.п.),
должны приходить из конфигов или окружения. Код не подставляет «разумные»
значения по умолчанию.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Конфигурация HTTP‑сервера FastAPI."""

    host: str = Field(description="Хост для прослушивания HTTP‑сервера.")
    port: int = Field(description="Порт для HTTP‑сервера.")
    debug: bool = Field(description="Режим отладки FastAPI/uvicorn.")
    name: str = Field(description="Логическое имя сервиса.")
    cors_origins: list[str] = Field(
        description="Список разрешённых CORS‑источников."
    )
    default_tenant_id: str = Field(
        description="Tenant ID по умолчанию для изоляции данных."
    )


class TasksConfig(BaseModel):
    """Конфигурация TaskIQ (брокер и бэкенд результатов)."""

    broker_url: str = Field(description="DSN брокера задач (Redis).")
    result_backend: str = Field(description="DSN бэкенда результатов (Redis).")
    default_task_timeout: float = Field(
        default=300.0,
        description="Таймаут выполнения таски в секундах.",
    )
    max_state_size_bytes: int = Field(
        default=10 * 1024 * 1024,
        description="Максимальный размер сериализованного состояния в байтах.",
    )
    max_messages_count: int = Field(
        default=1000,
        description="Максимальное количество сообщений в ExecutionState.messages.",
    )


class AuthConfig(BaseModel):
    """Конфигурация авторизации и permissions."""

    jwt_secret: str = Field(
        description="Секретный ключ для подписи JWT (обязателен)."
    )
    jwt_algorithm: str = Field(
        description="Алгоритм подписи JWT, например HS256."
    )
    access_token_expire_minutes: int = Field(
        default=420,
        description="Время жизни access‑токена в минутах.",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Время жизни refresh‑токена в днях.",
    )
    permissions_enabled: bool = Field(
        default=True,
        description="Включена ли проверка permissions (RBAC).",
    )
    cache_key_prefix: str = Field(
        default="token:auth:",
        description="Префикс ключей токенов в кэше.",
    )
    cache_session_key_prefix: str = Field(
        default="session:auth:",
        description="Префикс ключей сессионных данных в кэше.",
    )
    admin_api_key: Optional[str] = Field(
        default=None,
        description="API‑ключ для административных эндпоинтов.",
    )
    session_secret: Optional[str] = Field(
        default=None,
        description="Секрет для подписи сессионных данных (OAuth, cookie).",
    )


class LoggingConfig(BaseModel):
    """Конфигурация логирования сервиса."""

    level: str = Field(description="Уровень логирования, например INFO или DEBUG.")
    log_dir: str = Field(description="Директория для файлов логов.")
    max_bytes: int = Field(
        description="Максимальный размер файла лога в байтах."
    )
    backup_count: int = Field(
        description="Количество резервных файлов логов."
    )
    truncate_limit: int = Field(
        description="Лимит символов для усечения длинных сообщений в логах."
    )


class TracingConfig(BaseModel):
    """Конфигурация OpenTelemetry‑трейсинга."""

    enabled: bool = Field(
        default=False,
        description="Включён ли трейсинг.",
    )
    postgres_enabled: bool = Field(
        default=False,
        description="Сохранять ли spans в PostgreSQL.",
    )
    tempo_enabled: bool = Field(
        default=False,
        description="Отправлять ли spans в OTLP‑совместимый бекенд (например, Tempo).",
    )
    tempo_endpoint: str = Field(
        description="OTLP endpoint для приёма трейсинга.",
    )
    sampling_rate: float = Field(
        default=1.0,
        description="Доля запросов, для которых собираются трейс‑данные (0.0–1.0).",
    )
    service_name: str = Field(
        description="Имя сервиса, под которым он виден в системе трейсинга.",
    )
    retention_days: int = Field(
        default=30,
        description="Сколько дней хранить трейс‑данные во внутреннем хранилище.",
    )
    max_attributes_per_span: int = Field(
        default=128,
        description="Максимальное количество атрибутов на span.",
    )
    max_events_per_span: int = Field(
        default=128,
        description="Максимальное количество событий на span.",
    )
    trace_state_snapshots: bool = Field(
        default=True,
        description="Записывать ли snapshot состояния для отладки.",
    )
    trace_llm_response: bool = Field(
        default=True,
        description="Логировать ли агрегированную информацию об ответах LLM.",
    )
    log_text_snippets: bool = Field(
        default=True,
        description="Разрешено ли логировать текстовые срезы запросов и ответов.",
    )

