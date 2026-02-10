from pydantic import computed_field, BaseModel
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv


load_dotenv()


class Conf(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


class AppConfig(Conf):
    IS_PROD: bool


class CORSConfig(Conf):
    CORS_ORIGINS: list[str]
    CORS_METHODS: list[str]
    CORS_HEADERS: list[str]


class UrlsConfig(Conf):
    NGINX_URL: str = "http://nginx_gateway"


class PostgresConfig(Conf):
    DB_ORDER_SERVICE_HOST: str
    DB_ORDER_SERVICE_PORT: int
    DB_ORDER_SERVICE_NAME: str
    DB_ORDER_SERVICE_USER: str
    DB_ORDER_SERVICE_PASSWORD: str
    ECHO: bool

    @computed_field
    @property
    def POSTGRES_URL_ASYNC(self) -> MultiHostUrl:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.DB_ORDER_SERVICE_USER,
            password=self.DB_ORDER_SERVICE_PASSWORD,
            host=self.DB_ORDER_SERVICE_HOST,
            port=self.DB_ORDER_SERVICE_PORT,
            path=self.DB_ORDER_SERVICE_NAME,
        )


class RabbitConfig(Conf):
    PRODUCTS_ROUTING_KEY: str = "products-queue"
    PRODUCTS_EXCHANGE: str = "products-exchange"
    RABBITMQ_URL: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    app: AppConfig = AppConfig()
    cors: CORSConfig = CORSConfig()
    urls: UrlsConfig = UrlsConfig()
    pg_database: PostgresConfig = PostgresConfig()
    rabbitmq: RabbitConfig = RabbitConfig()


settings = Settings()
