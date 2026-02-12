"""add votes table

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "votes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("participant_name", sa.String(length=64), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "participant_name",
            "restaurant_id",
            name="uq_votes_session_participant_restaurant",
        ),
    )
    op.create_index(op.f("ix_votes_session_id"), "votes", ["session_id"], unique=False)
    op.create_index(op.f("ix_votes_restaurant_id"), "votes", ["restaurant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_votes_restaurant_id"), table_name="votes")
    op.drop_index(op.f("ix_votes_session_id"), table_name="votes")
    op.drop_table("votes")
