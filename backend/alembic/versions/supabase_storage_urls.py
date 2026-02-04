"""Rename path columns to URL columns for Supabase storage

Revision ID: supabase_storage_urls
Revises: e6cae3da83b4
Create Date: 2026-02-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'supabase_storage_urls'
down_revision = 'e6cae3da83b4'
branch_labels = None
depends_on = None


def upgrade():
    # Rename columns to reflect URL storage instead of local paths
    op.alter_column('comics', 'pdf_path', new_column_name='pdf_url')
    op.alter_column('comics', 'cover_image_path', new_column_name='cover_image_url')


def downgrade():
    # Revert column names back to path-based naming
    op.alter_column('comics', 'pdf_url', new_column_name='pdf_path')
    op.alter_column('comics', 'cover_image_url', new_column_name='cover_image_path')
