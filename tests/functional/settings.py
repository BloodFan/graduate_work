from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings
from redis.asyncio import Redis
from werkzeug.security import generate_password_hash


class TestSettings(BaseSettings):
    profiles_url: str = Field(default="http://profiles_app:40/")
    service_url: str = Field(default="http://auth_app:80/")
    model_config = ConfigDict(env_file=".tests.env")


class RedisSettings(BaseSettings):
    unix_socket_path: str

    model_config = ConfigDict(
        env_prefix="REDIS_",  # type: ignore
        env_file=".conn.env",  # type: ignore
    )

    def get_conn(self):
        return Redis(unix_socket_path=self.unix_socket_path, db=1)


class SuperUserConfig(BaseSettings):
    login: str = Field(default="admin")
    email: str = Field(default="test1@test.com")
    password: str = Field(default="tester34")

    @property
    def get_hashed_password(self):
        return generate_password_hash(self.password)

    model_config = ConfigDict(  # type: ignore
        env_prefix="SUPERUSER_",
        env_file=".env",
    )


class AuthPsqlConfig(BaseSettings):
    user: str = Field(default="postgres")
    password: str = Field(default="secret")
    db: str = Field(default="postgres")
    host: str = Field(default="auth_db")
    port: int = Field(default=5432)
    min_size: int = Field(default=1)
    max_size: int = Field(default=10)

    @property
    def get_dsn_for_sqlalchemy(self):
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@/{self.db}?host={self.host}"
        )

    @property
    def get_dsn_for_check(self):
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@/{self.db}?host={self.host}"
        )

    model_config = ConfigDict(
        env_prefix="POSTGRES_AUTH_",
        envenv_file=".conn.env",
    )


class ProfilesPsqlConfig(BaseSettings):
    user: str = Field(default="postgres")
    password: str = Field(default="secret")
    db: str = Field(default="postgres")
    host: str = Field(default="/postgres_socket")
    port: int = Field(default=5432)

    @property
    def get_dsn_for_sqlalchemy(self):
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@/{self.db}?host={self.host}"
        )

    @property
    def get_dsn_for_check(self):
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@/{self.db}?host={self.host}"
        )

    model_config = ConfigDict(
        env_prefix="POSTGRES_PROFILES_",
        envenv_file=".profiles.env",
    )


redis_settings = RedisSettings()
test_settings = TestSettings()
superuser_data = SuperUserConfig()
auth_psql_settings = AuthPsqlConfig()
profiles_psql_settings = ProfilesPsqlConfig()
