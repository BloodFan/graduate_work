import base64
import os

FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://127.0.0.1:8000/")
AUTH_URL: str = os.environ.get("AUTH_URL", "http://auth_app:80/")
USERS_BULK: str = os.environ.get("USERS_BULK", "api/v1/users/bulk")

HMAC_KEY: str = base64.urlsafe_b64decode(
    os.environ.get("HMAC_KEY", "X7Fq3tRk9vYlLpOzKjWnQrSsUmTdYcA1B2C3D4E5F6G=")
)
ENCRYPTION_KEY: str = os.environ.get(
    "ENCRYPTION_KEY", "mFb4xclONMT0TTIcuAmTQpVNh4ibHyvhSpmHUK-vJrI="
)

PROFILES_ADMIN_NAME: str = os.environ.get(
    "PROFILES_ADMIN_NAME", "profiles_admin_service"
)
SERVICE_TOKEN_MAX_AGE: int = os.environ.get(
    "SERVICE_TOKEN_MAX_AGE", 30 * 24 * 60 * 60
)
SECRET_KEY: str = os.environ.get(
    "SECRET_KEY",
    "fastapi-insecure-b2sh!qk&=%azim-=s&=d1(-1upbq7H&-^-=tmPeHPLKXD",
)
BATCH_SIZE: int = os.environ.get("BATCH_SIZE", 1000)
