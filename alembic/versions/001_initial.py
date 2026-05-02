"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('imported_at', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documents_content_hash', 'documents', ['content_hash'], unique=True)
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])
    op.create_index('idx_documents_imported_at', 'documents', ['imported_at'])
    op.create_index('idx_documents_mime_type', 'documents', ['mime_type'])

    # Tags store a JSON list of document IDs directly (denormalised for simplicity)
    op.create_table('tags',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tag', sa.String(), nullable=False),
        sa.Column('document_ids', sa.Text(), nullable=False, server_default='[]'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tags_tag', 'tags', ['tag'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_tags_tag', table_name='tags')
    op.drop_table('tags')
    op.drop_index('idx_documents_mime_type', table_name='documents')
    op.drop_index('idx_documents_imported_at', table_name='documents')
    op.drop_index('idx_documents_created_at', table_name='documents')
    op.drop_index('idx_documents_content_hash', table_name='documents')
    op.drop_table('documents')
