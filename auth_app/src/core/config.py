import os

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings
from werkzeug.security import generate_password_hash

# from logging import config as logging_config


# from .logger import LOGGING

# logging_config.dictConfig(LOGGING)


class LogstashConfig(BaseSettings):
    host: str = Field(default="logstash")
    port: int = Field(default=5044)
    version: int = Field(default=1)

    model_config = ConfigDict(  # type: ignore
        env_prefix="LOGSTASH_",
        envenv_file=".conn.env",
    )


class HawkConfig(BaseSettings):
    token: str = Field(
        default=(
            "eyJpbnRlZ3JhdGlvbklkIjoiZmJlOGQ4NmMtZjk0My00YmQ5LTg3"
            "MTUtMzM2NWMyMDEzMTMxIiwic2VjcmV0IjoiYWQ3ODVhYWItZjE5"
            "Yy00OTc4LWE4ZTctOGEwM2ZkN2UzZTIzIn0="
        )
    )

    model_config = ConfigDict(  # type: ignore
        env_prefix="HAWK_",
        envenv_file=".conn.env",
    )


class SuperUserConfig(BaseSettings):
    login: str = Field(default="admin")
    email: str = Field(default="test1@test.com")
    password: str = Field(default="tester34")

    @property
    def get_hashed_password(self):
        return generate_password_hash(self.password)

    model_config = ConfigDict(  # type: ignore
        env_prefix="SUPERUSER_",
        envenv_file=".env",
    )


class AppConfig(BaseSettings):
    project_auth_name: str = Field(default="auth_service")
    project_auth_description: str = Field(
        default="API for Movie theater(Auth_app)"
    )
    frontend_auth_url: str = Field(default="http://localhost:8080")
    auth_url: str = Field(default="http://auth_app:80/")
    profile_url: str = Field(default="http://profiles_app:40/")
    profile_create_url: str = Field(default="api/v1/profiles")
    enable_tracer: bool = Field(default=False)
    enable_hawk: bool = Field(default=True)
    jaeger_url: str = Field(default="http://jaeger:14268/")
    secret_key: str = Field(
        description="secret key auth_app for confirm requests"
    )
    allowed_services: list[str] = Field(
        default=[
            "notifications_service",
            "ugc_service",
            "auth_service",
            "profiles_service",
            "profiles_admin_service",
        ]
    )
    cache_expire: int = Field(
        default=60 * 10 * 1,
    )  # 10 минут
    confirmation_expire: int = Field(
        default=60 * 60 * 24 * 30,
    )  # 3 дня
    access_token_expires: int = Field(
        default=60 * 15,
    )  # 15 минут
    refresh_token_expires: int = Field(
        default=60 * 60 * 24 * 30,
    )  # 30 дней
    service_token_max_age: int = 30 * 24 * 3600  # 30 дней в секундах


class ContactConfig(BaseSettings):
    name: str = Field(default="Sergey Kimaikin")
    url: str = Field(default="https://github.com/BloodFan")
    email: str = Field(default="test1@test.com")

    model_config = ConfigDict(envenv_file=".contact.env")  # type: ignore


class RedisData(BaseSettings):
    unix_socket_path: str

    model_config = ConfigDict(  # type: ignore
        env_prefix="REDIS_",
        envenv_file=".conn.env",
    )


class PsqlData(BaseSettings):
    user: str = Field(default="postgres")
    password: str = Field(default="secret")
    db: str = Field(
        default="theatre_auth",
    )
    host: str = Field(default="/")
    port: int = Field(default=5432)
    min_size: int = Field(default=1)
    max_size: int = Field(default=10)

    @property
    def get_dsn(self):
        return (
            f"dbname={self.db} user={self.user} "
            f"password={self.password} host={self.host}"
        )

    @property
    def get_dsn_for_sqlalchemy(self):
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@/{self.db}?host={self.host}"
        )

    @property
    def get_dsn_for_asyncpg(self):
        return (
            f"postgres://{self.user}:{self.password}"
            f"@/{self.db}?host={self.host}"
        )

    model_config = ConfigDict(  # type: ignore
        env_prefix="POSTGRES_AUTH_",
        envenv_file=".conn.env",
    )


class RabbitMQData(BaseSettings):
    broker_url: str = Field(default="amqp://user:password@rabbitmq:5672/%2F")

    model_config = ConfigDict(  # type: ignore
        env_prefix="RABBIT_",
        envenv_file=".conn.env",
    )


psql_data = PsqlData()
redis_data = RedisData()  # type: ignore
app_config = AppConfig()  # type: ignore
contact_config = ContactConfig()
superuser_data = SuperUserConfig()
logstash_data = LogstashConfig()
hawk_data = HawkConfig()
rabbitmq_data = RabbitMQData()

contact_config = {  # type: ignore
    "name": contact_config.name,
    "url": contact_config.url,
    "email": contact_config.email,
}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
