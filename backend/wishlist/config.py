from functools import lru_cache
from pathlib import Path
from pydantic import  Field
from pydantic_settings import BaseSettings, SettingsConfigDict


base_dir = Path(__file__).resolve().parent.parent
env_path = base_dir.parent / '.env'

class Settings(BaseSettings):
    db_name: str = Field(alias='DB_NAME')
    db_user: str = Field(alias='DB_USER')
    db_password: str = Field(alias='DB_PASSWORD')
    db_host: str = Field(alias='DB_HOST')
    db_port: int = Field(alias='DB_PORT')
    model_config = SettingsConfigDict(env_file=env_path,extra='ignore')

@lru_cache
def get_settings() -> Settings:
    return Settings()

