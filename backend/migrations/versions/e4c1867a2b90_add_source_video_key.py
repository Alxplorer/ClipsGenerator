"""add optional R2 key for original videos

Revision ID: e4c1867a2b90
Revises: c820d74a91bf
"""
from alembic import op
import sqlalchemy as sa


revision = "e4c1867a2b90"
down_revision = "c820d74a91bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("source_video_key", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "source_video_key")
