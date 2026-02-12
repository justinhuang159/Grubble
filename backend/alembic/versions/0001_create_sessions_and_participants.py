"""create sessions and participants

Revision ID: 0001
Revises:
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("room_code", sa.String(length=8), nullable=False),
        sa.Column("host_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sessions_room_code"), "sessions", ["room_code"], unique=True)

    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_name", sa.String(length=64), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "user_name", name="uq_participants_session_user_name"),
    )
    op.create_index(op.f("ix_participants_session_id"), "participants", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_participants_session_id"), table_name="participants")
    op.drop_table("participants")
    op.drop_index(op.f("ix_sessions_room_code"), table_name="sessions")
    op.drop_table("sessions")
