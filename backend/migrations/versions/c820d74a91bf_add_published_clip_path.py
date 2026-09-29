"""add published clip path

Revision ID: c820d74a91bf
Revises: a749d20b31ef
"""
from alembic import op
import sqlalchemy as sa

revision = "c820d74a91bf"
down_revision = "a749d20b31ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clips", sa.Column("rendered_video_path", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("clips", "rendered_video_path")
