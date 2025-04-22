from authlib.integrations.starlette_client import OAuth  # type: ignore
from pydantic import Field
from pydantic_settings import BaseSettings


class YandexConfig(BaseSettings):
    client_id: str = Field(default="eed88c0527124b39a54fe797c3d1a072")
    client_secret: str = Field(default="868efdba6d874c148b4a129b6d0c15f6")
    c_id: str = Field(default="qbb32nmw0gv433d73u27rd6ebm")
    redirect_url: str = Field(
        default="http://localhost:8080/api/v1/auth/callback"
    )
    authorize_url: str = Field(default="https://oauth.yandex.ru/authorize")
    token_url: str = Field(default="https://oauth.yandex.ru/token")
    user_info_url: str = Field(default="https://login.yandex.ru/info")


class GoogleConfig(BaseSettings):
    client_id: str = Field(
        default="959459518678-bh1h637643gui9q1tgjn1ntkb36bcrm8.apps.googleusercontent.com"
    )
    client_secret: str = Field(default="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")
    # c_id: str = Field(default="qbb32nmw0gv433d73u27rd6ebm")
    redirect_url: str = Field(
        default="http://localhost:8080/api/v1/auth/callback"
    )
    authorize_url: str = Field(
        default="https://accounts.google.com/o/oauth2/auth"
    )
    token_url: str = Field(default="https://oauth2.googleapis.com/token")
    user_info_url: str = Field(
        default="https://www.googleapis.com/oauth2/v1/userinfo"
    )


yandex_data = YandexConfig()
google_data = GoogleConfig()

oauth = OAuth()

yandex = oauth.register(
    name="yandex",
    client_id=yandex_data.client_id,
    client_secret=yandex_data.client_secret,
    access_token_url=yandex_data.token_url,
    authorize_url=yandex_data.authorize_url,
    userinfo_endpoint=yandex_data.user_info_url,
    client_kwargs={
        "scope": "login:info",
    },
)

google = oauth.register(
    name="google",
    client_id=google_data.client_id,
    client_secret=google_data.client_secret,
    access_token_url=google_data.token_url,
    authorize_url=google_data.authorize_url,
    userinfo_endpoint=google_data.user_info_url,
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    client_kwargs={
        "scope": "openid email profile",
    },
)
