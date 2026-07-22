import os
import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    APP_TITLE: str = "Warehouse Inventory Manager"

    model_config = {"extra": "ignore"}


settings = Settings()
