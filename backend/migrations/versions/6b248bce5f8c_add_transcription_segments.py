"""add transcription segments

Revision ID: 6b248bce5f8c
Revises: df355a877f46
Create Date: 2026-09-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6b248bce5f8c"
down_revision: Union[str, Sequence[str], None] = "df355a877f46"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("transcriptions", sa.Column("segments", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("transcriptions", "segments")
