"""initial tables

Revision ID: a0000000001
Revises: 
Create Date: 2026-02-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0000000001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    # Create comics table with genre (singular) initially
    op.create_table('comics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('genre', sa.String(), nullable=True),
    sa.Column('pdf_path', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comics_id'), 'comics', ['id'], unique=False)
    op.create_index(op.f('ix_comics_title'), 'comics', ['title'], unique=False)
    op.create_index(op.f('ix_comics_genre'), 'comics', ['genre'], unique=False)


def downgrade() -> None:
    """Drop initial tables."""
    op.drop_index(op.f('ix_comics_genre'), table_name='comics')
    op.drop_index(op.f('ix_comics_title'), table_name='comics')
    op.drop_index(op.f('ix_comics_id'), table_name='comics')
    op.drop_table('comics')
