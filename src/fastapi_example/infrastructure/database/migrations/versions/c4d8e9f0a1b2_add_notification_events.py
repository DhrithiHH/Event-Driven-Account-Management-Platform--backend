"""Add notification events

Revision ID: c4d8e9f0a1b2
Revises: a7c2f19ca06c
Create Date: 2026-10-08 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "a7c2f19ca06c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

event_type = sa.Enum(
    "ACCOUNT_CREATED",
    "ACCOUNT_UPDATED",
    "ACCOUNT_DELETED",
    name="notification_event_type",
)
event_status = sa.Enum(
    "PENDING",
    "PROCESSING",
    "SENT",
    "FAILED",
    name="notification_event_status",
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notification_events",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("recipient", sa.String(length=250), nullable=False),
        sa.Column("status", event_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_events_id", "notification_events", ["id"])
    op.create_index("ix_notification_events_user_id", "notification_events", ["user_id"])
    op.create_index(
        "ix_notification_events_created_at", "notification_events", ["created_at"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_notification_events_created_at", table_name="notification_events")
    op.drop_index("ix_notification_events_user_id", table_name="notification_events")
    op.drop_index("ix_notification_events_id", table_name="notification_events")
    op.drop_table("notification_events")
    event_status.drop(op.get_bind(), checkfirst=True)
    event_type.drop(op.get_bind(), checkfirst=True)
