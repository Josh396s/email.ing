# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database and Security
    DB_URL: str 
    JWT_SECRET_KEY: str 
    ENCRYPTION_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRATION_MINUTES: int = 60 * 24 * 7
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str 
    GOOGLE_CLIENT_SECRET: str 
    GOOGLE_REDIRECT_URI: str 
    GOOGLE_METADATA_URL: str = "https://accounts.google.com/.well-known/openid-configuration"
    SCOPES: str

    # Gemini API Key
    GEMINI_API_KEY: str 

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()