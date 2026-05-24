from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    weather_api_key: str
    db_dns: str
    local_migration_db_dns: str 

    model_config = SettingsConfigDict(
        env_file="app/.env",
        env_file_encoding="utf-8"
    )

settings = Settings()