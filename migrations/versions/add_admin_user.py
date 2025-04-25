"""add admin user

Revision ID: add_admin_user
Revises: 
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_admin_user'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create admin_users table
    op.create_table('admin_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('google_id', sa.String(length=100), nullable=True),
        sa.Column('is_whitelisted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id'),
        sa.UniqueConstraint('username')
    )

    # Insert default admin user
    op.execute("""
        INSERT INTO admin_user (username, password, email, full_name, is_whitelisted, created_at, is_active)
        VALUES ('admin', 'admin123', 'admin@example.com', 'Admin User', TRUE, NOW(), TRUE)
        ON DUPLICATE KEY UPDATE id=id
    """)

def downgrade():
    op.drop_table('admin_user') 