import os
from typing import List
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./thermoculture.db"
    SECRET_KEY: str = Field(
        default="change-me-in-production-use-a-long-random-string",
        description="Secret key for JWT encoding",
    )
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Thermoculture Research Assistant"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    # Reddit API
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "ThermocultureResearchBot/1.0 (academic research project)"

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        placeholder_keys = {
            "change-me-in-production-use-a-long-random-string",
            "change-this-to-a-random-secret-key",
        }
        if (
            os.environ.get("THERMOCULTURE_ENV") == "production"
            and self.SECRET_KEY in placeholder_keys
        ):
            raise ValueError(
                "SECRET_KEY cannot be a placeholder value in production environment"
            )
        return self

    model_config = {
        "env_file": (".env", "../.env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
