import base64

from cryptography.fernet import InvalidToken
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    project_profiles_name: str = Field(default="profiles_service")
    project_profiles_description: str = Field(
        default="API for Movie theater(profiles_app)"
    )
    secret_key: str = Field(
        description="secret key auth_app for confirm requests"
    )
    allowed_services: list[str] = Field(
        default=["profiles_service", "ugc_service", "auth_service"]
    )
    auth_url: str = Field(default="http://auth_app:80/")
    content_url: str = Field(default="http://content_app:60/")
    service_token_max_age: int = 30 * 24 * 60 * 60  # 30 дней в секундах
    encryption_key: str = Field(
        default="mFb4xclONMT0TTIcuAmTQpVNh4ibHyvhSpmHUK-vJrI="
    )
    hmac_key: str = Field(
        default="X7Fq3tRk9vYlLpOzKjWnQrSsUmTdYcA1B2C3D4E5F6G="
    )
    sms_api_id: str = Field(default="EE623E83-BB20-09EB-5400-0AFE632BB520")

    @property
    def validated_encryption_key(self) -> bytes:
        try:
            key = base64.urlsafe_b64decode(self.encryption_key.encode())
            if len(key) != 32:
                raise ValueError("Encryption key must be 32 bytes!")
            return key
        except (ValueError, InvalidToken) as e:
            raise ValueError(f"Invalid Fernet encryption key: {e}")


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


class RabbitMQData(BaseSettings):
    broker_url: str = Field(default="amqp://user:password@rabbitmq:5672/%2F")

    model_config = ConfigDict(  # type: ignore
        env_prefix="REDIS_",
        envenv_file=".conn.env",
    )


class PsqlData(BaseSettings):
    user: str = Field(default="postgres")
    password: str = Field(default="secret")
    db: str = Field(
        default="postgres",
        description="movie_profiles",
    )
    host: str = Field(default="/postgres_socket")
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

    model_config = ConfigDict(
        env_prefix="POSTGRES_PROFILES",
        envenv_file=".conn.env",
    )


class LogstashConfig(BaseSettings):
    host: str = Field(default="logstash")
    port: int = Field(default=5044)
    version: int = Field(default=1)

    model_config = ConfigDict(  # type: ignore
        env_prefix="LOGSTASH_",
        envenv_file=".conn.env",
    )


logstash_data = LogstashConfig()
psql_data = PsqlData()
redis_data = RedisData()  # type: ignore
rabbitmq_data = RabbitMQData()
app_config = AppConfig()  # type: ignore
contact_config = ContactConfig()
