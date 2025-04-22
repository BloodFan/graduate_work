from .settings import *
from .settings import INSTALLED_APPS, INTERNAL_IPS, MIDDLEWARE

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
]
CORS_ORIGIN_ALLOW_ALL = True

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS += [
    "127.0.0.1",
]
