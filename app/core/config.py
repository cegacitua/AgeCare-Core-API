from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AgeCare Core API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    SECRET_KEY: str = Field(default="super-secret-key-change-in-production-agecare-2026", validation_alias="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./agecare.db",
        validation_alias="DATABASE_URL"
    )

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Azure Services (Mocks / Config)
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(default=None, validation_alias="AZURE_STORAGE_CONNECTION_STRING")
    AZURE_CONTAINER_NAME: str = "agecare-documents"

    # Alloxentric Integration
    ALLOXENTRIC_API_KEY: Optional[str] = Field(default="alloxentric-mock-key-2026", validation_alias="ALLOXENTRIC_API_KEY")
    ALLOXENTRIC_BASE_URL: str = Field(default="https://api.alloxentric.com/v1", validation_alias="ALLOXENTRIC_BASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
