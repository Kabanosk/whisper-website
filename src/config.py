from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or a .env file"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_idle_timeout_seconds: int = 5 * 60


settings = Settings()
