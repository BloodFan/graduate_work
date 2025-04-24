import logging
from logging import config as logging_config

from fastapi import HTTPException

from profiles_app.src.core.config import app_config
from profiles_app.src.core.logger import LOGGING
from profiles_app.src.services.api_client import APIClient

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("sms_send_service")

# Эмуляция отправления SMS для верификации моб.телефона профиля.
# т.к. на территории России частное лицо не может отправлять смс сервисом
# так что заглушкой выступает прямой возврат кода в ответе ручки.

# ниже ответ от sms.ru
# {'status': 'OK', 'status_code': 100,
# 'sms': {'+7(924)111-71-79':
# {'status': 'ERROR', 'status_code': 204, 'status_text':
# 'Вы не подключили данного оператора на данном имени
# (а также запасном или имени по умолчанию).
# Подайте заявку через раздел *Отправители* на сайте SMS.RU -
# https://sms.ru/?panel=senders'}}, 'balance': 120}


async def send_sms(phone: str, code: str):
    """Отправка SMS через sms.ru."""
    api_id = app_config.sms_api_id
    base_url = "https://sms.ru/"
    message = f"Код подтверждения: {code}"

    async with APIClient(base_url=base_url, token_manager=None) as client:
        try:
            response = await client.request(
                method="GET",
                endpoint="sms/send",
                params={
                    "api_id": api_id,
                    "to": phone,
                    "msg": message,
                    "json": 1,
                    "test": 1,
                },
            )
            if response.get("status") != "OK":
                error_code = response.get("status_code")
                logger.error(f"SMS error (code {error_code}): {response}")
                raise HTTPException(500, "Ошибка отправки SMS")

        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            raise HTTPException(500, "Ошибка подключения к SMS-сервису")
