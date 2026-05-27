from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NutriScan AI Backend"
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
