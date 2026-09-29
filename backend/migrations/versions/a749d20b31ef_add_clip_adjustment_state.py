"""add clip adjustment state

Revision ID: a749d20b31ef
Revises: 83edb3e589ef
"""
from alembic import op
import sqlalchemy as sa

revision = "a749d20b31ef"
down_revision = "83edb3e589ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clips", sa.Column("adjustment_id", sa.String(36), nullable=True))
    op.add_column("clips", sa.Column("adjustment_status", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("clips", "adjustment_status")
    op.drop_column("clips", "adjustment_id")
