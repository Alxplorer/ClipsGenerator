"""add optional R2 key for published clips

Revision ID: f28b9d7c4a61
Revises: e4c1867a2b90
"""
from alembic import op
import sqlalchemy as sa


revision = "f28b9d7c4a61"
down_revision = "e4c1867a2b90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clips", sa.Column("rendered_video_key", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("clips", "rendered_video_key")
