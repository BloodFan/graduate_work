import base64
import binascii
from http import HTTPStatus
from http.client import HTTPException

from django.conf import settings
from itsdangerous import TimestampSigner
from itsdangerous.exc import BadSignature, SignatureExpired


async def encode_id(id: str):
    """Кодирует переданную строку(как правило - id)"""
    secret_key = settings.SECRET_KEY
    signer = TimestampSigner(secret_key)
    signed_user_id = signer.sign(id)
    encoded = base64.urlsafe_b64encode(signed_user_id).decode("utf-8")
    return encoded.rstrip("=")


async def decode_id(key: str, max_age: int | None = None):
    """Декодирует переданную строку(как правило - id)"""
    secret_key = settings.SECRET_KEY
    max_age = max_age or settings.SERVICE_TOKEN_MAX_AGE
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
