from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SUPABASE_CHAT_TABLES = [
    "delivery_records",
    "disputes",
    "invoices",
    "onboarding_docs",
    "rfps",
    "supplier_admin_reviews",
    "suppliers",
    "support_tickets",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SCM Delivery Mismatch API"
    app_env: str = Field(default="development", alias="APP_ENV")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        alias="CORS_ORIGINS",
    )
    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_key: str = Field(alias="SUPABASE_KEY")
    supabase_chat_tables: list[str] = Field(
        default_factory=lambda: DEFAULT_SUPABASE_CHAT_TABLES.copy(),
        alias="SUPABASE_CHAT_TABLES",
    )
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
