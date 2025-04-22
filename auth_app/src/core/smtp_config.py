from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class SmtpConfig(BaseSettings):
    email_host: str
    email_port: int
    email_use_tls: bool
    email_use_ssl: bool
    default_from_email: str

    model_config = ConfigDict(  # type: ignore
        env_prefix="SMTP_",
        envenv_file=".smtp.env",
    )


smtp_data = SmtpConfig()  # type: ignore
