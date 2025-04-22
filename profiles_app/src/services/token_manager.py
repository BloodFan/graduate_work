from datetime import datetime

from profiles_app.src.core.config import app_config
from profiles_app.src.utils.utils import encode_id


class TokenManager:
    def __init__(
        self,
        service_id: str = app_config.project_profiles_name,
        max_age: int = app_config.service_token_max_age,
        buffer_seconds: int = 60 * 60,
    ):
        self.service_id = service_id
        self.max_age = max_age
        self.buffer_seconds = buffer_seconds
        self.token = None
        self.generated_at = None

    async def get_token(self) -> str:
        if self._is_expired():
            self.token = await encode_id(self.service_id)
            self.generated_at = datetime.now()
        return self.token

    def _is_expired(self) -> bool:
        if not self.generated_at:
            return True
        elapsed = (datetime.now() - self.generated_at).total_seconds()
        return elapsed > (self.max_age - self.buffer_seconds)

    async def get_auth_headers(self) -> dict:
        if self._is_expired():
            await self.get_token()
        return {"X-Service-Token": self.token}


async def get_token_manager(
    service_id: str = app_config.project_profiles_name,
    max_age: int = app_config.service_token_max_age,
    buffer_seconds: int = 60 * 60,
) -> TokenManager:
    return TokenManager(
        service_id=service_id, max_age=max_age, buffer_seconds=buffer_seconds
    )
