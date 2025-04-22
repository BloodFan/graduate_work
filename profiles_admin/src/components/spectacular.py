import os

SPECTACULAR_SETTINGS = {
    "TITLE": os.environ.get("PROJECT_NAME", "PROJECT_TITLE"),
    "DESCRIPTION": "API description",
    "VERSION": "1.0.0",
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
    "SERVE_AUTHENTICATION": [
        "rest_framework.authentication.SessionAuthentication"
    ],
    "SWAGGER_UI_SETTINGS": {
        "tryItOutEnabled": True,
        "displayRequestDuration": True,
        "persistAuthorization": True,
        "filter": True,
    },
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "Authorization": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Bearer jwt token",
            },
            "Language": {
                "type": "apiKey",
                "in": "header",
                "name": "Accept-Language",
                "description": "Authorization by Token",
            },
        },
    },
    "SECURITY": [
        {"Authorization": [], "Language": []},
    ],
}
