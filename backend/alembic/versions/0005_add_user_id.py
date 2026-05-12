"""add user id to sessions and participants

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("owner_user_id", sa.String(36), nullable=True))
    op.add_column("participants", sa.Column("user_id", sa.String(36), nullable=True))
    op.create_index("ix_sessions_owner_user_id", "sessions", ["owner_user_id"])
    op.create_index("ix_participants_user_id", "participants", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_participants_user_id", table_name="participants")
    op.drop_index("ix_sessions_owner_user_id", table_name="sessions")
    op.drop_column("participants", "user_id")
    op.drop_column("sessions", "owner_user_id")
