import base64
import binascii
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http import HTTPStatus

import aiosmtplib
from fastapi import HTTPException, Response
from itsdangerous import TimestampSigner
from itsdangerous.exc import BadSignature, SignatureExpired

from auth_app.src.core.config import app_config
from auth_app.src.core.smtp_config import smtp_data


async def send_email(subject, recipient, body):
    """метод для отправки писем(SMTP)"""
    message = MIMEMultipart()
    message["From"] = smtp_data.default_from_email
    message["To"] = recipient
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    await aiosmtplib.send(
        message,
        hostname=smtp_data.email_host,
        port=smtp_data.email_port,
        use_tls=smtp_data.email_use_tls,
        start_tls=smtp_data.email_use_ssl,
    )


async def encode_id(id: str):
    """Кодирует переданную строку(как правило - id)"""
    secret_key = app_config.secret_key
    signer = TimestampSigner(secret_key)
    signed_user_id = signer.sign(id)
    encoded = base64.urlsafe_b64encode(signed_user_id).decode("utf-8")
    return encoded.rstrip("=")


async def decode_id(key: str, max_age: int | None = None):
    """Декодирует переданную строку(как правило - id)"""
    secret_key = app_config.secret_key
    max_age = max_age or app_config.service_token_max_age
    signer = TimestampSigner(secret_key)
    try:
        padding_needed = 4 - (len(key) % 4)
        if padding_needed:
            key += "=" * padding_needed
        key = base64.urlsafe_b64decode(key.encode("utf-8"))  # type: ignore
        return signer.unsign(key, max_age=max_age).decode("utf-8")
    except binascii.Error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Invalid base64 encoding.",
        )
    except SignatureExpired:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Signature has expired."
        )
    except BadSignature:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Invalid signature."
        )


async def set_cookie(response: Response, access: str, refresh: str) -> dict:
    """Устанавливает в Cookie пару jwt токенов."""
    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        samesite="Lax",  # type: ignore
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        samesite="Lax",  # type: ignore
    )
    # нужно чтобы эндпоит возвращал токены
    return {"access_token": access, "refresh_token": refresh}
