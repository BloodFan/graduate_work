import os

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.environ.get("POSTGRES_DB"),
#         "USER": os.environ.get("POSTGRES_USER"),
#         "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
#         "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
#         "PORT": os.environ.get("POSTGRES_PORT", 5432),
#     }
# }
DATABASES = {
    "default": {  # Для модели User и Django-админки
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_ADMIN_DB"),
        "USER": os.environ.get("POSTGRES_ADMIN_USER"),
        "PASSWORD": os.environ.get("POSTGRES_ADMIN_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_ADMIN_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_ADMIN_PORT", 5432),
    },
    "profiles_db": {  # Для модели Profile
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", 5432),
    },
}
