from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./vault.db"
    SECRET_KEY: str = "dev-only-secret-key-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    VAULT_DIR: str = "./vault_data"
    MAX_UPLOAD_SIZE_MB: int = 10
    VAULT_SESSION_TTL_MINUTES: int = 30
    KDF_ITERATIONS: int = 200000


settings = Settings()
