from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENCRYPTION_KEY: str  # must match EXPO_PUBLIC_ENCRYPTION_KEY in mobile .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
