from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "POC Receitas"
    mysql_url: str = "mysql+mysqlconnector://receitas:receitas@mysql:3306/receitas"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    env: str = "dev"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
