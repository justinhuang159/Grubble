"""add yelp query cache

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "yelp_query_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("query_key", sa.String(length=512), nullable=False),
        sa.Column("term", sa.String(length=64), nullable=False),
        sa.Column("location_text", sa.String(length=256), nullable=False),
        sa.Column("price", sa.String(length=16), nullable=True),
        sa.Column("radius_meters", sa.Integer(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_yelp_query_cache_query_key"), "yelp_query_cache", ["query_key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_yelp_query_cache_query_key"), table_name="yelp_query_cache")
    op.drop_table("yelp_query_cache")
