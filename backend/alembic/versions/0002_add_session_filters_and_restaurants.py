"""add session filters and restaurants

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("cuisine", sa.String(length=64), nullable=True))
    op.add_column("sessions", sa.Column("price", sa.String(length=16), nullable=True))
    op.add_column("sessions", sa.Column("radius_meters", sa.Integer(), nullable=True))
    op.add_column("sessions", sa.Column("location_text", sa.String(length=256), nullable=True))

    op.create_table(
        "restaurants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("address", sa.String(length=512), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("price", sa.String(length=16), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("source_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "external_id", name="uq_restaurants_session_external_id"),
    )
    op.create_index(op.f("ix_restaurants_session_id"), "restaurants", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_restaurants_session_id"), table_name="restaurants")
    op.drop_table("restaurants")
    op.drop_column("sessions", "location_text")
    op.drop_column("sessions", "radius_meters")
    op.drop_column("sessions", "price")
    op.drop_column("sessions", "cuisine")
