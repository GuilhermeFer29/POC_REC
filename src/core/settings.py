from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "POC Receitas"
    mysql_url: str = "mysql+mysqlconnector://receitas:receitas@mysql:3306/receitas"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    env: str = "dev"

    gemini_api_key: str | None = None
    gemini_model_text: str = "gemini-2.5-flash"
    gemini_model_embed: str = "gemini-embedding-001"

    agno_telemetry: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
