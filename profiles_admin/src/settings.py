import os
from pathlib import Path

from split_settings.tools import include

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = int(os.environ.get("DEBUG", 1))

ALLOWED_HOSTS: list = (
    ["*"] if DEBUG else os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
)

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ORIGIN_ALLOW_ALL = True

DATABASE_ROUTERS = [
    "src.routers.UnifiedRouter",
]
INTERNAL_IPS: list[str] = []

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = [
    "users.authentications.CustomBackend",
    # 'django.contrib.auth.backends.ModelBackend',
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rosetta",
    "django_filters",
    "rest_framework",
    "drf_spectacular",
]

LOCAL_APPS = [
    "users.apps.UsersConfig",
    "profiles.apps.ProfilesConfig",
    "favorites.apps.FavoritesConfig",
    "reviews.apps.ReviewsConfig",
]

INSTALLED_APPS += THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

ROOT_URLCONF = "src.urls"

include(
    "components/env_variables.py",
    "components/templates.py",
    "components/database.py",
    "components/auth_password_validators.py",
    "components/debug_toolbar_config.py",
    "components/rest_framework.py",
    "components/spectacular.py",
    "components/logging.py",
)

WSGI_APPLICATION = "src.wsgi.application"
ASGI_APPLICATION = "src.asgi.application"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

LANGUAGES = (
    ("en", "English"),
    ("ru", "Russian"),
)

ROSETTA_SHOW_AT_ADMIN_PANEL = DEBUG

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")


MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
