"""migrate_pdf_to_images

Revision ID: 33d952a74f07
Revises: 2b38fe32d451
Create Date: 2026-02-10 13:01:29.554736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33d952a74f07'
down_revision: Union[str, Sequence[str], None] = '2b38fe32d451'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Replace pdf_url with image_urls."""
    # Add the new image_urls column as JSONB
    op.add_column('chapters', sa.Column('image_urls', sa.dialects.postgresql.JSONB(), nullable=True))
    
    # Set default empty array for existing rows
    op.execute("UPDATE chapters SET image_urls = '[]'::jsonb WHERE image_urls IS NULL")
    
    # Drop the old pdf_url column
    op.drop_column('chapters', 'pdf_url')


def downgrade() -> None:
    """Downgrade schema: Restore pdf_url from image_urls."""
    # Add back the pdf_url column
    op.add_column('chapters', sa.Column('pdf_url', sa.String(), nullable=True))
    
    # Note: We cannot reliably convert image_urls back to pdf_url
    # This is a destructive migration - data will be lost on downgrade
    
    # Drop the image_urls column
    op.drop_column('chapters', 'image_urls')

