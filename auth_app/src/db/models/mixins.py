import uuid
from datetime import datetime, timezone
from typing import Annotated

from sqlalchemy import DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

int_pk = Annotated[int, mapped_column(Integer, primary_key=True, index=True)]

uuid_pk = Annotated[
    uuid.UUID,
    mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    ),
]

created_at = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    ),
]


class IDMixin:
    id: Mapped[int_pk]


class UUIDMixin:
    id: Mapped[uuid_pk]


class TimeStampedMixin:
    created_at: Mapped[created_at]
