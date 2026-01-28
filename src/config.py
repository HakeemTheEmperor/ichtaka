from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )
    
    # Database Settings
    DATABASE_URL: str 
    
    # Security Settings
    JWT_SECRET_KEY: str 
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # CORS Settings
    CORS_ORIGINS: list[str] = ["*"]
    
settings = Settings()