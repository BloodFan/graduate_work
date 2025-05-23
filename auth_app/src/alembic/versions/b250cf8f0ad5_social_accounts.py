"""social_accounts

Revision ID: b250cf8f0ad5
Revises: bcc4465775ce
Create Date: 2024-11-29 14:44:31.624525

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b250cf8f0ad5"
down_revision: Union[str, None] = "bcc4465775ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "social_accounts",
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_user_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint(
            "provider", "provider_user_id", name="uq_provider_provider_user_id"
        ),
    )
    op.create_index(
        op.f("ix_social_accounts_provider"),
        "social_accounts",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_social_accounts_provider_user_id"),
        "social_accounts",
        ["provider_user_id"],
        unique=False,
    )
    op.create_unique_constraint(None, "refresh_tokens", ["id"])
    op.create_unique_constraint(None, "sessions", ["id"])
    op.create_unique_constraint(None, "users", ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "users", type_="unique")  # type: ignore
    op.drop_constraint(None, "sessions", type_="unique")  # type: ignore
    op.drop_constraint(None, "refresh_tokens", type_="unique")  # type: ignore
    op.drop_index(
        op.f("ix_social_accounts_provider_user_id"),
        table_name="social_accounts",
    )
    op.drop_index(
        op.f("ix_social_accounts_provider"), table_name="social_accounts"
    )
    op.drop_table("social_accounts")
    # ### end Alembic commands ###
