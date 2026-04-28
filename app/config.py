from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Railway will inject these; Pydantic will read them from the environment
    DATABASE_URL: str
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "production"

    # Modern Pydantic 2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",      # Vital: ignores variables not defined here
        case_sensitive=True  # Matches UPPERCASE Railway variables
    )

settings = Settings()
