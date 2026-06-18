from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=('.env', '../.env'), env_file_encoding='utf8', extra='ignore')
    
    APP_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    SECRET_KEY: str
    SMTP_ADDRESS: str
    SMTP_PASSWORD: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    HOST: str
    PORT: int
    RELOAD: bool
    FRONTEND_HOST: str
    FRONTEND_PORT: int
    ALLOW_ORIGINS: list[str]
    ALLOW_METHODS: list[str]
    ALLOW_HEADERS: list[str]
    ALLOW_CREDENTIALS: bool
    SLUG_LENGTH: int
    ACCESS_TOKEN_EXPIRE_SECONDS: int
    ACCESS_AUTH_TOKEN_EXPIRE_SECONDS: int
    VERSION: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # @property
    # def DATABASE_URL(self) -> str:
    #     return f"sqlite+aiosqlite:///sites.db"
    
    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"


settings = Settings()
