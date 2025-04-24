import json
import logging

import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.conf import settings

User = get_user_model()
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        auth_url = settings.AUTH_URL
        url = auth_url + "api/v1/auth/login"
        payload = {"login": username, "password": password}
        response = requests.post(url, data=json.dumps(payload))
        data = response.json()
        try:
            user, created = User.objects.get_or_create(
                email=data["user"]["email"],
                defaults={
                    "email": data["user"]["email"],
                    "login": data["user"]["login"],
                    "username": data["user"]["login"],
                    "first_name": data["user"]["first_name"],
                    "last_name": data["user"]["last_name"],
                    "is_active": data["user"]["is_active"],
                    "is_admin": "admin" in data["user"]["roles"],
                    "is_staff": "admin" in data["user"]["roles"],
                    "is_superuser": "admin" in data["user"]["roles"],
                },
            )
            if not created:
                user.login = data["user"]["login"]
                user.username = data["user"]["login"]
                user.first_name = data["user"]["first_name"]
                user.last_name = data["user"]["last_name"]
                user.is_active = data["user"]["is_active"]
                user.is_admin = "admin" in data["user"]["roles"]
                user.is_staff = "admin" in data["user"]["roles"]
                user.is_superuser = "admin" in data["user"]["roles"]
                user.set_password(password)
                user.save()
        except Exception:
            return None
        return user

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return user
        except User.DoesNotExist:
            return None
