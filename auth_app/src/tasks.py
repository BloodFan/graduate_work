import asyncio
from concurrent.futures import ThreadPoolExecutor

import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker

from auth_app.src.core.config import app_config, rabbitmq_data
from auth_app.src.core.logger import logstash_handler
from auth_app.src.services.api_client import APIClient
from auth_app.src.services.token_manager import TokenManager
from auth_app.src.utils.encoders import UUIDEncoder

logger = logstash_handler()

rabbitmq_broker = RabbitmqBroker(url=rabbitmq_data.broker_url)
dramatiq.set_broker(rabbitmq_broker)
dramatiq.set_encoder(UUIDEncoder())


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        with ThreadPoolExecutor() as executor:
            future = executor.submit(loop.run_until_complete, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)


@dramatiq.actor(
    queue_name="user_profiles",
    max_retries=5,
    min_backoff=1000,
    max_backoff=60000,
)
def create_profile_task(user_data: dict):
    """
    Отправляет POST-запрос в profiles_app для создания профиля пользователя.
    """
    token_manager = TokenManager()
    try:

        async def _create_profile():
            async with APIClient(
                app_config.profile_url, token_manager
            ) as api_client:
                await api_client.request(
                    "POST",
                    app_config.profile_create_url,
                    json={
                        "user_id": str(user_data["id"]),
                        "first_name": user_data["first_name"],
                        "last_name": user_data["last_name"],
                    },
                )

    except Exception as e:
        print(e)
        logger.error(f"Ошибка создания профиля: {e}")

    run_async(_create_profile())
